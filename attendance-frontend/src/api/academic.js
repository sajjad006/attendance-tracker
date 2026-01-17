import api from './axios';

export const semesterApi = {
  getAll: async () => {
    const response = await api.get('/semesters/');
    // Handle paginated response
    return response.data.results || response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/semesters/${id}/`);
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/semesters/', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.put(`/semesters/${id}/`, data);
    return response.data;
  },

  delete: async (id) => {
    const response = await api.delete(`/semesters/${id}/`);
    return response.data;
  },

  setAsCurrent: async (id) => {
    const response = await api.post(`/semesters/${id}/set_current/`);
    return response.data;
  },
};

export const subjectApi = {
  getAll: async (semesterId = null) => {
    const params = semesterId ? { semester: semesterId } : {};
    const response = await api.get('/subjects/', { params });
    // Handle paginated response
    return response.data.results || response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/subjects/${id}/`);
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/subjects/', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.put(`/subjects/${id}/`, data);
    return response.data;
  },

  delete: async (id) => {
    const response = await api.delete(`/subjects/${id}/`);
    return response.data;
  },
};
