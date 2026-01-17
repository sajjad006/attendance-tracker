import api from './axios';

export const attendanceApi = {
  getAll: async (params = {}) => {
    const response = await api.get('/attendance/', { params });
    // Handle paginated response
    return response.data.results || response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/attendance/${id}/`);
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/attendance/', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.patch(`/attendance/${id}/`, data);
    return response.data;
  },

  delete: async (id) => {
    const response = await api.delete(`/attendance/${id}/`);
    return response.data;
  },

  getToday: async (semesterId = null) => {
    const params = semesterId ? { semester_id: semesterId } : {};
    const response = await api.get('/attendance/today/', { params });
    return response.data;
  },

  getCalendar: async (year, month, semesterId = null) => {
    const params = { year, month };
    if (semesterId) params.semester_id = semesterId;
    const response = await api.get('/attendance/calendar/', { params });
    return response.data;
  },

  bulkUpdate: async (data) => {
    const response = await api.post('/attendance/bulk_update/', data);
    return response.data;
  },

  markDay: async (data) => {
    const response = await api.post('/attendance/mark_day/', data);
    return response.data;
  },

  addAdhoc: async (data) => {
    const response = await api.post('/attendance/add_adhoc/', data);
    return response.data;
  },

  generateClasses: async (data) => {
    const response = await api.post('/attendance/generate/', data);
    return response.data;
  },

  generateForDate: async (semesterId, date) => {
    const response = await api.post('/attendance/generate/', {
      semester_id: semesterId,
      start_date: date,
      end_date: date,
    });
    return response.data;
  },
};
