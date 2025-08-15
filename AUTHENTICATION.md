# Authentication System

The mini-mam API uses JWT (JSON Web Token) authentication to secure API endpoints. Users must authenticate to obtain a JWT token, which is then used to access protected endpoints.

## Default Users

The system comes with two users with configurable passwords:

| Username | Password | Role | Description |
|----------|----------|------|-------------|
| `admin` | Set via `ADMIN_PASSWORD` env var (default: `admin123`) | `admin` | Administrator with full access |
| `user` | Set via `USER_PASSWORD` env var (default: `user123`) | `user` | Regular user with standard access |

## Authentication Flow

### 1. Login to Get Token

**Endpoint**: `POST /auth/login`

**Request Body**:
```json
{
    "username": "admin",
    "password": "your-admin-password"
}
```

**Response**:
```json
{
    "message": "Login successful",
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "user_id": 1,
        "username": "admin",
        "role": "admin"
    }
}
```

### 2. Use Token for API Requests

Include the token in the `Authorization` header:

```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## API Endpoints

### Authentication Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/auth/login` | POST | Login to get JWT token | No |
| `/auth/verify` | POST | Verify JWT token | Yes |
| `/auth/me` | GET | Get current user info | Yes |

### Protected API Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/assets/*` | GET, POST, PUT, DELETE | Asset management | Yes |
| `/api/files/*` | GET, POST, PUT, DELETE | File management | Yes |
| `/api/transcode/*` | GET, POST, PUT, DELETE | Transcode management | Yes |
| `/api/search/*` | GET, POST | Search functionality | Yes |
| `/api/status` | GET | Service status | Yes |

## Example Usage

### Using curl

1. **Login**:
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-admin-password"}'
```

2. **Use the token**:
```bash
curl -X GET http://localhost:8000/api/assets \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Using JavaScript/Fetch

```javascript
// Login
const loginResponse = await fetch('http://localhost:8000/auth/login', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        username: 'admin',
        password: 'your-admin-password'
    })
});

const loginData = await loginResponse.json();
const token = loginData.token;

// Use token for API requests
const assetsResponse = await fetch('http://localhost:8000/api/assets', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});
```

## Error Responses

### Authentication Errors

**401 Unauthorized** - No token provided:
```json
{
    "error": "Authentication required",
    "message": "No token provided"
}
```

**401 Unauthorized** - Invalid/expired token:
```json
{
    "error": "Authentication failed",
    "message": "Invalid or expired token"
}
```

**403 Forbidden** - Insufficient permissions:
```json
{
    "error": "Insufficient permissions",
    "message": "Role admin required"
}
```

### Login Errors

**400 Bad Request** - Missing credentials:
```json
{
    "error": "Missing credentials",
    "message": "Username and password are required"
}
```

**401 Unauthorized** - Invalid credentials:
```json
{
    "error": "Authentication failed",
    "message": "Invalid username or password"
}
```

## Token Details

- **Algorithm**: HS256
- **Expiration**: 24 hours from creation
- **Payload**: Contains user_id, username, role, expiration, and issued-at timestamp

## Security Considerations

### Production Deployment

1. **Change Default Credentials**: Replace hardcoded users with database-backed authentication
2. **Secure JWT Secret**: Set `JWT_SECRET_KEY` environment variable with a strong secret
3. **HTTPS**: Always use HTTPS in production
4. **Token Expiration**: Consider shorter token expiration times for sensitive applications
5. **Rate Limiting**: Authentication endpoints are rate-limited to prevent brute force attacks

### Environment Variables

```bash
# JWT Secret Key (change in production)
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production

# User Passwords (change in production)
ADMIN_PASSWORD=your-admin-password
USER_PASSWORD=your-user-password
```

## User Information Forwarding

When a request is authenticated, the API Gateway forwards user information to microservices via headers:

- `X-User-ID`: User ID
- `X-Username`: Username
- `X-User-Role`: User role

This allows microservices to implement user-specific logic and access control.

## Rate Limiting

Authentication endpoints have rate limits to prevent abuse:

- `/auth/login`: 10 requests per minute
- `/auth/verify`: 100 requests per minute
- `/auth/me`: 100 requests per minute

## Testing

You can test the authentication system using the provided users. The passwords can be configured via environment variables:

- Set `ADMIN_PASSWORD` to change the admin password
- Set `USER_PASSWORD` to change the user password

If environment variables are not set, the system uses default passwords (`admin123` and `user123`). 