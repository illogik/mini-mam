import axios, { AxiosResponse } from 'axios';
import { LoginCredentials, AuthResponse, User } from '../types/auth';

// Configure axios base URL - use host-relative URLs by default
const API_BASE_URL = process.env.REACT_APP_API_URL || '';

const authApi = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor to handle errors
authApi.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error) => {
    console.error('Auth API Error:', error);
    return Promise.reject(error);
  }
);

export class AuthService {
  static async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await authApi.post('/auth/login', credentials);
    return response.data;
  }

  static async verifyToken(token: string): Promise<{ valid: boolean; user?: User }> {
    try {
      const response = await authApi.post('/auth/verify', {}, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      return { valid: true, user: response.data.user };
    } catch (error) {
      return { valid: false };
    }
  }

  static async getCurrentUser(token: string): Promise<User> {
    const response = await authApi.get('/auth/me', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    return response.data.user;
  }

  static async logout(): Promise<void> {
    // Clear local storage
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
  }

  // Token management
  static getStoredToken(): string | null {
    return localStorage.getItem('auth_token');
  }

  static setStoredToken(token: string): void {
    localStorage.setItem('auth_token', token);
  }

  static getStoredUser(): User | null {
    const userStr = localStorage.getItem('auth_user');
    return userStr ? JSON.parse(userStr) : null;
  }

  static setStoredUser(user: User): void {
    localStorage.setItem('auth_user', JSON.stringify(user));
  }

  static clearStoredAuth(): void {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
  }
}

export default authApi; 