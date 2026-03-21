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

  const handleStartScenario = async () => {
    if (!scenario) return;
    setStarting(true);
    try {
      await client.post(`/scenarios/${scenario.id}/start`);
      setValidationResult(null);
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

  const difficultyLabel = {
    easy: 'легко',
    medium: 'средне',
    hard: 'сложно',
  };

  return (
    <>
      {/* Кнопка открытия если закрыт */}
      {!open && (
        <button className="sidebar-toggle-btn left" onClick={onToggle}>
          ›
        </button>
      )}

      <aside className={`left-sidebar ${open ? 'open' : 'closed'}`}>
        {/* Заголовок */}
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
          {/* Выбор сценария */}
          {scenarios.length > 1 && (
            <div className="sidebar-section">
              <p className="sidebar-label">сценарий</p>
              <select
                className="scenario-select"
                value={scenario?.id || ''}
                onChange={(e) => onSelectScenario(e.target.value)}
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
              {/* Сложность */}
              <div className="sidebar-section">
                <span className={`badge badge-${scenario.difficulty}`}>
                  {difficultyLabel[scenario.difficulty] || scenario.difficulty}
                </span>
              </div>

              {/* Описание проблемы */}
              <div className="sidebar-section">
                <p className="sidebar-label">текущая проблема:</p>
                <p className="sidebar-text">{scenario.description}</p>
              </div>

              {/* Подсказки */}
              {scenario.hints?.length > 0 && (
                <div className="sidebar-section">
                  <div className="sidebar-label">
                    <span className="text-orange mono">[?]</span>
                    {' '}подсказки
                  </div>
                  <div className="hints-list">
                    {scenario.hints.map((hint) => (
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
                </div>
              )}

              {/* Результат проверки */}
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

        {/* Кнопки действий */}
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
              <HintIcon size={14} />
              {validating ? 'проверка...' : 'проверка'}
            </button>
          </div>
        )}
      </aside>
    </>
  );
}