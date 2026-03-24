import { useState } from 'react';
import client from '../api/client';
import { CheckIcon, HintIcon } from './Icons';
import './LeftSidebar.css';

export default function LeftSidebar({
  open,
  onToggle,
  scenario,
  scenarios,
  sessionId,
  onSelectScenario,
}) {
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  const [starting, setStarting] = useState(false);
  const [revealedCount, setRevealedCount] = useState(0);

  // сбрасываем подсказки при смене сценария
  const handleSelectScenario = (id) => {
    setRevealedCount(0);
    setValidationResult(null);
    onSelectScenario(id);
  };

  const handleStartScenario = async () => {
    if (!scenario) return;
    setStarting(true);
    setRevealedCount(0);
    setValidationResult(null);
    try {
      await client.post(`/scenarios/${scenario.id}/start`);
    } catch (err) {
      console.error(err);
    } finally {
      setStarting(false);
    }
  };

  const handleValidate = async () => {
    if (!scenario) return;
    setValidating(true);
    try {
      const res = await client.post(`/scenarios/${scenario.id}/validate`);
      setValidationResult(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setValidating(false);
    }
  };

  const handleRevealHint = () => {
    if (!scenario?.hints) return;
    const sorted = [...scenario.hints].sort(
      (a, b) => a.order_number - b.order_number
    );
    if (revealedCount < sorted.length) {
      setRevealedCount((prev) => prev + 1);
    }
  };

  const difficultyLabel = {
    easy: 'легко',
    medium: 'средне',
    hard: 'сложно',
  };

  const sortedHints = scenario?.hints
    ? [...scenario.hints].sort((a, b) => a.order_number - b.order_number)
    : [];

  const visibleHints = sortedHints.slice(0, revealedCount);
  const hasMoreHints = revealedCount < sortedHints.length;

  return (
    <>

      <aside className={`left-sidebar ${open ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <div className="sidebar-header-title">
            <span className="text-green mono">[i]</span>
            <span>информация</span>
          </div>
          <button className="btn-ghost sidebar-close" onClick={onToggle}>
            ‹
          </button>
        </div>

        <div className="sidebar-content">
          {scenarios.length > 1 && (
            <div className="sidebar-section">
              <p className="sidebar-label">сценарий</p>
              <select
                className="scenario-select"
                value={scenario?.id || ''}
                onChange={(e) => handleSelectScenario(e.target.value)}
              >
                {scenarios.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {scenario ? (
            <>
              <div className="sidebar-section">
                <span className={`badge badge-${scenario.difficulty}`}>
                  {difficultyLabel[scenario.difficulty] || scenario.difficulty}
                </span>
              </div>

              <div className="sidebar-section">
                <p className="sidebar-label">текущая проблема:</p>
                <p className="sidebar-text">{scenario.description}</p>
              </div>

              {/* подсказки */}
              {sortedHints.length > 0 && (
                <div className="sidebar-section">
                  <div className="sidebar-label">
                    <span className="text-orange mono">[?]</span>
                    {' '}подсказки{' '}
                    <span className="text-dim mono">
                      ({revealedCount}/{sortedHints.length})
                    </span>
                  </div>

                  {visibleHints.length > 0 && (
                    <div className="hints-list">
                      {visibleHints.map((hint) => (
                        <div key={hint.id} className="hint-item">
                          <span className="hint-number mono text-orange">
                            ({hint.order_number})
                          </span>
                          <span className="hint-text">{hint.text}</span>
                          {hint.documentation_link && (
                            <a
                              href={hint.documentation_link}
                              target="_blank"
                              rel="noreferrer"
                              className="hint-link"
                            >
                              документация →
                            </a>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {hasMoreHints && (
                    <button
                      className="btn-ghost hint-reveal-btn"
                      onClick={handleRevealHint}
                    >
                      <HintIcon size={13} />
                      показать подсказку
                    </button>
                  )}
                </div>
              )}

              {validationResult && (
                <div className={`validation-result ${
                  validationResult.success ? 'success' : 'failure'
                }`}>
                  <p className="validation-status mono">
                    {validationResult.success
                      ? '✓ решение верное'
                      : '✗ решение неверное'}
                  </p>
                  {validationResult.message && (
                    <p className="validation-message">
                      {validationResult.message}
                    </p>
                  )}
                </div>
              )}
            </>
          ) : (
            <p className="text-secondary">сценарии не найдены</p>
          )}
        </div>

        {scenario && (
          <div className="sidebar-actions">
            <button
              className="btn-primary sidebar-action-btn"
              onClick={handleStartScenario}
              disabled={starting}
            >
              <CheckIcon size={14} />
              {starting ? 'запуск...' : 'запустить'}
            </button>

            <button
              className="btn-secondary sidebar-action-btn"
              onClick={handleValidate}
              disabled={validating}
            >
              <CheckIcon size={14} />
              {validating ? 'проверка...' : 'проверка'}
            </button>
          </div>
        )}
      </aside>
    </>
  );
}