import axios from 'axios';

const API_BASE_URL = '/api';

const selfApi = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth interceptors
selfApi.interceptors.request.use(config => {
  const token = localStorage.getItem('accessToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  } else {
    // Dev fallback with x-student-id header
    const studentId = localStorage.getItem('studentId') || 'student123';
    config.headers['x-student-id'] = studentId;
  }
  return config;
}, error => {
  return Promise.reject(error);
});

// Response interceptor for error handling
selfApi.interceptors.response.use(
  response => response,
  error => {
    console.error('Self service API error:', error.response?.data);
    return Promise.reject(error);
  }
);

export interface UserProfile {
  student_id: string;
  name: string;
  major: string;
}

export interface TicketSummary {
  id: number;
  subject: string;
  category: string;
  priority: string;
  status: string;
  created_at: string;
}

export interface ChatMessage {
  user: string;
  bot: string;
  timestamp: number;
  agent: string;
  student_id?: string;
}

export interface CallToolRequest {
  intent: 'reset_password' | 'renew_library' | 'book_room';
  parameters: Record<string, any>;
}

export interface CallToolResponse {
  success: boolean;
  message: string;
  data?: any;
}

export const selfService = {
  // Get current user profile
  async getMe(): Promise<UserProfile> {
    try {
      const response = await selfApi.get('/me');
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 401) {
        throw new Error('Authentication required');
      }
      throw new Error('Failed to fetch user profile');
    }
  },

  // Get user's tickets with optional status filter
  async getMyTickets(status?: string): Promise<TicketSummary[]> {
    try {
      const params = status ? { status } : {};
      const response = await selfApi.get('/me/tickets', { params });
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 401) {
        throw new Error('Authentication required');
      }
      if (error.response?.status === 503) {
        throw new Error('Ticket service temporarily unavailable');
      }
      throw new Error('Failed to fetch tickets');
    }
  },

  // Get session chat history
  async getSessionHistory(sessionId: string, limit: number = 50): Promise<ChatMessage[]> {
    try {
      const response = await selfApi.get(`/sessions/${sessionId}/history`, {
        params: { limit }
      });
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 401) {
        throw new Error('Authentication required');
      }
      if (error.response?.status === 404) {
        return []; // Return empty array for non-existent sessions
      }
      throw new Error('Failed to fetch session history');
    }
  },

  // Call action tools (reset password, renew library, book room)
  async callTool(toolName: string, toolArgs: any): Promise<any> {
    try {
      const response = await selfApi.post('/call_tool', {
        tool_name: toolName,
        tool_args: toolArgs
      });
      
      return {
        status: 'success',
        message: response.data.message || 'Action completed successfully',
        data: response.data
      };
    } catch (error: any) {
      console.error('Tool call error:', error);
      throw error;
    }
  }
};

export const getMe = () => selfService.getMe();
export const getMyTickets = () => selfService.getMyTickets();
export const getSessionHistory = (sessionId: string, limit?: number) => 
  selfService.getSessionHistory(sessionId, limit);
export const callTool = (toolName: string, toolArgs: any) => 
  selfService.callTool(toolName, toolArgs);

export default selfService;
