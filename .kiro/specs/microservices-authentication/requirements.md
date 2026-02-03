# Microservices Authentication & User Tracking

## Overview
Design and implement a robust authentication and user tracking system for the Billing and Tazama AI microservices that maintains independence while ensuring seamless integration with the main QuidPath backend's user management system.

## Problem Statement
Currently, the Billing and Tazama AI microservices have removed direct references to `CustomUser`, `Corporate`, and `CorporateUser` models from the main backend, which breaks user tracking and authentication. The microservices need to:
1. Track which users are making requests
2. Associate data with specific corporate entities
3. Maintain independence (separate databases)
4. Avoid tight coupling with the main backend's database

## Current Architecture

### Main Backend (quidpath-backend)
- **Port**: 8000
- **Database**: postgres_prod (quidpath_db)
- **User Model**: `Authentication.CustomUser` (extends AbstractBaseUser)
- **Corporate Model**: `OrgAuth.Corporate` (company/organization entity)
- **Corporate User Model**: `OrgAuth.CorporateUser` (extends CustomUser, links users to corporates)

### Billing Service
- **Port**: 8002
- **Database**: postgres_billing_prod (billing_prod)
- **Current Issue**: Uses UUID fields (`corporate_id`, `uploaded_by_id`) but no way to validate or enrich user data

### Tazama AI Service
- **Port**: 8001
- **Database**: tazama_postgres (tazama_db)
- **Current Issue**: Uses UUID fields (`corporate_id`, `requested_by_id`) but no way to validate or enrich user data

## User Stories

### 1. JWT Token-Based Authentication
**As a** microservice (Billing/Tazama)  
**I want to** validate JWT tokens issued by the main backend  
**So that** I can authenticate users without direct database access

**Acceptance Criteria:**
- 1.1 Microservices can decode and validate JWT tokens from the main backend
- 1.2 JWT tokens contain user_id, corporate_id, email, username, and role information
- 1.3 Invalid or expired tokens are rejected with appropriate error messages
- 1.4 Token validation happens on every authenticated request

### 2. User Data Caching
**As a** microservice  
**I want to** cache user and corporate data locally  
**So that** I can reduce API calls to the main backend and improve performance

**Acceptance Criteria:**
- 2.1 User data is cached in Redis with configurable TTL (default: 1 hour)
- 2.2 Corporate data is cached in Redis with configurable TTL (default: 24 hours)
- 2.3 Cache is automatically invalidated when user/corporate data changes
- 2.4 Cache misses trigger API calls to the main backend to fetch fresh data

### 3. User Validation API
**As a** microservice  
**I want to** call the main backend API to validate and fetch user details  
**So that** I can ensure user data is current and accurate

**Acceptance Criteria:**
- 3.1 Main backend exposes `/api/auth/validate-user/` endpoint
- 3.2 Endpoint accepts JWT token and returns user details (id, username, email, corporate_id, role)
- 3.3 Endpoint returns corporate details (id, name, industry, is_active)
- 3.4 Endpoint handles rate limiting (max 100 requests/minute per service)
- 3.5 Failed validations return clear error messages

### 4. Audit Trail & User Tracking
**As a** system administrator  
**I want to** track which users performed which actions in microservices  
**So that** I can maintain audit logs and ensure accountability

**Acceptance Criteria:**
- 4.1 All database records store user_id and corporate_id as UUIDs
- 4.2 Audit logs include timestamp, user_id, corporate_id, action, and result
- 4.3 Logs are queryable by user_id, corporate_id, date range
- 4.4 User details (username, email) are enriched from cache/API when displaying logs

### 5. Service-to-Service Authentication
**As a** microservice  
**I want to** authenticate with the main backend using service credentials  
**So that** I can make API calls on behalf of the service (not a specific user)

**Acceptance Criteria:**
- 5.1 Each microservice has a unique service API key
- 5.2 Service API keys are stored securely in environment variables
- 5.3 Main backend validates service API keys before processing requests
- 5.4 Service-to-service calls are logged separately from user requests

### 6. User Synchronization (Optional)
**As a** microservice  
**I want to** maintain a read-only copy of essential user data  
**So that** I can function even if the main backend is temporarily unavailable

**Acceptance Criteria:**
- 6.1 Microservices store minimal user data (id, username, email, corporate_id) in local database
- 6.2 User data is synchronized via webhook when users are created/updated in main backend
- 6.3 Synchronization is eventual (not real-time)
- 6.4 Local user data is marked as "cached" and includes last_synced_at timestamp

### 7. Corporate Context Middleware
**As a** developer  
**I want to** automatically extract user and corporate context from requests  
**So that** I don't have to manually parse JWT tokens in every view

**Acceptance Criteria:**
- 7.1 Middleware extracts JWT token from Authorization header
- 7.2 Middleware validates token and attaches user data to request object
- 7.3 Middleware attaches corporate data to request object
- 7.4 Views can access `request.user_data` and `request.corporate_data`
- 7.5 Unauthenticated requests are rejected with 401 status

## Technical Constraints

1. **No Direct Database Access**: Microservices MUST NOT connect to the main backend's database
2. **Independence**: Each microservice must function with its own database
3. **Loose Coupling**: Changes to main backend user models should not break microservices
4. **Performance**: User validation should not add more than 50ms latency to requests
5. **Security**: JWT tokens must use RS256 (asymmetric) encryption
6. **Scalability**: Solution must support horizontal scaling of microservices

## Non-Functional Requirements

1. **Availability**: 99.9% uptime for authentication services
2. **Performance**: < 50ms for cached user lookups, < 200ms for API-based lookups
3. **Security**: All communication over HTTPS, tokens expire after 1 hour
4. **Monitoring**: Track authentication failures, cache hit rates, API call latency
5. **Documentation**: Clear API documentation for all authentication endpoints

## Out of Scope

1. User registration/creation in microservices (only main backend creates users)
2. Password management in microservices
3. Role-based access control (RBAC) within microservices (handled by main backend)
4. Multi-factor authentication (MFA) in microservices

## Success Metrics

1. 95%+ cache hit rate for user data lookups
2. < 100ms average authentication latency
3. Zero authentication-related security incidents
4. 100% audit trail coverage for all user actions
5. < 1% authentication failure rate (excluding invalid credentials)

## Dependencies

1. Main backend must expose user validation API
2. Redis instance for caching (shared or per-service)
3. JWT library (PyJWT) for token handling
4. Requests library for HTTP calls to main backend

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Main backend API unavailable | High | Implement circuit breaker, use cached data, graceful degradation |
| JWT secret key compromise | Critical | Use asymmetric keys (RS256), rotate keys regularly, monitor for suspicious activity |
| Cache poisoning | Medium | Validate all cached data, use signed cache entries, implement cache versioning |
| Performance degradation | Medium | Implement connection pooling, use async requests, monitor API latency |
| User data inconsistency | Low | Implement webhook-based synchronization, add data validation checks |

## Related Documentation

- JWT Authentication: https://jwt.io/introduction
- Django REST Framework JWT: https://www.django-rest-framework.org/api-guide/authentication/#json-web-token-authentication
- Microservices Authentication Patterns: https://microservices.io/patterns/security/access-token.html
