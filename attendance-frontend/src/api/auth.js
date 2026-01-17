import api from './axios';

export const authApi = {
  login: async (credentials) => {
    const response = await api.post('/auth/login/', credentials);
    return response.data;
  },

  register: async (userData) => {
    const response = await api.post('/auth/register/', userData);
    return response.data;
  },

  logout: async () => {
    const response = await api.post('/auth/logout/');
    return response.data;
  },

  getProfile: async () => {
    const response = await api.get('/auth/profile/');
    return response.data;
  },

  updateProfile: async (data) => {
    const response = await api.put('/auth/profile/', data);
    return response.data;
  },

  changePassword: async (data) => {
    const response = await api.post('/auth/change-password/', data);
    return response.data;
  },
};
