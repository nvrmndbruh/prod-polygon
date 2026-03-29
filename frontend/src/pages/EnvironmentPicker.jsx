import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import client from '../api/client';
import { LogoIcon, LogoHorizontal } from '../components/Brand';
import { ArrowRightIcon, ChevronDownIcon, GraphIcon, InfoIcon, TwoArrowsIcon } from '../components/Icons';
import './EnvironmentPicker.css';

export default function EnvironmentPicker() {
  const navigate = useNavigate();
  const [environments, setEnvironments] = useState([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState('');

  const selectedEnvironment = environments[selectedIndex] || null;

  // загружаем список окружений при открытии страницы
  useEffect(() => {
    const fetchEnvironments = async () => {
      try {
        const response = await client.get('/environments');
        setEnvironments(response.data);

        // проверяем — вдруг у пользователя уже есть активная сессия
        // если есть — сразу отправляем на рабочую страницу
        const sessionResponse = await client.get('/sessions/current');
        if (sessionResponse.data) {
          navigate('/workspace');
        }
      } catch (err) {
        // 404 значит сессии нет
        if (err.response?.status !== 404) {
          setError('Не удалось загрузить окружения');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchEnvironments();
  }, [navigate]);

  const handlePrev = () => {
    setSelectedIndex((prev) =>
      prev === 0 ? environments.length - 1 : prev - 1
    );
  };

  const handleNext = () => {
    setSelectedIndex((prev) =>
      prev === environments.length - 1 ? 0 : prev + 1
    );
  };

  const handleStart = async () => {
    if (!selectedEnvironment) return;
    if (!selectedEnvironment.is_available) {
      setError('Это окружение пока недоступно для запуска');
      return;
    }

    setStarting(true);
    setError('');

    try {
      await client.post('/sessions', {
        environment_id: selectedEnvironment.id,
      });
      navigate('/workspace');
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Не удалось запустить окружение'
      );
      setStarting(false);
    }
  };

  // вычисляем индексы для трёх видимых карточек
  const getCardIndex = (offset) => {
    const len = environments.length;
    if (len === 0) return 0;
    return (selectedIndex + offset + len) % len;
  };

  if (loading) {
    return (
      <div className="picker-page">
        <div className="picker-loading">
          <span className="text-green mono">загрузка окружений...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="picker-page">
      {/* топбар */}
      <header className="picker-header">
        <div className="picker-header-logo">
          <LogoIcon size={24} />
          <LogoHorizontal width={160} />
        </div>
      </header>

      {/* основной контент */}
      <main className="picker-main">
        <p className="picker-subtitle">
          выберите вариант окружения для дальнейшей работы
        </p>

        {error && <p className="picker-error">{error}</p>}

        {environments.length === 0 ? (
          <p className="text-secondary mono">окружения не найдены</p>
        ) : (
          <>
            {/* карусель карточек */}
            <div className="picker-carousel">
              <button
                className="picker-arrow picker-arrow-left"
                onClick={handlePrev}
                disabled={environments.length <= 1}
              >
                <ChevronDownIcon size={24} style={{ transform: 'rotate(90deg)' }} />
              </button>

              <div className="picker-cards">
                {environments.length >= 1 && (
                  <EnvironmentCard
                    environment={environments[getCardIndex(-1)]}
                    active={false}
                    onClick={handlePrev}
                  />
                )}

                <EnvironmentCard
                  environment={selectedEnvironment}
                  active={true}
                  onClick={handleStart}
                />

                {environments.length >= 1 && (
                  <EnvironmentCard
                    environment={environments[getCardIndex(1)]}
                    active={false}
                    onClick={handleNext}
                  />
                )}
              </div>

              <button
                className="picker-arrow picker-arrow-right"
                onClick={handleNext}
                disabled={environments.length <= 1}
              >
                <ChevronDownIcon size={24} style={{ transform: 'rotate(-90deg)' }} />
              </button>
            </div>

            {/* кнопка запуска */}
            <button
              className="btn-primary picker-start"
              onClick={handleStart}
              disabled={starting || !selectedEnvironment?.is_available}
            >
              {starting ? (
                <>
                  <span className="picker-spinner" />
                  запуск окружения...
                </>
              ) : !selectedEnvironment?.is_available ? (
                <>
                  <InfoIcon size={14} className="picker-start-icon" />
                  окружение недоступно
                </>
              ) : (
                <>
                  <ArrowRightIcon size={14} className="picker-start-icon" />
                  запустить окружение
                </>
              )}
            </button>
          </>
        )}
      </main>
    </div>
  );
}

// карточка одного окружения
function EnvironmentCard({ environment, active, onClick }) {
  const available = Boolean(environment?.is_available);

  return (
    <div
      className={`env-card ${active ? 'env-card-active' : 'env-card-dim'} ${
        available ? '' : 'env-card-unavailable'
      }`}
      onClick={onClick}
    >
      {/* иконка окружения заглушка */}
      <div className="env-card-icon">
        <GraphIcon size={36} className="env-card-icon-svg" />
      </div>

      <h3 className="env-card-name">{environment.name}</h3>
      <p className="env-card-desc">{environment.description}</p>
      <p className={`env-card-status ${available ? 'ok' : 'pending'}`}>
        {available ? 'доступно' : 'в разработке'}
      </p>
    </div>
  );
}