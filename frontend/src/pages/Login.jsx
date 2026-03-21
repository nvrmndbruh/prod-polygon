import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import client from '../api/client';
import { auth } from '../store/auth';
import { LogoIcon, LogoHorizontal } from '../components/Brand';
import './Auth.css';

export default function Login() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ login: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await client.post('/auth/login', form);
      auth.setToken(response.data.access_token);
      navigate('/environments');
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка входа');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        {/* брендинг */}
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

        {/* форма */}
        <div className="auth-form-panel">
          <h1 className="auth-title">Войдите, чтобы продолжить</h1>

          <form onSubmit={handleSubmit} className="auth-form">
            <div className="form-group">
              <label className="form-label">логин</label>
              <input
                type="text"
                name="login"
                value={form.login}
                onChange={handleChange}
                autoComplete="username"
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
                autoComplete="current-password"
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
              {loading ? 'вход...' : 'войти'}
            </button>
          </form>

          <p className="auth-switch">
            Нет аккаунта?{' '}
            <Link to="/register">Зарегистрироваться</Link>
          </p>
        </div>
      </div>
    </div>
  );
}