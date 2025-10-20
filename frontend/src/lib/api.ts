import axiosInstance from './axios';
import { LoginRequest, RegisterRequest, AuthResponse, User } from '@/types/auth';

export const authAPI = {
  // Register new user
  register: async (data: RegisterRequest): Promise<AuthResponse> => {
    const response = await axiosInstance.post('/auth/register/', data);
    return response.data;
  },

  // Login user
  login: async (data: LoginRequest): Promise<AuthResponse> => {
    const response = await axiosInstance.post('/auth/login/', data);
    return response.data;
  },

  // Logout user
  logout: async (refreshToken: string): Promise<void> => {
    await axiosInstance.post('/auth/logout/', {
      refresh_token: refreshToken,
    });
  },

  // Get current user profile
  getProfile: async (): Promise<User> => {
    const response = await axiosInstance.get('/auth/profile/');
    return response.data;
  },

  // Update user profile
  updateProfile: async (data: Partial<User>): Promise<User> => {
    const response = await axiosInstance.patch('/auth/profile/', data);
    return response.data;
  },

  // Refresh token
  refreshToken: async (refreshToken: string): Promise<{ access: string }> => {
    const response = await axiosInstance.post('/auth/token/refresh/', {
      refresh: refreshToken,
    });
    return response.data;
  },
};
