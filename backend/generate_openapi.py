"""Generate OpenAPI specification for the Lifelink API"""
import json
from main import app

# Generate OpenAPI spec
openapi_spec = app.openapi()

# Enhance the spec with additional information
openapi_spec["info"]["description"] = """
# Lifelink API Documentation

Welcome to the Lifelink API! This API powers a sophisticated memory and journal application with AI capabilities.

## Features

- **Memory Management**: Create, read, update, and delete personal memories
- **AI-Powered Insights**: Get AI-generated responses and mood analysis
- **Semantic Search**: Find memories using natural language queries
- **User Authentication**: Secure JWT-based authentication
- **Media Support**: Upload and transcribe audio recordings
- **Analytics**: Get insights and patterns from your memories

## Authentication

Most endpoints require authentication. Use the `/auth/login` endpoint to obtain a JWT token, 
then include it in the `Authorization` header as `Bearer <token>`.

## Rate Limiting

API requests are rate limited to ensure fair usage:
- Authenticated users: 1000 requests per hour
- Unauthenticated users: 100 requests per hour

## Support

For API support, please contact: support@lifelink.app
"""

openapi_spec["servers"] = [
    {"url": "http://localhost:8000", "description": "Development server"},
    {"url": "https://api.lifelink.app", "description": "Production server"}
]

openapi_spec["tags"] = [
    {
        "name": "authentication",
        "description": "User authentication and authorization"
    },
    {
        "name": "memories",
        "description": "Memory management operations"
    },
    {
        "name": "search",
        "description": "Search and discovery features"
    },
    {
        "name": "insights",
        "description": "Analytics and insights"
    },
    {
        "name": "health",
        "description": "System health and status"
    }
]

# Add security schemes
openapi_spec["components"]["securitySchemes"] = {
    "bearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT"
    }
}

# Save to file
with open("openapi.json", "w") as f:
    json.dump(openapi_spec, f, indent=2)

print("OpenAPI specification generated successfully!")
print("View the documentation at: http://localhost:8000/docs")
