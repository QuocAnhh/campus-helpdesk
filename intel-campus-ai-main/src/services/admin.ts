// Admin service for action requests management
import axios from 'axios';

const API_BASE_URL = '/api';

const adminApi = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth interceptors
adminApi.interceptors.request.use(config => {
  const token = localStorage.getItem('accessToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, error => {
  return Promise.reject(error);
});

// Response interceptor for error handling
adminApi.interceptors.response.use(
  response => response,
  error => {
    console.error('Admin API error:', error.response?.data);
    return Promise.reject(error);
  }
);

export interface ActionRequest {
  id: number;
  student_id: string;
  action_type: string;
  status: 'submitted' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
  request_data: any;
  result_data?: any;
  external_id?: string;
  submitted_at: string;
  processed_at?: string;
  processed_by?: string;
  notes?: string;
  client_ip?: string;
}

export interface ActionRequestStats {
  total: number;
  submitted: number;
  in_progress: number;
  completed: number;
  failed: number;
  cancelled: number;
}

export interface ActionRequestFilters {
  status?: string;
  action_type?: string;
  student_id?: string;
  limit?: number;
  offset?: number;
}

export interface ActionRequestUpdate {
  status?: string;
  notes?: string;
  processed_by?: string;
}

const adminService = {
  // Get action requests with filtering
  async getActionRequests(filters: ActionRequestFilters = {}): Promise<ActionRequest[]> {
    try {
      const response = await adminApi.get('/admin/action-requests', {
        params: filters
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch action requests');
    }
  },

  // Get specific action request
  async getActionRequest(id: number): Promise<ActionRequest> {
    try {
      const response = await adminApi.get(`/admin/action-requests/${id}`);
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        throw new Error('Action request not found');
      }
      throw new Error(error.response?.data?.detail || 'Failed to fetch action request');
    }
  },

  // Update action request
  async updateActionRequest(id: number, update: ActionRequestUpdate): Promise<void> {
    try {
      await adminApi.patch(`/admin/action-requests/${id}`, update);
    } catch (error: any) {
      if (error.response?.status === 404) {
        throw new Error('Action request not found');
      }
      throw new Error(error.response?.data?.detail || 'Failed to update action request');
    }
  },

  // Get action request statistics
  async getActionRequestStats(): Promise<ActionRequestStats> {
    try {
      const response = await adminApi.get('/admin/action-requests-stats');
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch statistics');
    }
  }
};

export const getActionRequests = (filters?: ActionRequestFilters) => 
  adminService.getActionRequests(filters);
export const getActionRequest = (id: number) => 
  adminService.getActionRequest(id);
export const updateActionRequest = (id: number, update: ActionRequestUpdate) => 
  adminService.updateActionRequest(id, update);
export const getActionRequestStats = () => 
  adminService.getActionRequestStats();

export default adminService;
