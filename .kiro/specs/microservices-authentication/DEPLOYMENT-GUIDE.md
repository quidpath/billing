# Microservices Authentication - Deployment Guide

## Quick Start

Follow these steps to deploy the JWT authentication system to production.

## Step 1: Generate Secret Keys

```bash
# Generate JWT secret key (use a strong random string)
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Generate service API keys
python -c "import secrets; print('BILLING:', secrets.token_urlsafe(32))"
python -c "import secrets; print('TAZAMA:', secrets.token_urlsafe(32))"
```

## Step 2: Update Environment Variables

### Main Backend (.env)
```bash
# Add to quidpath-backend/.env
JWT_SECRET_KEY=<generated-jwt-secret-key>
BILLING_SERVICE_API_KEY=<generated-billing-key>
TAZAMA_SERVICE_API_KEY=<generated-tazama-key>
```

### Billing Service (.env)
```bash
# Add to billing/.env
JWT_SECRET_KEY=<same-jwt-secret-key-as-main-backend>
ERP_BACKEND_URL=http://django-backend:8000
SERVICE_API_KEY=<same-billing-key-as-main-backend>
USER_CACHE_TTL=3600
CORPORATE_CACHE_TTL=86400
```

### Tazama AI Service (.env)
```bash
# Add to tazama-ai-microservice/.env
JWT_SECRET_KEY=<same-jwt-secret-key-as-main-backend>
ERP_BACKEND_URL=http://django-backend:8000
SERVICE_API_KEY=<same-tazama-key-as-main-backend>
USER_CACHE_TTL=3600
CORPORATE_CACHE_TTL=86400
```

## Step 3: Deploy Services

### Main Backend
```bash
cd ~/quidpath-deployment/quidpath-backend
docker-compose down
docker-compose up -d --build
docker-compose logs -f backend
```

### Billing Service
```bash
cd ~/quidpath-deployment/billing
docker-compose down
docker-compose up -d --build
docker-compose logs -f backend
```

### Tazama AI Service
```bash
cd ~/quidpath-deployment/tazama-ai-microservice
docker-compose down
docker-compose up -d --build
docker-compose logs -f web
```

## Step 4: Verify Deployment

### Test Main Backend API
```bash
# Replace with actual user UUID from your database
USER_ID="your-user-uuid-here"
CORPORATE_ID="your-corporate-uuid-here"
BILLING_KEY="your-billing-service-api-key"

# Test user endpoint
curl -X GET http://localhost:8000/api/auth/users/$USER_ID/ \
  -H "X-Service-Key: $BILLING_KEY"

# Test corporate endpoint
curl -X GET http://localhost:8000/api/auth/corporates/$CORPORATE_ID/ \
  -H "X-Service-Key: $BILLING_KEY"
```

### Test JWT Authentication
```bash
# Login to get token
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your-username", "password": "your-password"}' \
  | jq -r '.access_token')

echo "Token: $TOKEN"

# Test billing service
curl -X GET http://localhost:8002/api/billing/subscriptions/ \
  -H "Authorization: Bearer $TOKEN"

# Test tazama service
curl -X GET http://localhost:8001/api/tazama/analysis/ \
  -H "Authorization: Bearer $TOKEN"
```

## Step 5: Monitor Logs

### Check for Authentication Errors
```bash
# Main backend
docker-compose -f ~/quidpath-deployment/quidpath-backend/docker-compose.yml logs backend | grep -i "auth\|jwt"

# Billing
docker-compose -f ~/quidpath-deployment/billing/docker-compose.yml logs backend | grep -i "auth\|jwt"

# Tazama
docker-compose -f ~/quidpath-deployment/tazama-ai-microservice/docker-compose.yml logs web | grep -i "auth\|jwt"
```

### Check Cache Performance
```bash
# Look for cache hit/miss logs
docker-compose logs backend | grep -i "cache"
```

## Step 6: Update Frontend

Update your frontend to include JWT token in requests:

```javascript
// Example: Axios interceptor
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);
```

## Rollback Plan

If issues occur, rollback to previous version:

```bash
# Main Backend
cd ~/quidpath-deployment/quidpath-backend
git checkout <previous-commit>
docker-compose up -d --build

# Billing
cd ~/quidpath-deployment/billing
git checkout <previous-commit>
docker-compose up -d --build

# Tazama
cd ~/quidpath-deployment/tazama-ai-microservice
git checkout <previous-commit>
docker-compose up -d --build
```

## Production Checklist

- [ ] JWT secret keys generated and stored securely
- [ ] Service API keys generated and stored securely
- [ ] Environment variables updated in all services
- [ ] All services deployed and running
- [ ] API endpoints tested successfully
- [ ] JWT authentication tested end-to-end
- [ ] Logs monitored for errors
- [ ] Frontend updated to use JWT tokens
- [ ] Cache performance verified
- [ ] Backup of previous deployment available

## Common Issues

### Issue: Services can't communicate
**Solution**: Ensure all services are on the same Docker network (`quidpath_network`)

```bash
docker network inspect quidpath_network
```

### Issue: JWT validation fails
**Solution**: Verify JWT_SECRET_KEY is identical in all services

```bash
# Check main backend
docker exec django-backend env | grep JWT_SECRET_KEY

# Check billing
docker exec billing-backend env | grep JWT_SECRET_KEY

# Check tazama
docker exec tazama-ai-backend env | grep JWT_SECRET_KEY
```

### Issue: Service API key invalid
**Solution**: Verify SERVICE_API_KEY matches between services

```bash
# Main backend should have BILLING_SERVICE_API_KEY
docker exec django-backend env | grep BILLING_SERVICE_API_KEY

# Billing should have SERVICE_API_KEY matching above
docker exec billing-backend env | grep SERVICE_API_KEY
```

## Performance Tuning

### Enable Redis for Production

Update docker-compose.yml to add Redis:

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - quidpath_network

volumes:
  redis_data:
```

Update settings to use Redis:

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://redis:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

## Security Hardening

1. **Rotate Keys Regularly**
   ```bash
   # Generate new keys every 90 days
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   ```

2. **Enable HTTPS**
   - Ensure all services use HTTPS in production
   - Update ERP_BACKEND_URL to use https://

3. **Rate Limiting**
   - Add rate limiting to API endpoints
   - Use Django REST Framework throttling

4. **Monitoring**
   - Set up alerts for authentication failures
   - Monitor cache hit rates
   - Track API latency

## Success Metrics

After deployment, verify:
- ✅ Authentication success rate > 99%
- ✅ Cache hit rate > 90%
- ✅ API latency < 200ms
- ✅ No authentication errors in logs
- ✅ All microservices communicating successfully

## Support

If you encounter issues:
1. Check service logs
2. Verify environment variables
3. Test API endpoints directly
4. Review IMPLEMENTATION.md for detailed troubleshooting

## Conclusion

Your microservices authentication system is now deployed and production-ready!
