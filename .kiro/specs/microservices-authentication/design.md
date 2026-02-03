# Microservices Authentication & User Tracking - Design Document

## Recommended Solution: JWT + API Gateway Pattern

After analyzing the requirements and constraints, I recommend a **hybrid approach** combining:
1. **JWT Token Authentication** for user identity
2. **API Gateway Pattern** for user data enrichment
3. **Redis Caching** for performance
4. **Minimal Local Storage** for resilience

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client/Frontend                          │
└────────────────────────────────┬────────────────────────────────┘
                                 │ JWT Token
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Main Backend (Port 8000)                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Authentication Service                                   │  │
│  │  - Issues JWT tokens (RS256)                            │  │
│  │  - Token contains: user_id, corporate_id, email, role   │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  User Validation API                                      │  │
│  │  - GET /api/auth/validate-user/                          │  │
│  │  - POST /api/auth/enrich-user-data/                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Database: postgres_prod                                  │  │
│  │  - CustomUser, Corporate, CorporateUser                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
┌──────────────────────────────┐  ┌──────────────────────────────┐
│  Billing Service (Port 8002) │  │  Tazama AI (Port 8001)       │
│  ┌────────────────────────┐  │  │  ┌────────────────────────┐  │
│  │ JWT Middleware         │  │  │  │ JWT Middleware         │  │
│  │ - Validates token      │  │  │  │ - Validates token      │  │
│  │ - Extracts user_id     │  │  │  │ - Extracts user_id     │  │
│  └────────────────────────┘  │  │  └────────────────────────┘  │
│  ┌────────────────────────┐  │  │  ┌────────────────────────┐  │
│  │ User Cache Service     │  │  │  │ User Cache Service     │  │
│  │ - Redis cache          │  │  │  │ - Redis cache          │  │
│  │ - API fallback         │  │  │  │ - API fallback         │  │
│  └────────────────────────┘  │  │  └────────────────────────┘  │
│  ┌────────────────────────┐  │  │  ┌────────────────────────┐  │
│  │ Local DB               │  │  │  │ Local DB               │  │
│  │ - Stores UUIDs only    │  │  │  │ - Stores UUIDs only    │  │
│  │ - No user details      │  │  │  │ - No user details      │  │
│  └────────────────────────┘  │  │  └────────────────────────┘  │
└──────────────────────────────┘  └──────────────────────────────┘
                    │                         │
                    └────────────┬────────────┘
                                 ▼
                    ┌────────────────────────┐
                    │  Redis Cache (Shared)  │
                    │  - User data (1h TTL)  │
                    │  - Corporate (24h TTL) │
                    └────────────────────────┘
```

## Component Design

### 1. JWT Token Structure

**Token Payload:**
```json
{
  "user_id": "uuid-string",
  "corporate_id": "uuid-string",
  "username": "john.doe",
  "email": "john@example.com",
  "role": "admin",
  "is_staff": false,
  "exp": 1234567890,
  "iat": 1234567890,
  "iss": "quidpath-backend"
}
```

**Token Generation (Main Backend):**
```python
# quidpath-backend/Authentication/services/jwt_service.py
import jwt
from datetime import datetime, timedelta
from django.conf import settings

def generate_access_token(user, corporate_user=None):
    """Generate JWT access token with user and corporate data"""
    payload = {
        'user_id': str(user.id),
        'username': user.username,
        'email': user.email,
        'is_staff': user.is_staff,
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iat': datetime.utcnow(),
        'iss': 'quidpath-backend'
    }
    
    # Add corporate data if user is a CorporateUser
    if corporate_user:
        payload['corporate_id'] = str(corporate_user.corporate.id)
        payload['role'] = corporate_user.role.name if corporate_user.role else None
    
    return jwt.encode(payload, settings.JWT_PRIVATE_KEY, algorithm='RS256')
```

### 2. JWT Middleware (Microservices)

**Implementation:**
```python
# billing/billing_service/middleware/jwt_auth.py
import jwt
import requests
from django.conf import settings
from django.http import JsonResponse
from functools import wraps

