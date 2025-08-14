
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

