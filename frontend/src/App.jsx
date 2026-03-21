import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import EnvironmentPicker from './pages/EnvironmentPicker';
import Workspace from './pages/Workspace';
import { auth } from './store/auth';

// компонент-обёртка для защищённых маршрутов
// если пользователь не авторизован — редиректит на логин
function ProtectedRoute({ children }) {
  if (!auth.isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/environments"
          element={
            <ProtectedRoute>
              <EnvironmentPicker />
            </ProtectedRoute>
          }
        />
        <Route
          path="/workspace"
          element={
            <ProtectedRoute>
              <Workspace />
            </ProtectedRoute>
          }
        />
        {/* по умолчанию редиректим на выбор окружения */}
        <Route path="*" element={<Navigate to="/environments" replace />} />
      </Routes>
    </BrowserRouter>
  );
}