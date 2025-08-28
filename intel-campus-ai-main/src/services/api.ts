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
  console.log('API request interceptor - token exists:', !!token, 'URL:', config.url);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
    console.log('API request - Authorization header set, token length:', token.length);
  } else {
    console.warn('API request - No token found in localStorage');
  }
  return config;
}, error => {
  console.error('API request interceptor error:', error);
  return Promise.reject(error);
});

// Response interceptor for debugging
api.interceptors.response.use(
  response => {
    console.log('API response success:', response.status, response.config.url);
    return response;
  },
  error => {
    console.error('API response error:', error.response?.status, error.config?.url, error.response?.data);
    if (error.response?.status === 401) {
      console.warn('401 Unauthorized - checking token...');
      const token = localStorage.getItem('accessToken');
      console.log('Current token exists:', !!token);
      if (token) {
        console.log('Token length:', token.length, 'Token preview:', token.substring(0, 20) + '...');
      }
    }
    return Promise.reject(error);
  }
);

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

export const ticketAPI = {
  // Get all tickets with filtering and pagination
  getTickets: async (params?: {
    page?: number;
    per_page?: number;
    status?: string;
    category?: string;
    priority?: string;
    assigned_to?: string;
    user_id?: number;
  }) => {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.per_page) queryParams.append('per_page', params.per_page.toString());
    if (params?.status) queryParams.append('status', params.status);
    if (params?.category) queryParams.append('category', params.category);
    if (params?.priority) queryParams.append('priority', params.priority);
    if (params?.assigned_to) queryParams.append('assigned_to', params.assigned_to);
    if (params?.user_id) queryParams.append('user_id', params.user_id.toString());

    const response = await api.get(`/tickets?${queryParams.toString()}`);
    return response.data;
  },

  // Get single ticket
  getTicket: async (ticketId: number) => {
    const response = await api.get(`/tickets/${ticketId}`);
    return response.data;
  },

  // Create new ticket
  createTicket: async (ticketData: {
    subject: string;
    content: string;
    category?: string;
    priority?: string;
  }) => {
    console.log('Creating ticket with data:', ticketData);
    // Ensure category and priority have valid enum values
    const validCategories = ['technical', 'account', 'general', 'academic', 'facility'];
    const validPriorities = ['low', 'normal', 'high', 'urgent'];
    
    const processedData = {
      subject: ticketData.subject,
      content: ticketData.content,
      category: ticketData.category && validCategories.includes(ticketData.category) ? ticketData.category : 'general',
      priority: ticketData.priority && validPriorities.includes(ticketData.priority) ? ticketData.priority : 'normal'
    };
    
    console.log('Processed ticket data:', processedData);
    const response = await api.post('/tickets', processedData);
    return response.data;
  },

  // Update ticket
  updateTicket: async (ticketId: number, ticketData: {
    subject?: string;
    content?: string;
    category?: string;
    priority?: string;
    status?: string;
    assigned_to?: string;
    resolution?: string;
  }) => {
    const response = await api.put(`/tickets/${ticketId}`, ticketData);
    return response.data;
  },

  // Update ticket status
  updateTicketStatus: async (ticketId: number, statusData: {
    status: string;
    resolution?: string;
  }) => {
    const response = await api.patch(`/tickets/${ticketId}/status`, statusData);
    return response.data;
  },

  // Assign ticket
  assignTicket: async (ticketId: number, assignedTo: string) => {
    const response = await api.patch(`/tickets/${ticketId}/assign`, assignedTo, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  },

  // Delete ticket
  deleteTicket: async (ticketId: number) => {
    const response = await api.delete(`/tickets/${ticketId}`);
    return response.data;
  },

  // Get my tickets
  getMyTickets: async (skip?: number, limit?: number) => {
    const queryParams = new URLSearchParams();
    if (skip) queryParams.append('skip', skip.toString());
    if (limit) queryParams.append('limit', limit.toString());

    const response = await api.get(`/my-tickets?${queryParams.toString()}`);
    return response.data;
  },

  // Admin: Get ticket statistics
  getTicketStats: async () => {
    const response = await api.get('/admin/tickets/stats');
    return response.data;
  },

  // Admin: Get unassigned tickets
  getUnassignedTickets: async (skip?: number, limit?: number) => {
    const queryParams = new URLSearchParams();
    if (skip) queryParams.append('skip', skip.toString());
    if (limit) queryParams.append('limit', limit.toString());

    const response = await api.get(`/admin/tickets/unassigned?${queryParams.toString()}`);
    return response.data;
  },

  // Request technical analysis
  requestTechnicalAnalysis: async (ticketId: number) => {
    const response = await api.post(`/tickets/${ticketId}/technical-analysis`);
    return response.data;
  },

  // Request solution
  requestSolution: async (ticketId: number) => {
    const response = await api.post(`/tickets/${ticketId}/solution`);
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