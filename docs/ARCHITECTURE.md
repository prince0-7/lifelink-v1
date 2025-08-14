# Lifelink Architecture Documentation

## Overview

Lifelink is a sophisticated memory and journal application with AI capabilities, built using a modern microservices architecture.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                       │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Components  │  │   Services   │  │   State Mgmt    │   │
│  │  - Memory   │  │  - API       │  │  - Context API  │   │
│  │  - Auth     │  │  - Auth      │  │  - Local State  │   │
│  │  - Search   │  │  - WebSocket │  │                 │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS/WSS
                              │
┌─────────────────────────────────────────────────────────────┐
│                         API Gateway                          │
│                    (Nginx Reverse Proxy)                     │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                           │
┌───────────────────────┐               ┌──────────────────────┐
│   Backend (FastAPI)   │               │   AI Service Layer   │
│  ┌─────────────────┐  │               │  ┌───────────────┐   │
│  │   REST API      │  │               │  │ Local Models  │   │
│  │   - Auth        │  │               │  │ - Whisper     │   │
│  │   - CRUD        │  │               │  │ - Embeddings  │   │
│  │   - Search      │  │               │  │ - LLM         │   │
│  └─────────────────┘  │               │  └───────────────┘   │
│  ┌─────────────────┐  │               │  ┌───────────────┐   │
│  │ Business Logic  │  │               │  │ Cloud APIs    │   │
│  │   - Memory Mgmt │  │               │  │ - OpenAI      │   │
│  │   - Analytics   │  │               │  │ - Google AI   │   │
│  │   - Auth        │  │               │  │ - Anthropic   │   │
│  └─────────────────┘  │               │  └───────────────┘   │
└───────────────────────┘               └──────────────────────┘
            │                                       │
            └───────────────┬───────────────────────┘
                            │
        ┌───────────────────┴────────────────────┐
        │                                        │
┌──────────────────┐                 ┌──────────────────────┐
│    MongoDB       │                 │   Vector Database    │
│  ┌────────────┐  │                 │    (ChromaDB)        │
│  │ Collections│  │                 │  ┌───────────────┐   │
│  │ - Users    │  │                 │  │  Embeddings   │   │
│  │ - Memories │  │                 │  │  - Semantic   │   │
│  │ - Insights │  │                 │  │  - Search     │   │
│  └────────────┘  │                 │  └───────────────┘   │
└──────────────────┘                 └──────────────────────┘
```

## Technology Stack

### Frontend
- **Framework**: React 19 with Vite
- **UI Library**: Material-UI (MUI)
- **State Management**: React Context API + Local State
- **Styling**: Tailwind CSS + Emotion
- **Charts**: Chart.js with react-chartjs-2
- **HTTP Client**: Axios
- **Testing**: Vitest + React Testing Library

### Backend
- **Framework**: FastAPI (Python 3.10+)
- **Database**: MongoDB with Beanie ODM
- **Vector DB**: ChromaDB for semantic search
- **Authentication**: JWT with python-jose
- **AI/ML**: 
  - OpenAI Whisper for audio transcription
  - Sentence Transformers for embeddings
  - LangChain for AI orchestration
- **Background Jobs**: Celery with Redis
- **Testing**: Pytest + pytest-asyncio

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Reverse Proxy**: Nginx
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)

## Key Design Patterns

### 1. Repository Pattern
Used in the backend for data access abstraction:
```python
class MemoryRepository:
    async def create(self, memory: Memory) -> Memory
    async def get_by_id(self, id: str) -> Optional[Memory]
    async def update(self, id: str, data: dict) -> Memory
    async def delete(self, id: str) -> bool
```

### 2. Service Layer Pattern
Business logic is encapsulated in service classes:
```python
class MemoryService:
    def __init__(self, repo: MemoryRepository, ai_service: AIService):
        self.repo = repo
        self.ai_service = ai_service
    
    async def create_memory_with_ai(self, data: MemoryCreate) -> Memory:
        # Business logic here
```

### 3. Dependency Injection
FastAPI's dependency injection system is used throughout:
```python
@router.post("/memories")
async def create_memory(
    memory: MemoryCreate,
    service: MemoryService = Depends(get_memory_service),
    current_user: User = Depends(get_current_user)
):
    return await service.create_memory(memory, current_user)
```

### 4. Component Composition (Frontend)
React components are composed for reusability:
```jsx
<MemoryList>
  <MemoryCard />
  <MemoryCard />
