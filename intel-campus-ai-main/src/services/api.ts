import axios from 'axios';
import { ChatRequest, ChatResponse, HealthStatus, Agent } from '@/types/chat';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // Increase timeout to 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Auth token interceptor
api.interceptors.request.use(config => {
  const token = localStorage.getItem('accessToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, error => {
  return Promise.reject(error);
});

export const authAPI = {
  login: async (username: string, password: string) => {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);

    const response = await api.post('/auth/token', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },

  register: async (userData: {
    username: string;
    email: string;
    full_name: string;
    password: string;
    role?: 'student' | 'admin';
  }) => {
    const response = await api.post('/auth/register', {
      ...userData,
      role: userData.role || 'student', // Default to student
    });
    return response.data;
  },
};

export const chatAPI = {
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await api.post<ChatResponse>('/ask', request);
    return response.data;
  },

  getHealth: async (): Promise<HealthStatus> => {
    const response = await api.get<HealthStatus>('/health');
    return response.data;
  },

  getAgents: async (): Promise<Agent[]> => {
    const response = await api.get<{available_agents: string[], description: string}>('/agents');
    // Convert string array to Agent array
    return response.data.available_agents.map(name => ({
      name: name,
      type: name, // Use name as type for now
      status: 'active' // Assume all agents are active
    }));
  },

  getChatLogs: async () => {
    const response = await api.get('/chat-logs');
    return response.data;
  },

  getChatLogDetail: async (sessionId: string) => {
    const response = await api.get(`/chat-logs/${sessionId}`);
    return response.data;
  },

  markSessionComplete: async (sessionId: string) => {
    const response = await api.post(`/chat-logs/${sessionId}/complete`);
    return response.data;
  },

  reopenSession: async (sessionId: string) => {
    const response = await api.post(`/chat-logs/${sessionId}/reopen`);
    return response.data;
  },
};