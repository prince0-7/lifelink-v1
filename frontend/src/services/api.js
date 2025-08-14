
import axios from 'axios';

const API_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
});

export const getMemories = async () => {
  const response = await api.get('/memories/');
  return response.data;
};

export const createMemory = async (memoryData) => {
  const response = await api.post('/memories/', memoryData);
  return response.data;
};

export const updateMemory = async (id, memoryData) => {
  const response = await api.put(`/memories/${id}`, memoryData);
  return response.data;
};

export const deleteMemory = async (id) => {
  await api.delete(`/memories/${id}`);
};

// Graph API endpoints
export const getMemoryGraph = async (timeRange = 'month', minStrength = 0.3) => {
  const response = await api.get('/api/graph/memories/graph', {
    params: { time_range: timeRange, min_strength: minStrength }
  });
  return response.data;
};

export const analyzeRelationships = async (forceRefresh = false) => {
  const response = await api.post('/api/graph/memories/analyze-relationships', null, {
    params: { force_refresh: forceRefresh }
  });
  return response.data;
};

export const detectClusters = async () => {
  const response = await api.post('/api/graph/memories/detect-clusters');
  return response.data;
};

export const createManualRelationship = async (sourceId, targetId, type = 'manual', strength = 0.8) => {
  const response = await api.post(`/api/graph/memories/${sourceId}/relate/${targetId}`, null, {
    params: { relationship_type: type, strength }
  });
  return response.data;
};

export const findMemoryPath = async (sourceId, targetId) => {
  const response = await api.get(`/api/graph/memories/${sourceId}/path/${targetId}`);
  return response.data;
};

// Analytics API endpoints
export const getAnalytics = {
  getMoodTrends: async (period = 'month') => {
    const response = await api.get('/api/analytics/mood-trends', {
      params: { period }
    });
    return response.data;
  },

  getConsistency: async (days = 30) => {
    const response = await api.get('/api/analytics/consistency', {
      params: { days }
    });
    return response.data;
  },

  getPeakTimes: async () => {
    const response = await api.get('/api/analytics/peak-times');
    return response.data;
  },

  getKeywords: async (limit = 20) => {
    const response = await api.get('/api/analytics/keywords', {
      params: { limit }
    });
    return response.data;
  },

  getMemoryLength: async () => {
    const response = await api.get('/api/analytics/memory-length');
    return response.data;
  },

  getEmotionalJourney: async (days = 30) => {
    const response = await api.get('/api/analytics/emotional-journey', {
      params: { days }
    });
    return response.data;
  },

  getInsightsSummary: async () => {
    const response = await api.get('/api/analytics/insights-summary');
    return response.data;
  },

  getActivityHeatmap: async (year) => {
    const response = await api.get('/api/analytics/activity-heatmap', {
      params: { year }
    });
    return response.data;
  },

  trackEvent: async (eventType, eventData = {}) => {
    const response = await api.post('/api/analytics/track-event', {
      event_type: eventType,
      event_data: eventData
    });
    return response.data;
  }
};

