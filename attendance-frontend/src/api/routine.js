import api from './axios';

export const routineApi = {
  getAll: async () => {
    const response = await api.get('/routines/');
    // Handle paginated response
    return response.data.results || response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/routines/${id}/`);
    return response.data;
  },

  getBySemester: async (semesterId) => {
    const response = await api.get('/routines/', { params: { semester: semesterId } });
    // Handle paginated response
    return response.data.results || response.data;
  },

  create: async (data) => {
    const response = await api.post('/routines/', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.put(`/routines/${id}/`, data);
    return response.data;
  },

  delete: async (id) => {
    const response = await api.delete(`/routines/${id}/`);
    return response.data;
  },
};

export const routineEntryApi = {
  getAll: async (routineId = null) => {
    const params = routineId ? { routine: routineId } : {};
    const response = await api.get('/routine-entries/', { params });
    // Handle paginated response
    return response.data.results || response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/routine-entries/${id}/`);
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/routine-entries/', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.put(`/routine-entries/${id}/`, data);
    return response.data;
  },

  delete: async (id) => {
    const response = await api.delete(`/routine-entries/${id}/`);
    return response.data;
  },
};
