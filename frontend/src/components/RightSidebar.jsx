import { useState, useEffect, useCallback } from 'react';
import client from '../api/client';
import { GraphIcon } from './Icons';
import './RightSidebar.css';

export default function RightSidebar({ open, onToggle, sessionId }) {
  const [containers, setContainers] = useState([]);
  const [selectedContainer, setSelectedContainer] = useState(null);
  const [logs, setLogs] = useState('');
  const [loadingLogs, setLoadingLogs] = useState(false);

  // загружаем список контейнеров
  const fetchContainers = useCallback(async () => {
    if (!sessionId) return;
    try {
      const res = await client.get('/containers');
      setContainers(res.data.containers || []);

      // выбираем первый контейнер по умолчанию
      if (res.data.containers?.length > 0 && !selectedContainer) {
        setSelectedContainer(res.data.containers[0].name);
      }
    } catch {
      // игнорируем
    }
  }, [sessionId, selectedContainer]);

  useEffect(() => {
    fetchContainers();
    // обновляем список каждые 5 секунд
    const interval = setInterval(fetchContainers, 5000);
    return () => clearInterval(interval);
  }, [fetchContainers]);

  // загружаем логи выбранного контейнера
  useEffect(() => {
    if (!selectedContainer || !sessionId) return;

    const fetchLogs = async () => {
      setLoadingLogs(true);
      try {
        const res = await client.get(
          `/containers/${selectedContainer}/logs?lines=50`
        );
        setLogs(res.data.logs || '');
      } catch {
        setLogs('Не удалось загрузить логи');
      } finally {
        setLoadingLogs(false);
      }
    };

    fetchLogs();
    const interval = setInterval(fetchLogs, 3000);
    return () => clearInterval(interval);
  }, [selectedContainer, sessionId]);

  const statusColor = (status) => {
    if (!status) return '#e8a040';
    const s = status.toLowerCase();
    if (s.startsWith('up')) return '#4ade80';
    if (s.startsWith('exited') || s.startsWith('dead')) return '#e05252';
    return '#e8a040';
  };

  return (
    <>
      {/* кнопка открытия если закрыт */}
      {!open && (
        <button className="sidebar-toggle-btn right" onClick={onToggle}>
          ‹
        </button>
      )}

      <aside className={`right-sidebar ${open ? 'open' : 'closed'}`}>
        {/* Граф */}
        <div className="right-section">
          <div className="sidebar-header">
            <div className="sidebar-header-title">
              <GraphIcon size={14} className="text-orange" />
              <span>граф</span>
            </div>
            <button
              className="btn-ghost sidebar-close"
              onClick={onToggle}
            >
              ›
            </button>
          </div>

          <div className="graph-area">
            {containers.length === 0 ? (
              <p className="text-dim mono" style={{ fontSize: 12, padding: 12 }}>
                контейнеры не найдены
              </p>
            ) : (
              <div className="graph-nodes">
                {containers.map((c) => (
                  <div
                    key={c.name}
                    className={`graph-node ${
                      selectedContainer === c.name ? 'graph-node-selected' : ''
                    }`}
                    onClick={() => setSelectedContainer(c.name)}
                  >
                    <div className="graph-node-header">
                      <span className="graph-node-name mono">{c.name}</span>
                      <span
                        className="graph-node-status"
                        style={{ color: statusColor(c.status) }}
                      >
                        ●
                      </span>
                    </div>
                    <p className="graph-node-image">{c.image}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* мониторинг — логи */}
        <div className="right-section right-section-logs">
          <div className="sidebar-header">
            <div className="sidebar-header-title">
              <span className="text-orange mono">[|||]</span>
              <span>мониторинг</span>
            </div>
          </div>

          {selectedContainer && (
            <div className="monitoring-container-name">
              данные о:{' '}
              <span className="text-orange mono">{selectedContainer}</span>
            </div>
          )}

          <div className="logs-label">логи</div>

          <div className="logs-area">
            {loadingLogs && !logs ? (
              <span className="text-dim mono" style={{ fontSize: 11 }}>
                загрузка...
              </span>
            ) : (
              <pre className="logs-content">{logs}</pre>
            )}
          </div>
        </div>
      </aside>
    </>
  );
}