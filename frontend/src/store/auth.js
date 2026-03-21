// простое хранилище без Redux — для MVP достаточно
// хранит токен в localStorage и предоставляет хелперы

export const auth = {
  getToken: () => localStorage.getItem('token'),
  
  setToken: (token) => localStorage.setItem('token', token),
  
  removeToken: () => localStorage.removeItem('token'),
  
  isAuthenticated: () => !!localStorage.getItem('token'),
};