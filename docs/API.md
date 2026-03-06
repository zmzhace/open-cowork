# API Documentation

## Base URL

```
http://localhost:8000
```

## Endpoints

### Health Check

Check if the API is running.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy"
}
```

**Example:**
```bash
curl http://localhost:8000/health
```

---

### Root

Get API information.

**Endpoint:** `GET /`

**Response:**
```json
{
  "message": "Open-Cowork API"
}
```

---

### Chat (Placeholder)

Send a message to the agent.

**Endpoint:** `POST /chat`

**Request Body:**
```json
{
  "message": "Your message here"
}
```

**Response:**
```json
{
  "response": "Not implemented yet"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

---

## Interactive Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## CORS

The API supports CORS with the following configuration:
- **Allowed Origins:** `*` (all origins)
- **Allowed Methods:** `*` (all methods)
- **Allowed Headers:** `*` (all headers)
- **Allow Credentials:** `true`

## Rate Limiting

Currently not implemented. Planned for future releases.

## Authentication

Currently not implemented. Planned for future releases.

## WebSocket Support

Planned for future releases to support real-time bidirectional communication.