</MemoryList>
```

## Security Architecture

### Authentication Flow
1. User submits credentials to `/auth/login`
2. Backend validates credentials against hashed password
3. JWT token is generated with user claims
4. Token is returned to frontend and stored in localStorage
5. Subsequent requests include token in Authorization header
6. Backend validates token and extracts user information

### Security Measures
- **Password Hashing**: bcrypt with salt rounds
- **JWT Tokens**: Short-lived access tokens (30 minutes)
- **HTTPS**: All production traffic encrypted
- **CORS**: Configured for specific origins
- **Rate Limiting**: Per-user and per-IP limits
- **Input Validation**: Pydantic models for all inputs
- **SQL Injection**: Prevented by using ODM
- **XSS Prevention**: React's built-in escaping
- **CSRF Protection**: SameSite cookies

## Data Flow

### Memory Creation Flow
1. User enters memory in frontend
2. Frontend sends POST request to `/memories`
3. Backend validates input with Pydantic
4. AI service processes memory:
   - Mood detection
   - Keyword extraction
   - Response generation
   - Embedding creation
5. Memory saved to MongoDB
6. Embedding saved to ChromaDB
7. Response returned to frontend
8. UI updates with new memory

### Search Flow
1. User enters search query
2. Query sent to `/search` endpoint
3. Backend creates query embedding
4. ChromaDB performs similarity search
5. Results filtered and ranked
6. Enriched results returned to frontend

## Scalability Considerations

### Horizontal Scaling
- **Frontend**: Static files served via CDN
- **Backend**: Multiple FastAPI instances behind load balancer
- **Database**: MongoDB replica sets with sharding
- **Cache**: Redis cluster for session and cache data

### Performance Optimizations
- **Database Indexes**: On frequently queried fields
- **Caching**: Redis for frequently accessed data
- **Lazy Loading**: Frontend components loaded on demand
- **Pagination**: API responses paginated
- **Image Optimization**: Automatic resizing and compression
- **Connection Pooling**: Database connection reuse

## Deployment Architecture

### Production Environment
```
┌─────────────────┐     ┌─────────────────┐
│   CloudFlare    │     │   AWS ALB       │
│   (CDN/WAF)     │     │ (Load Balancer) │
└────────┬────────┘     └────────┬────────┘
         │                       │
         │                       │
┌────────▼────────┐     ┌────────▼────────┐
│   S3 Bucket     │     │   ECS Cluster   │
│ (Static Assets) │     │  (Backend API)  │
└─────────────────┘     └─────────────────┘
                                 │
                        ┌────────┴────────┐
                        │                 │
               ┌────────▼──────┐ ┌────────▼──────┐
               │  MongoDB      │ │  Redis        │
               │  Atlas        │ │  ElastiCache  │
               └───────────────┘ └───────────────┘
```

## Monitoring and Observability

### Metrics Collection
- **Application Metrics**: Custom metrics via Prometheus
- **Infrastructure Metrics**: CloudWatch/Datadog
- **Business Metrics**: Custom dashboards in Grafana

### Logging Strategy
- **Structured Logging**: JSON format for all logs
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Correlation IDs**: Track requests across services
- **Log Aggregation**: Centralized in Elasticsearch

### Alerting
- **Uptime Monitoring**: Pingdom/UptimeRobot
- **Error Tracking**: Sentry for exceptions
- **Performance**: New Relic/DataDog APM
- **Custom Alerts**: Prometheus AlertManager

## Development Workflow

### Git Flow
```
main
  └── develop
       ├── feature/user-auth
       ├── feature/ai-insights
       └── fix/memory-search
```

### CI/CD Pipeline
1. **Code Push**: Developer pushes to feature branch
2. **CI Triggered**: GitHub Actions runs tests
3. **Code Review**: PR created and reviewed
4. **Merge**: Code merged to develop
5. **Build**: Docker images built
6. **Deploy Staging**: Automatic deployment to staging
7. **Testing**: E2E tests run on staging
8. **Deploy Production**: Manual approval for production

## Future Enhancements

### Planned Features
1. **Real-time Collaboration**: WebSocket-based sharing
2. **Mobile Apps**: React Native applications
3. **Voice Interface**: Voice commands and responses
4. **Advanced Analytics**: ML-based pattern recognition
5. **Export/Import**: Various format support
6. **Plugins**: Extensible architecture

### Technical Improvements
1. **GraphQL API**: For flexible data fetching
2. **Event Sourcing**: For audit trail
3. **Microservices**: Split into smaller services
4. **Kubernetes**: For orchestration
5. **Service Mesh**: Istio for service communication
