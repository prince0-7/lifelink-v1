from datetime import datetime, timedelta
from typing import Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
import redis
import json
from config import settings

class RateLimiter:
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or settings.redis_url
        self.redis_client = None
        if self.redis_url:
            try:
                self.redis_client = redis.from_url(self.redis_url)
                self.redis_client.ping()
            except Exception as e:
                print(f"Redis connection failed: {e}")
                self.redis_client = None

    def _get_identifier(self, request: Request) -> str:
        """Get unique identifier for rate limiting"""
        # Try to get user ID from JWT token
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        client_ip = request.client.host
        return f"ip:{client_ip}"

    def _get_limits(self, identifier: str) -> Dict[str, int]:
        """Get rate limits based on identifier type"""
        if identifier.startswith("user:"):
            return {
                "per_minute": 60,
                "per_hour": 1000,
                "per_day": 10000
            }
        else:
            return {
                "per_minute": 20,
                "per_hour": 100,
                "per_day": 1000
            }

    async def check_rate_limit(self, request: Request) -> Optional[JSONResponse]:
        """Check if request exceeds rate limit"""
        if not self.redis_client:
            # If Redis is not available, allow all requests
            return None

        identifier = self._get_identifier(request)
        limits = self._get_limits(identifier)
        now = datetime.utcnow()

        for period, limit in limits.items():
            if period == "per_minute":
                window = 60
            elif period == "per_hour":
                window = 3600
            else:  # per_day
                window = 86400

            key = f"rate_limit:{identifier}:{period}"
            
            try:
                # Get current count
                current = self.redis_client.get(key)
                if current is None:
                    # First request in this window
                    self.redis_client.setex(key, window, 1)
                    continue
                
                current_count = int(current)
                if current_count >= limit:
                    # Rate limit exceeded
                    retry_after = self.redis_client.ttl(key)
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "detail": f"Rate limit exceeded. Try again in {retry_after} seconds.",
                            "retry_after": retry_after
                        },
                        headers={
                            "Retry-After": str(retry_after),
                            "X-RateLimit-Limit": str(limit),
                            "X-RateLimit-Remaining": "0",
                            "X-RateLimit-Reset": str(int(now.timestamp()) + retry_after)
                        }
                    )
                
                # Increment counter
                self.redis_client.incr(key)
                
            except Exception as e:
                print(f"Rate limiting error: {e}")
                # On error, allow the request
                continue

        return None

class RateLimitMiddleware:
    def __init__(self, app, rate_limiter: RateLimiter):
        self.app = app
        self.rate_limiter = rate_limiter

    async def __call__(self, request: Request, call_next):
        # Skip rate limiting for health check and docs
        if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)

        # Check rate limit
        rate_limit_response = await self.rate_limiter.check_rate_limit(request)
        if rate_limit_response:
            return rate_limit_response

        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to successful responses
        if self.rate_limiter.redis_client and 200 <= response.status_code < 300:
            identifier = self.rate_limiter._get_identifier(request)
            limits = self.rate_limiter._get_limits(identifier)
            
            # Add headers for the hourly limit
            try:
                key = f"rate_limit:{identifier}:per_hour"
                current = self.rate_limiter.redis_client.get(key)
                if current:
                    remaining = limits["per_hour"] - int(current)
                    ttl = self.rate_limiter.redis_client.ttl(key)
                    response.headers["X-RateLimit-Limit"] = str(limits["per_hour"])
                    response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
                    response.headers["X-RateLimit-Reset"] = str(int(datetime.utcnow().timestamp()) + ttl)
            except Exception:
                pass

        return response
