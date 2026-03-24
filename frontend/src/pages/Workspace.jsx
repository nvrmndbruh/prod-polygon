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
  const [error, setError] = useState('');
  const [restarting, setRestarting] = useState(false);

  useEffect(() => {
    const init = async () => {
      try {
        const sessionRes = await client.get('/sessions/current');
        setSession(sessionRes.data);

        const envRes = await client.get(
          `/environments/${sessionRes.data.environment_id}`
        );
        setEnvironment(envRes.data);
        setScenarios(envRes.data.scenarios || []);

        if (envRes.data.scenarios?.length > 0) {
          const scenarioRes = await client.get(
            `/scenarios/${envRes.data.scenarios[0].id}`
          );
          setActiveScenario(scenarioRes.data);
        }
      } catch (err) {
        if (err.response?.status === 404) {
          navigate('/environments');
        } else {
          setError('Не удалось загрузить данные сессии');
        }
      } finally {
        setLoading(false);
      }
    };

    init();
  }, [navigate]);

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
    try {
      await client.post(`/sessions/${session.id}/restart`);
    } catch (err) {
      console.error('Не удалось перезапустить окружение', err);
    } finally {
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
        <span className="text-green mono">загрузка рабочего пространства...</span>
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