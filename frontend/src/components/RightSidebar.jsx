import { useState, useEffect, useCallback } from 'react';
import client from '../api/client';
import { GraphIcon } from './Icons';
import './RightSidebar.css';

const SERVICE_CONNECTIONS = [
  { from: 'nginx', to: 'backend' },
  { from: 'backend', to: 'db' },
  { from: 'backend', to: 'redis' },
];

const NODE_POSITIONS = {
  nginx:   { x: 90,  y: 30 },
  backend: { x: 90,  y: 110 },
  db:      { x: 20,  y: 190 },
  redis:   { x: 160, y: 190 },
};

const NODE_WIDTH = 80;
const NODE_HEIGHT = 36;

export default function RightSidebar({ open, onToggle, sessionId }) {
  const [containers, setContainers] = useState([]);
  const [connections, setConnections] = useState([]);
  const [selectedContainer, setSelectedContainer] = useState(null);
  const [logs, setLogs] = useState('');
  const [loadingLogs, setLoadingLogs] = useState(false);

  const fetchContainers = useCallback(async () => {
    if (!sessionId) return;
    try {
      const res = await client.get('/containers');
      setContainers(res.data.containers || []);
      if (res.data.containers?.length > 0 && !selectedContainer) {
        setSelectedContainer(res.data.containers[0].name);
      }
    } catch {
      // игнорируем
    }
  }, [sessionId, selectedContainer]);

  const fetchConnections = useCallback(async () => {
    if (!sessionId) return;
    try {
      const res = await client.get('/containers/connections/status');
      setConnections(res.data.connections || []);
    } catch {
      // игнорируем
    }
  }, [sessionId]);

  useEffect(() => {
    fetchContainers();
    const interval = setInterval(fetchContainers, 5000);
    return () => clearInterval(interval);
  }, [fetchContainers]);

  useEffect(() => {
    fetchConnections();
    const interval = setInterval(fetchConnections, 5000);
    return () => clearInterval(interval);
  }, [fetchConnections]);

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

  const getContainer = (name) =>
    containers.find((c) => c.name === name);

  const nodeCenter = (name) => {
    const pos = NODE_POSITIONS[name];
    if (!pos) return null;
    return {
      x: pos.x + NODE_WIDTH / 2,
      y: pos.y + NODE_HEIGHT / 2,
    };
  };

  const edgePoint = (from, to, isSource) => {
    const f = nodeCenter(from);
    const t = nodeCenter(to);
    if (!f || !t) return null;

    const dx = t.x - f.x;
    const dy = t.y - f.y;
    const angle = Math.atan2(dy, dx);
    const hw = NODE_WIDTH / 2;
    const hh = NODE_HEIGHT / 2;
    const absDx = Math.abs(Math.cos(angle));
    const absDy = Math.abs(Math.sin(angle));

    let rx, ry;
    if (absDx * hh > absDy * hw) {
      rx = hw * Math.sign(dx);
      ry = hw * Math.tan(angle) * Math.sign(dx);
    } else {
      ry = hh * Math.sign(dy);
      rx = hh / Math.tan(angle) * Math.sign(dy);
    }

    const center = isSource ? f : t;
    const sign = isSource ? 1 : -1;
    return {
      x: center.x + sign * rx,
      y: center.y + sign * ry,
    };
  };

  const graphWidth = 260;
  const graphHeight = 260;

  return (
    <>
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
            <button className="btn-ghost sidebar-close" onClick={onToggle}>
              ›
            </button>
          </div>

          <div className="graph-area">
            {containers.length === 0 ? (
              <p className="text-dim mono" style={{ fontSize: 12, padding: 12 }}>
                контейнеры не найдены
              </p>
            ) : (
              <svg
                width="100%"
                viewBox={`0 0 ${graphWidth} ${graphHeight}`}
                className="graph-svg"
              >
                <defs>
                  <marker
                    id="arrowhead"
                    markerWidth="8"
                    markerHeight="6"
                    refX="8"
                    refY="3"
                    orient="auto"
                  >
                    <polygon
                      points="0 0, 8 3, 0 6"
                      fill="var(--border-color)"
                    />
                  </marker>
                  <marker
                    id="arrowhead-error"
                    markerWidth="8"
                    markerHeight="6"
                    refX="8"
                    refY="3"
                    orient="auto"
                  >
                    <polygon
                      points="0 0, 8 3, 0 6"
                      fill="#e05252"
                    />
                  </marker>
                </defs>

                {/* связи */}
                {SERVICE_CONNECTIONS.map(({ from, to }) => {
                  const posFrom = NODE_POSITIONS[from];
                  const posTo = NODE_POSITIONS[to];
                  if (!posFrom || !posTo) return null;

                  const src = edgePoint(from, to, true);
                  const dst = edgePoint(from, to, false);
                  if (!src || !dst) return null;

                  // проверяем статус связи из API
                  const connStatus = connections.find(
                    (c) => c.from === from && c.to === to
                  );
                  // если целевой контейнер упал — тоже ошибка
                  const containerTo = getContainer(to);
                  const targetDown = containerTo &&
                    !containerTo.status?.toLowerCase().startsWith('up');

                  const isError =
                    (connStatus && !connStatus.ok) || targetDown;

                  return (
                    <line
                      key={`${from}-${to}`}
                      x1={src.x}
                      y1={src.y}
                      x2={dst.x}
                      y2={dst.y}
                      stroke={isError ? '#e05252' : 'var(--border-color)'}
                      strokeWidth="1.5"
                      strokeDasharray={isError ? '4 3' : 'none'}
                      markerEnd={
                        isError
                          ? 'url(#arrowhead-error)'
                          : 'url(#arrowhead)'
                      }
                    />
                  );
                })}

                {/* узлы */}
                {containers.map((c) => {
                  const pos = NODE_POSITIONS[c.name];
                  if (!pos) return null;

                  const color = statusColor(c.status);
                  const isSelected = selectedContainer === c.name;

                  return (
                    <g
                      key={c.name}
                      onClick={() => setSelectedContainer(c.name)}
                      style={{ cursor: 'pointer' }}
                    >
                      <rect
                        x={pos.x}
                        y={pos.y}
                        width={NODE_WIDTH}
                        height={NODE_HEIGHT}
                        rx="5"
                        fill="var(--bg-card)"
                        stroke={
                          isSelected
                            ? 'var(--color-orange)'
                            : 'var(--border-color)'
                        }
                        strokeWidth={isSelected ? 1.5 : 1}
                      />
                      <circle
                        cx={pos.x + NODE_WIDTH - 10}
                        cy={pos.y + 10}
                        r="4"
                        fill={color}
                      />
                      <text
                        x={pos.x + NODE_WIDTH / 2}
                        y={pos.y + NODE_HEIGHT / 2 + 4}
                        textAnchor="middle"
                        fill="var(--text-primary)"
                        fontSize="12"
                        fontFamily="var(--font-mono)"
                      >
                        {c.name}
                      </text>
                    </g>
                  );
                })}
              </svg>
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