import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import client from '../api/client';
import { LogoIcon } from '../components/Brand';
import LeftSidebar from '../components/LeftSidebar';
import RightSidebar from '../components/RightSidebar';
import Terminal from '../components/Terminal';
import { auth } from '../store/auth';
import './Workspace.css';

export default function Workspace() {
  const navigate = useNavigate();

  const [session, setSession] = useState(null);
  const [environment, setEnvironment] = useState(null);
  const [scenarios, setScenarios] = useState([]);
  const [activeScenario, setActiveScenario] = useState(null);

  const [leftOpen, setLeftOpen] = useState(true);
  const [rightOpen, setRightOpen] = useState(true);

  const [terminals, setTerminals] = useState([{ id: 1, label: 'terminal 1' }]);
  const [activeTerminal, setActiveTerminal] = useState(1);

  const [loading, setLoading] = useState(true);
  const [loadingMessage, setLoadingMessage] = useState('загрузка рабочего пространства...');
  const [error, setError] = useState('');
  const [restarting, setRestarting] = useState(false);

  const waitForSessionReady = useCallback(async (sessionId, options = {}) => {
    const { onStatus, shouldStop } = options;
    let failedStreak = 0;

    while (true) {
      if (shouldStop?.()) return false;

      try {
        const statusRes = await client.get(`/sessions/${sessionId}/status`);
        const status = statusRes.data || {};

        onStatus?.(status);

        if (status.is_ready) {
          return true;
        }

        if (status.stage === 'failed') {
          failedStreak += 1;
          if (failedStreak >= 3) {
            throw new Error(status.message || 'Не удалось запустить окружение');
          }
        } else {
          failedStreak = 0;
        }
      } catch (err) {
        if (shouldStop?.()) return false;

        if (err.response?.status === 404) {
          throw err;
        }

        if (!err.response) {
          await new Promise((resolve) => setTimeout(resolve, 2000));
          continue;
        }

        throw err;
      }

      await new Promise((resolve) => setTimeout(resolve, 2000));
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    const init = async () => {
      try {
        setLoadingMessage('получение активной сессии...');

        const sessionRes = await client.get('/sessions/current');
        if (cancelled) return;
        setSession(sessionRes.data);

        setLoadingMessage('получение данных окружения...');

        const envRes = await client.get(
          `/environments/${sessionRes.data.environment_id}`
        );
        if (cancelled) return;
        setEnvironment(envRes.data);
        setScenarios(envRes.data.scenarios || []);

        setLoadingMessage('подготовка окружения...');
        const ready = await waitForSessionReady(sessionRes.data.id, {
          shouldStop: () => cancelled,
          onStatus: (status) => {
            if (cancelled) return;
            setLoadingMessage(status.message || 'подготовка окружения...');
          },
        });

        if (!ready || cancelled) return;

        if (envRes.data.scenarios?.length > 0) {
          const scenarioRes = await client.get(
            `/scenarios/${envRes.data.scenarios[0].id}`
          );
          if (cancelled) return;
          setActiveScenario(scenarioRes.data);
        }
      } catch (err) {
        if (cancelled) return;

        if (err.response?.status === 404) {
          navigate('/environments');
        } else {
          setError(err.message || 'Не удалось загрузить данные сессии');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    init();

    return () => {
      cancelled = true;
    };
  }, [navigate, waitForSessionReady]);

  const handleSelectScenario = useCallback(async (scenarioId) => {
    try {
      const res = await client.get(`/scenarios/${scenarioId}`);
      setActiveScenario(res.data);
    } catch {
      // игнорируем
    }
  }, []);

  const handleEndSession = async () => {
    if (!session) return;
    if (!window.confirm('Завершить сессию? Все изменения в окружении будут потеряны.')) {
      return;
    }
    try {
      await client.delete(`/sessions/${session.id}`);
      navigate('/environments');
    } catch {
      navigate('/environments');
    }
  };

  // перезапуск окружения
  const handleRestartEnvironment = async () => {
    if (!session) return;
    if (!window.confirm('Перезапустить окружение? Все текущие изменения будут сброшены.')) {
      return;
    }

    setRestarting(true);
    setError('');
    setLoading(true);
    setLoadingMessage('перезапуск окружения...');

    try {
      await client.post(`/sessions/${session.id}/restart`);

      const ready = await waitForSessionReady(session.id, {
        onStatus: (status) => {
          setLoadingMessage(status.message || 'перезапуск окружения...');
        },
      });

      if (!ready) {
        setError('Не удалось дождаться готовности окружения');
      }
    } catch (err) {
      console.error('Не удалось перезапустить окружение', err);
      setError('Не удалось перезапустить окружение');
    } finally {
      setLoading(false);
      setRestarting(false);
    }
  };

  const handleAddTerminal = () => {
    const newId = Math.max(...terminals.map((t) => t.id)) + 1;
    setTerminals((prev) => [
      ...prev,
      { id: newId, label: `terminal ${newId}` },
    ]);
    setActiveTerminal(newId);
  };

  const handleCloseTerminal = (id) => {
    if (terminals.length === 1) return;
    const remaining = terminals.filter((t) => t.id !== id);
    setTerminals(remaining);
    if (activeTerminal === id) {
      setActiveTerminal(remaining[remaining.length - 1].id);
    }
  };

  const handleLogout = () => {
    handleEndSession().finally(() => {
      auth.removeToken();
      navigate('/login');
    });
  };

  if (loading) {
    return (
      <div className="workspace-loading">
        <span className="text-green mono">{loadingMessage}</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="workspace-loading">
        <span className="text-orange mono">{error}</span>
      </div>
    );
  }

  return (
    <div className="workspace">
      {/* топбар */}
      <header className="workspace-topbar">
        <div className="topbar-left">
          <LogoIcon size={22} />

          {/* кнопка левого сайдбара */}
          <button
            className={`btn-ghost topbar-sidebar-btn ${leftOpen ? 'active' : ''}`}
            onClick={() => setLeftOpen((v) => !v)}
            title="Левая панель"
          >
            ☰
          </button>

          <span className="topbar-env-name mono">
            {environment?.name || '—'}
          </span>

          {/* кнопка перезапуска */}
          <button
            className="btn-ghost topbar-restart"
            onClick={handleRestartEnvironment}
            disabled={restarting}
            title="Перезапустить окружение"
          >
            {restarting ? '↻...' : '↻'}
          </button>

          <button
            className="btn-ghost topbar-exit"
            onClick={handleEndSession}
            title="Завершить сессию"
          >
            ⇥
          </button>
        </div>

        {/* вкладки терминала */}
        <div className="topbar-tabs">
          {terminals.map((term) => (
            <div
              key={term.id}
              className={`topbar-tab ${activeTerminal === term.id ? 'topbar-tab-active' : ''}`}
              onClick={() => setActiveTerminal(term.id)}
            >
              <span className="topbar-tab-icon">□</span>
              <span>{term.label}</span>
              {terminals.length > 1 && (
                <button
                  className="topbar-tab-close"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleCloseTerminal(term.id);
                  }}
                >
                  ×
                </button>
              )}
            </div>
          ))}
          <button
            className="topbar-tab-add"
            onClick={handleAddTerminal}
            title="Новый терминал"
          >
            +
          </button>
        </div>

        <div className="topbar-right">
          <SessionTimer startTime={session?.start_time} />
          <button
            className={`btn-ghost topbar-sidebar-btn ${rightOpen ? 'active' : ''}`}
            onClick={() => setRightOpen((v) => !v)}
            title="Правая панель"
          >
            □
          </button>
        </div>
      </header>

      {/* основная область */}
      <div className="workspace-body">
        <LeftSidebar
          open={leftOpen}
          onToggle={() => setLeftOpen((v) => !v)}
          scenario={activeScenario}
          scenarios={scenarios}
          sessionId={session?.id}
          onSelectScenario={handleSelectScenario}
        />

        <div className="workspace-terminals">
          {terminals.map((term) => (
            <div
              key={term.id}
              className="terminal-wrapper"
              style={{ display: activeTerminal === term.id ? 'flex' : 'none' }}
            >
              <Terminal
                sessionId={session?.id}
                token={auth.getToken()}
                active={activeTerminal === term.id}
              />
            </div>
          ))}
        </div>

        <RightSidebar
          open={rightOpen}
          onToggle={() => setRightOpen((v) => !v)}
          sessionId={session?.id}
        />
      </div>
    </div>
  );
}

function SessionTimer({ startTime }) {
  const [elapsed, setElapsed] = useState('00:00');

  useEffect(() => {
    if (!startTime) return;

    const update = () => {
      const start = new Date(startTime);
      const now = new Date();
      const diff = Math.floor((now - start) / 1000);
      const minutes = Math.floor(diff / 60).toString().padStart(2, '0');
      const seconds = (diff % 60).toString().padStart(2, '0');
      setElapsed(`${minutes}:${seconds}`);
    };

    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, [startTime]);

  return (
    <span className="topbar-timer mono">{elapsed}</span>
  );
}