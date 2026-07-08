# API Overview

Base URL: `/api/v1`

## Authentication

Most endpoints require a JWT Bearer token. Obtain a token via `POST /api/v1/auth/login`.

All authenticated requests must include the header:

```
Authorization: Bearer <token>
```

## Endpoints

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Service health check |

### Auth

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/register` | Create a new user account |
| POST | `/api/v1/auth/login` | Authenticate and return a JWT |
| POST | `/api/v1/auth/refresh` | Refresh an expiring access token |

### Documents

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/documents` | List all accessible documents |
| POST | `/api/v1/documents` | Upload a new document |
| GET | `/api/v1/documents/{id}` | Retrieve document metadata and status |
| DELETE | `/api/v1/documents/{id}` | Delete a document and its analysis data |

### Chat

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/chat` | Send a message and receive a response |
| GET | `/api/v1/chat/conversations` | List all conversations for the user |

### Analysis

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/analysis` | Start a new document analysis |
| GET | `/api/v1/analysis/{id}` | Retrieve analysis results |

## Response Format

All successful responses follow a consistent structure:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Error Format

Errors follow a uniform structure:

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Description of the error",
  "details": {}
}
```

Standard error codes:

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `UNAUTHORIZED` | 401 | Missing or invalid authentication |
| `FORBIDDEN` | 403 | Authenticated but not permitted |
| `NOT_FOUND` | 404 | Resource does not exist |
| `CONFLICT` | 409 | Resource state conflict |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Unexpected server error |
