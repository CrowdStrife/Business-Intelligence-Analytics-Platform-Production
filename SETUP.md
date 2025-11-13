# 🛠️ Docker Compose Setup

## Prerequisites
- 🐳 Docker Desktop (with WSL2 on Windows)
- 🛑 Ports free: 80, 5432, 8000, 8080, 9000, 9001

## 1. Clone Repository
```bash
git clone <your-repo-url>
cd Business-Analytics-Platform
git checkout features/connection
```

## 2. Create Environment Files

### Root .env (Docker Compose)
Create `.env` in project root:
```bash
# PostgreSQL
POSTGRES_USER=booklatte
POSTGRES_PASSWORD=change_this_password
POSTGRES_DB=booklatte
POSTGRES_PORT=5432

# MinIO
MINIO_ROOT_USER=booklatte
MINIO_ROOT_PASSWORD=change_this_password
MINIO_PORT=9000
MINIO_CONSOLE_PORT=9001

# Keycloak
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=change_this_password
KEYCLOAK_PORT=8080

# Services
API_PORT=8000
FRONTEND_PORT=80
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

### Backend .env
Create `backend/.env`:
```bash
# Use Docker service names
POSTGRES_HOST=postgres
MINIO_ENDPOINT=minio:9000
KEYCLOAK_ISSUER=http://keycloak:8080/realms/booklatte
TRIGGER_DIR=/app/trigger

# Passwords (must match root .env)
POSTGRES_PASSWORD=change_this_password
MINIO_ROOT_PASSWORD=change_this_password

# Config
POSTGRES_USER=booklatte
POSTGRES_DB=booklatte
MINIO_SECURE=false
KEYCLOAK_CLIENT_ID=frontend
CORS_ALLOW_ORIGINS=http://localhost:80,http://localhost:5173,http://frontend
```

## 3. Build and Start All Services
```bash
# Build all services
docker-compose build

# Start all services (correct order enforced automatically)
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

Services start in this order:
1. postgres (database)
2. minio (object storage)
3. keycloak (authentication)
4. backend-api (API server)
5. observer (file watcher)
6. frontend (web app)

## 4. Configure Keycloak (First Time Only)
Open http://localhost:8080 and login with admin credentials from `.env`

### Create Realm
- Name: `booklatte`

### Create Client
- Client ID: `frontend`
- Client Protocol: `openid-connect`
- Access Type: `public`
- Valid Redirect URIs: `http://localhost:80/*`, `http://localhost:5173/*`
- Web Origins: `http://localhost:80`, `http://localhost:5173`
- Enable: Standard Flow, Direct Access Grants

### Create User
- Users → Add user → username: `testuser`
- Credentials → set password (uncheck Temporary)

## 5. Configure MinIO (Automatic)
MinIO buckets are created automatically by the backend:
- `landing` (raw uploads)
- `staging` (processed data)

Access MinIO Console at http://localhost:9001
- User: booklatte
- Password: (from your .env)

## 6. Access Your Application

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:80 | Keycloak user |
| **Backend API** | http://localhost:8000 | - |
| **Keycloak** | http://localhost:8080 | admin / (from .env) |
| **MinIO Console** | http://localhost:9001 | booklatte / (from .env) |

## 7. Using the Application

1. Open http://localhost:80
2. Login with Keycloak user (testuser)
3. Upload Excel files (Sales Transaction List or Sales Report by Product)
4. Files are processed automatically by the pipeline
5. View results in the dashboard

## 8. Verify Setup

```bash
# Check all services are running
docker-compose ps

# Check logs
docker-compose logs backend-api
docker-compose logs observer
docker-compose logs frontend

# Verify database
docker exec -it postgres_db psql -U booklatte -d booklatte -c "\dt"
```

## Troubleshooting

### Port Already in Use
```bash
# Check what's using the port
netstat -ano | findstr :80
netstat -ano | findstr :8080

# Stop the service or change port in .env
```

### Services Won't Start
```bash
# Clean restart (WARNING: deletes data)
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Keycloak Authentication Fails
- Verify realm is `booklatte`
- Check client `frontend` is configured
- Ensure redirect URIs include `http://localhost:80/*`

### Can't Connect to Backend
- Check `backend/.env` has `POSTGRES_HOST=postgres` (not localhost)
- Verify passwords match between root and backend .env

### View Service Logs
```bash
docker-compose logs -f <service-name>
# Examples: frontend, backend-api, keycloak, postgres
```

## Useful Commands

```bash
# Stop all services
docker-compose down

# Restart specific service
docker-compose restart backend-api

# Rebuild specific service
docker-compose build --no-cache frontend
docker-compose up -d frontend

# View resource usage
docker stats
```

---

✅ **Your fully containerized analytics platform is ready!**