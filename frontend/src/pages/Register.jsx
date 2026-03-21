import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import client from '../api/client';
import { LogoIcon, LogoHorizontal } from '../components/Brand';
import './Auth.css';

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    login: '',
    password: '',
    password_confirm: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (form.password !== form.password_confirm) {
      setError('Пароли не совпадают');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await client.post('/auth/register', form);
      // после регистрации отправляем на логин
      navigate('/login');
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка регистрации');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">
          <LogoIcon
            size={180}
            bgGradient={{
              id: "auth-gradient",
              x1: "0%", y1: "0%", x2: "100%", y2: "100%",
              stops: [
                { offset: "30%", color: "#E8854F" },
                { offset: "100%", color: "#4ade80" },
              ],
            }}
          />
          <LogoHorizontal width={180} />
          <p className="auth-tagline">
            обучающая платформа для диагностики реальных систем
          </p>
        </div>

        <div className="auth-form-panel">
          <h1 className="auth-title">Создайте аккаунт</h1>

          <form onSubmit={handleSubmit} className="auth-form">
            <div className="form-group">
              <label className="form-label">логин</label>
              <input
                type="text"
                name="login"
                value={form.login}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">пароль</label>
              <input
                type="password"
                name="password"
                value={form.password}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">подтверждение пароля</label>
              <input
                type="password"
                name="password_confirm"
                value={form.password_confirm}
                onChange={handleChange}
                required
              />
            </div>

            {error && <p className="form-error">{error}</p>}

            <button
              type="submit"
              className="btn-primary auth-submit"
              disabled={loading}
            >
              <span>[</span>
              <span>:&gt;</span>
              <span>]</span>
              {loading ? 'регистрация...' : 'зарегистрироваться'}
            </button>
          </form>

          <p className="auth-switch">
            Уже есть аккаунт?{' '}
            <Link to="/login">Войти</Link>
          </p>
        </div>
      </div>
    </div>
  );
}