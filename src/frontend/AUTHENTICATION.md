# Frontend Authentication

This document describes the authentication system implemented in the React frontend.

## Overview

The frontend uses JWT (JSON Web Token) authentication with the following features:

- **Login/Logout**: User authentication with username/password
- **Token Management**: Automatic token storage and retrieval
- **Protected Routes**: Authentication-required access to application features
- **User Context**: Global state management for user information
- **Auto-login**: Persistent sessions using localStorage

## Components

### 1. Authentication Context (`contexts/AuthContext.tsx`)

Manages global authentication state using React Context API:

```typescript
interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  loading: boolean;
  error: string | null;
}
```

**Features:**
- Automatic token verification on app start
- Persistent login state
- Error handling and loading states
- Login/logout functions

### 2. Login Page (`components/LoginPage.tsx`)

Modern, responsive login interface with:

- **Form Validation**: Client-side validation for required fields
- **Error Display**: Clear error messages for failed login attempts
- **Demo Accounts**: Quick login buttons for testing
- **Loading States**: Visual feedback during authentication
- **Responsive Design**: Works on desktop and mobile

### 3. Authentication Service (`services/auth.ts`)

Handles all authentication API calls:

```typescript
class AuthService {
  static async login(credentials: LoginCredentials): Promise<AuthResponse>
  static async verifyToken(token: string): Promise<{ valid: boolean; user?: User }>
  static async getCurrentUser(token: string): Promise<User>
  static async logout(): Promise<void>
}
```

## Authentication Flow

### 1. App Initialization
1. App loads and checks for stored token in localStorage
2. If token exists, verifies it with the backend
3. If valid, restores user session
4. If invalid, clears stored data and shows login page

### 2. Login Process
1. User enters credentials or clicks demo button
2. Frontend validates form inputs
3. API call to `/auth/login` endpoint
4. On success: token and user data stored in localStorage
5. User redirected to main application

### 3. Protected Routes
1. All API calls automatically include Authorization header
2. If token expires, user is logged out automatically
3. Unauthenticated users see login page

### 4. Logout Process
1. User clicks logout button
2. Stored token and user data cleared
3. User redirected to login page

## API Integration

### Automatic Token Injection

All API calls automatically include the authentication token:

```typescript
// Request interceptor in api.ts
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  }
);
```

### Protected Endpoints

All service endpoints now require authentication:
- Assets API
- Files API
- Search API
- Transcode API

## User Interface

### Header Component

Updated to show user information and logout button:

```typescript
<div className="user-section">
  <div className="user-info">
    <span className="username">{user.username}</span>
    <span className="user-role">({user.role})</span>
  </div>
  <button className="logout-button" onClick={handleLogout}>
    Logout
  </button>
</div>
```

### Login Page Features

- **Modern Design**: Gradient background with clean card layout
- **Form Validation**: Real-time validation with error messages
- **Demo Buttons**: Quick access to admin and user accounts
- **Responsive**: Mobile-friendly design
- **Loading States**: Visual feedback during authentication

## Default Credentials

For development and testing:

- **Admin User**: `admin` / `admin123`
- **Regular User**: `user` / `user123`

These can be configured via environment variables in the backend.

## Security Features

### Token Storage
- Tokens stored in localStorage for persistence
- Automatic token verification on app start
- Secure token transmission in Authorization headers

### Error Handling
- Graceful handling of expired tokens
- Clear error messages for failed authentication
- Automatic logout on authentication failures

### Session Management
- Persistent sessions across browser restarts
- Automatic token refresh verification
- Secure logout with complete session cleanup

## Development

### Running the Frontend

```bash
cd src/frontend
npm install
npm start
```

### Building for Production

```bash
npm run build
```

### Environment Variables

```bash
REACT_APP_API_URL=http://localhost:80  # API Gateway URL
```

## Testing

The authentication system can be tested using:

1. **Demo Buttons**: Quick login with predefined credentials
2. **Manual Login**: Enter credentials manually
3. **Token Verification**: Check browser localStorage for stored tokens
4. **API Calls**: Verify authenticated requests work correctly

## Troubleshooting

### Common Issues

1. **Login Fails**: Check backend authentication service is running
2. **Token Expired**: User will be automatically logged out
3. **API Errors**: Verify API Gateway is accessible
4. **CORS Issues**: Ensure proper CORS configuration in backend

### Debug Information

- Check browser console for authentication errors
- Verify localStorage contains `auth_token` and `auth_user`
- Confirm API calls include Authorization headers
- Check network tab for failed authentication requests 