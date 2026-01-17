import api from './axios';

export const analyticsApi = {
  getDashboard: async (semesterId = null) => {
    const params = semesterId ? { semester_id: semesterId } : {};
    const response = await api.get('/analytics/dashboard/', { params });
    return response.data;
  },

  getSemesterAnalytics: async (semesterId) => {
    const response = await api.get(`/analytics/semester/${semesterId}/`);
    return response.data;
  },

  getSemesterAlerts: async (semesterId) => {
    const response = await api.get(`/analytics/semester/${semesterId}/alerts/`);
    return response.data;
  },

  getSubjectAnalytics: async (subjectId) => {
    const response = await api.get(`/analytics/subject/${subjectId}/`);
    return response.data;
  },

  getWeeklyTrends: async (subjectId, weeks = 8) => {
    const response = await api.get(`/analytics/subject/${subjectId}/weekly/`, {
      params: { weeks },
    });
    return response.data;
  },

  getMonthlyTrends: async (subjectId, months = 6) => {
    const response = await api.get(`/analytics/subject/${subjectId}/monthly/`, {
      params: { months },
    });
    return response.data;
  },

  getAttendanceHistory: async (subjectId, startDate = null, endDate = null) => {
    const params = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    const response = await api.get(`/analytics/subject/${subjectId}/history/`, { params });
    return response.data;
  },
};