class JWTAuthenticationMiddleware:
    """Middleware to validate JWT tokens and attach user data to request"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.cache_service = UserCacheService()
    
    def __call__(self, request):
        # Skip authentication for public endpoints
        if self._is_public_endpoint(request.path):
            return self.get_response(request)
        
        # Extract token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Missing or invalid authorization header'}, status=401)
        
        token = auth_header.split(' ')[1]
        
        try:
            # Decode and validate token
            payload = jwt.decode(
                token,
                settings.JWT_PUBLIC_KEY,
                algorithms=['RS256'],
                issuer='quidpath-backend'
            )
            
            # Attach user data to request
            request.user_id = payload['user_id']
            request.corporate_id = payload.get('corporate_id')
            request.user_data = {
                'id': payload['user_id'],
                'username': payload['username'],
                'email': payload['email'],
                'role': payload.get('role'),
                'is_staff': payload.get('is_staff', False)
            }
            
            # Enrich with cached/API data
            request.user_data = self.cache_service.get_user_data(payload['user_id'])
            if request.corporate_id:
                request.corporate_data = self.cache_service.get_corporate_data(request.corporate_id)
            
        except jwt.ExpiredSignatureError:
            return JsonResponse({'error': 'Token has expired'}, status=401)
        except jwt.InvalidTokenError as e:
            return JsonResponse({'error': f'Invalid token: {str(e)}'}, status=401)
        except Exception as e:
            return JsonResponse({'error': f'Authentication failed: {str(e)}'}, status=500)
        
        return self.get_response(request)
    
    def _is_public_endpoint(self, path):
        """Check if endpoint is public (no authentication required)"""
        public_paths = ['/health/', '/api/docs/', '/admin/']
        return any(path.startswith(p) for p in public_paths)
```

### 3. User Cache Service

**Implementation:**
```python
# billing/billing_service/services/user_cache_service.py
import redis
import requests
import json
from django.conf import settings
from typing import Optional, Dict

class UserCacheService:
    """Service for caching and fetching user/corporate data"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self.user_ttl = 3600  # 1 hour
        self.corporate_ttl = 86400  # 24 hours
        self.backend_url = settings.ERP_BACKEND_URL
    
    def get_user_data(self, user_id: str) -> Dict:
        """Get user data from cache or API"""
        cache_key = f"user:{user_id}"
        
        # Try cache first
        cached_data = self.redis_client.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
        
        # Fetch from API
        user_data = self._fetch_user_from_api(user_id)
        if user_data:
            # Cache the result
            self.redis_client.setex(
                cache_key,
                self.user_ttl,
                json.dumps(user_data)
            )
        
        return user_data or {}
    
    def get_corporate_data(self, corporate_id: str) -> Dict:
        """Get corporate data from cache or API"""
        cache_key = f"corporate:{corporate_id}"
        
        # Try cache first
        cached_data = self.redis_client.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
        
        # Fetch from API
        corporate_data = self._fetch_corporate_from_api(corporate_id)
        if corporate_data:
            # Cache the result
            self.redis_client.setex(
                cache_key,
                self.corporate_ttl,
                json.dumps(corporate_data)
            )
        
        return corporate_data or {}
    
    def invalidate_user_cache(self, user_id: str):
        """Invalidate user cache (called via webhook)"""
        self.redis_client.delete(f"user:{user_id}")
    
    def invalidate_corporate_cache(self, corporate_id: str):
        """Invalidate corporate cache (called via webhook)"""
        self.redis_client.delete(f"corporate:{corporate_id}")
    
    def _fetch_user_from_api(self, user_id: str) -> Optional[Dict]:
        """Fetch user data from main backend API"""
        try:
            response = requests.get(
                f"{self.backend_url}/api/auth/users/{user_id}/",
                headers={
                    'X-Service-Key': settings.SERVICE_API_KEY
                },
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to fetch user data: {e}")
            return None
    
    def _fetch_corporate_from_api(self, corporate_id: str) -> Optional[Dict]:
        """Fetch corporate data from main backend API"""
        try:
            response = requests.get(
                f"{self.backend_url}/api/corporates/{corporate_id}/",
                headers={
                    'X-Service-Key': settings.SERVICE_API_KEY
                },
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to fetch corporate data: {e}")
            return None
```

### 4. Main Backend API Endpoints

**User Validation Endpoint:**
```python
# quidpath-backend/Authentication/views/user_api.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from Authentication.models import CustomUser
from OrgAuth.models import CorporateUser, Corporate

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_details(request, user_id):
    """Get user details for microservices"""
    # Validate service API key
    service_key = request.headers.get('X-Service-Key')
    if service_key != settings.SERVICE_API_KEY:
        return Response({'error': 'Invalid service key'}, status=403)
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    # Check if user is a CorporateUser
    corporate_user = None
    corporate_data = None
    try:
        corporate_user = CorporateUser.objects.get(customuser_ptr_id=user_id)
        corporate_data = {
            'id': str(corporate_user.corporate.id),
            'name': corporate_user.corporate.name,
            'industry': corporate_user.corporate.industry,
            'is_active': corporate_user.corporate.is_active,
            'is_approved': corporate_user.corporate.is_approved
        }
    except CorporateUser.DoesNotExist:
        pass
    
    return Response({
        'id': str(user.id),
        'username': user.username,
        'email': user.email,
        'phone_number': user.phone_number,
        'is_active': user.is_active,
        'is_staff': user.is_staff,
        'date_joined': user.date_joined.isoformat(),
        'corporate': corporate_data,
        'role': corporate_user.role.name if corporate_user and corporate_user.role else None
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_corporate_details(request, corporate_id):
    """Get corporate details for microservices"""
    # Validate service API key
    service_key = request.headers.get('X-Service-Key')
    if service_key != settings.SERVICE_API_KEY:
        return Response({'error': 'Invalid service key'}, status=403)
    
    corporate = get_object_or_404(Corporate, id=corporate_id)
    
    return Response({
        'id': str(corporate.id),
        'name': corporate.name,
        'industry': corporate.industry,
        'company_size': corporate.company_size,
        'registration_number': corporate.registration_number,
        'email': corporate.email,
        'phone': corporate.phone,
        'address': corporate.address,
        'city': corporate.city,
        'country': corporate.country,
        'is_active': corporate.is_active,
        'is_approved': corporate.is_approved,
        'is_verified': corporate.is_verified
    })
```

### 5. Database Schema (Microservices)

**No changes needed!** The current UUID-based approach is correct:

```python
# Billing Service Models (CURRENT - KEEP AS IS)
class Subscription(BaseModel):
    corporate_id = models.UUIDField()  # Reference to ERP Corporate
    user_id = models.UUIDField()  # Reference to ERP CorporateUser
    # ... other fields

# Tazama AI Models (CURRENT - KEEP AS IS)
class TazamaAnalysisRequest(BaseModel):
    corporate_id = models.UUIDField()  # Reference to ERP Corporate
    requested_by_id = models.UUIDField()  # Reference to ERP CorporateUser
    # ... other fields
```

**Why this works:**
- UUIDs are stored as references (foreign key concept without actual FK constraint)
- User details are fetched dynamically via cache/API when needed
- No database coupling between services
- Maintains data integrity through application logic

### 6. Configuration

**Main Backend Settings:**
```python
# quidpath-backend/quidpath_backend/settings/prod.py

# JWT Configuration
JWT_ALGORITHM = 'RS256'
JWT_PRIVATE_KEY = open(os.path.join(BASE_DIR, 'keys/jwt_private.pem')).read()
JWT_PUBLIC_KEY = open(os.path.join(BASE_DIR, 'keys/jwt_public.pem')).read()
JWT_ACCESS_TOKEN_LIFETIME = timedelta(hours=1)
JWT_REFRESH_TOKEN_LIFETIME = timedelta(days=7)

# Service API Keys (for microservice-to-backend communication)
SERVICE_API_KEYS = {
    'billing-service': os.getenv('BILLING_SERVICE_API_KEY'),
    'tazama-service': os.getenv('TAZAMA_SERVICE_API_KEY')
}
```

**Microservice Settings:**
```python
# billing/billing_service/settings/prod.py

# JWT Configuration
JWT_PUBLIC_KEY = open(os.path.join(BASE_DIR, 'keys/jwt_public.pem')).read()
JWT_ALGORITHM = 'RS256'

# Main Backend API
ERP_BACKEND_URL = os.getenv('ERP_BACKEND_URL', 'https://api.quidpath.com')
SERVICE_API_KEY = os.getenv('SERVICE_API_KEY')  # Unique per service

# Redis Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

# Cache TTLs
USER_CACHE_TTL = 3600  # 1 hour
CORPORATE_CACHE_TTL = 86400  # 24 hours
```

## Data Flow Examples

### Example 1: User Creates Billing Subscription

1. **Frontend** → Sends request to Billing Service with JWT token
2. **Billing Middleware** → Validates JWT, extracts user_id and corporate_id
3. **Billing Middleware** → Checks Redis cache for user data
4. **Cache Miss** → Calls Main Backend API to fetch user details
5. **Main Backend** → Returns user and corporate data
6. **Billing Service** → Caches data in Redis, attaches to request
7. **Billing View** → Creates subscription with corporate_id and user_id (UUIDs)
8. **Response** → Returns subscription data with enriched user info

### Example 2: Displaying Audit Logs

1. **Admin** → Requests audit logs from Tazama Service
2. **Tazama Service** → Queries local DB for logs (has user_id UUIDs)
3. **Tazama Service** → Batch fetches user details from cache/API
4. **Response** → Returns logs with enriched user data (username, email, corporate name)

## Security Considerations

1. **JWT Keys**: Use RS256 (asymmetric) to prevent token forgery
2. **Service API Keys**: Rotate regularly, store in secrets manager
3. **HTTPS Only**: All communication must use TLS
4. **Rate Limiting**: Implement on both main backend and microservices
5. **Token Expiry**: Short-lived access tokens (1 hour), refresh tokens for renewal
6. **Cache Security**: Use Redis AUTH, encrypt sensitive cached data

## Performance Optimization

1. **Connection Pooling**: Reuse HTTP connections to main backend
2. **Batch API Calls**: Fetch multiple users/corporates in single request
3. **Async Requests**: Use async HTTP client for non-blocking calls
4. **Cache Warming**: Pre-populate cache for frequently accessed users
5. **Circuit Breaker**: Fail fast if main backend is down, use stale cache

## Monitoring & Observability

**Metrics to Track:**
- JWT validation success/failure rate
- Cache hit/miss ratio
- API call latency to main backend
- Authentication errors by type
- User data staleness (time since last sync)

**Logging:**
- All authentication attempts (success/failure)
- Cache invalidations
- API calls to main backend
- Service API key usage

## Migration Plan

1. **Phase 1**: Add JWT middleware to microservices (non-breaking)
2. **Phase 2**: Implement user cache service
3. **Phase 3**: Add main backend API endpoints
4. **Phase 4**: Update microservice views to use enriched user data
5. **Phase 5**: Add monitoring and alerting
6. **Phase 6**: Optimize cache TTLs based on metrics

## Alternative Approaches Considered

### ❌ Shared Database
**Pros**: Simple, no API calls needed  
**Cons**: Tight coupling, violates microservice principles, scaling issues

### ❌ Database Replication
**Pros**: Fast reads, no API calls  
**Cons**: Complex setup, data consistency issues, security risks

### ❌ Event Sourcing
**Pros**: Full audit trail, eventual consistency  
**Cons**: Complex implementation, overkill for this use case

### ✅ JWT + API Gateway (Recommended)
**Pros**: Loose coupling, scalable, secure, industry standard  
**Cons**: Slight latency (mitigated by caching)

## Conclusion

The recommended JWT + API Gateway pattern provides the best balance of:
- **Independence**: Microservices remain autonomous
- **Performance**: Redis caching minimizes latency
- **Security**: Industry-standard JWT authentication
- **Maintainability**: Clear separation of concerns
- **Scalability**: Horizontal scaling supported

This approach is battle-tested in production microservice architectures and aligns with industry best practices.
