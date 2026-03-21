import axios from 'axios';

// базовый URL бэкенда
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// интерцептор запросов — автоматически добавляет токен в каждый запрос
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// интерцептор ответов — если токен устарел (401),
// автоматически разлогиниваем пользователя
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default client;

// адрес для WebSocket — отдельно от HTTP
export const WS_URL = API_URL.replace('http', 'ws');