export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthResponse {
  token: string;
  user: {
    username: string;
    role: string;
    user_id: number;
  };
}

export interface User {
  username: string;
  role: string;
  user_id: number;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  loading: boolean;
  error: string | null;
} 