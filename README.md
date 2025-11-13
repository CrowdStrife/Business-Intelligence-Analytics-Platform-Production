## Capstone Business Analytics Project

**Fully containerized analytics platform** for restaurant sales data  
ETL + Market Basket Analysis + Forecasting + Price Elasticity Analysis

**Tech Stack:**
- 🐳 Docker Compose (all services containerized)
- ⚛️ React + TypeScript (frontend)
- 🚀 FastAPI (backend API)
- 🐘 PostgreSQL (data warehouse)
- 🪣 MinIO (object storage)
- 🔐 Keycloak (authentication)
- 🐍 Python (analytics pipeline)

---

## 🚀 Quick Start

**Prerequisites:** Docker Desktop

```bash
# 1. Clone and setup
git clone <repo-url>
cd Business-Analytics-Platform

# 2. Create .env files (see SETUP.md for details)
# Root .env and backend/.env

# 3. Start everything
docker-compose build
docker-compose up -d

# 4. Access frontend
http://localhost:80
```

**See [SETUP.md](SETUP.md) for detailed setup instructions.**

---

## 📁 Repository Structure

```
Business-Analytics-Platform/
├── frontend/                    # React + TypeScript web application
│   ├── src/
│   │   ├── components/          # UI components (Dashboard, DataUpload, Navigation)
│   │   ├── keycloak.ts          # Keycloak authentication integration
│   │   ├── config.ts            # Frontend configuration
│   │   ├── App.tsx              # Main application component
│   │   └── main.tsx             # Application entry point
│   ├── Dockerfile               # Multi-stage build (Node.js + Nginx)
│   ├── nginx.conf               # Nginx configuration for SPA routing
│   └── package.json             # Dependencies (React 19, Vite, Keycloak)
│
├── backend/                     # FastAPI backend + analytics pipeline
│   ├── app/
│   │   ├── api/
│   │   │   └── upload.py        # File upload endpoint (JWT protected)
│   │   ├── core/
│   │   │   └── config.py        # Centralized configuration
│   │   ├── services/
│   │   │   ├── auth.py          # JWT validation with Keycloak
│   │   │   └── storage.py       # MinIO integration
│   │   ├── observer/
│   │   │   └── handler.py       # Watchdog file system handler
│   │   ├── pipeline/
│   │   │   ├── etl.py           # ETL (Extract, Transform, Load)
│   │   │   ├── mba.py           # Market Basket Analysis (FP-Growth)
│   │   │   ├── ped.py           # Price Elasticity of Demand
│   │   │   ├── nlp.py           # Non-Linear Programming optimization
│   │   │   ├── holtwinters.py   # Holt-Winters forecasting
│   │   │   └── run_all.py       # Pipeline orchestrator
│   │   └── main.py              # FastAPI app initialization
│   ├── Dockerfile               # Python 3.11 container
│   ├── requirements.txt         # Python dependencies
│   ├── run_api.py               # API server entry point
│   └── run_observer.py          # Observer service entry point
│
├── db/                          # PostgreSQL initialization scripts
│   └── init/                    # Database schema creation
│
├── docker-compose.yml           # Orchestrates all services
├── .env                         # Docker Compose environment variables
└── SETUP.md                     # Complete setup guide
```

---

## 1. ETL Pipeline (`etl.py`)

**Phases:** Extract → Transform → Load (with enhanced numeric coercion & outlier auditability)

- **Extract:**  
  Reads all `.xlsx` files in `raw_sales/` and `raw_sales_by_product/`.  
  Auto-detects header row (scans first 10 rows for tokens like `date`, `receipt`, `product`, etc.; defaults to row 4 if not found).  
  Normalizes columns across files; fills missing columns with `None`.  
  Standardizes "Take Out" flag (`Y` → `True`, blanks → `False`).

- **Transform:**  
  Cleans columns/rows (drops unused admin fields, removes blank `Date`/`Time`).  
  Normalizes product naming/IDs (first ID per canonical name).  
  Uppercases product names & standardizes receipt key.  
  Merges Sales Transaction List ↔ Sales by Product on `Receipt No`.  
  Performs numeric coercion on key metrics (`Qty`, `Price`, `Line Total`, `Net Total`) and logs coercion-induced NaNs.  
  Flags outliers using enhanced IQR logic (details below) before optional row removal.

**Outlier Detection & Removal (Overview):**

| Aspect | Logic |
| ------ | ----- |
| Method | IQR (Tukey fences) per metric (`Qty`, `Price`, `Line Total`, `Net Total` if present) |
| Per-Feature k | Custom k overrides (e.g. `{'Qty':1.2,'Price':2.0}`) fall back to global default (1.5) |
| Category-Aware | Optional segmentation: bounds computed within each `CATEGORY` to avoid cross-category skew |
| Log-Scale Price | Optional: Price bounds computed in log-space (multiplicative fence) to preserve legitimately high-priced premium items |
| Removal Rule | A row is removed only if ≥ 2 different metrics are individually flagged as outliers |
| Artifacts | Full, flagged, removed snapshot, value-level log, numeric coercion report |

**Generated Outlier & Coercion Artifacts (in `etl_dimensions/`):**

| File | Description |
| ---- | ----------- |
| `fact_transaction_full.csv` | Pre-removal fact snapshot (includes `__outlier_*` helper flag columns) |
| `fact_transaction_with_flags.csv` | Alias (currently same as full; future divergence placeholder) |
| `outliers_removed.csv` | Value-level log: one row per flagged value (row index, column, value, method, k, lower, upper, deviation) |
| `outlier_rows_snapshot.csv` | Entire rows meeting multi-metric removal rule (before they are dropped) |
| `numeric_coercion_report.csv` | Counts of newly introduced NaNs per coerced numeric column |

**Load:**
  - **Fact Transaction Dimension:** `fact_transaction_dimension.csv` (cleaned line-level fact after optional outlier row removal & duplicate pruning).  
  - **Product Dimension (SCD Type 4):**
    - `current_product_dimension.csv`: latest row per product with `parent_sku`, `CATEGORY`, `last_transaction_date`, cost inference, SCD metadata.
    - `history_product_dimension.csv`: all historical versions (SCD lineage).  
  - **Parent SKU Derivation:** Removes size/temperature tokens (`ICED`, `HOT`, `8OZ`, etc.), cleans noise, consolidates core product root (`parent_sku`).  
  - **Category Classification:** Heuristic keyword + pattern rules → `DRINK`, `FOOD`, `EXTRA`, `OTHERS`.  
  - **Transaction Records:** `transaction_records.csv` (one row per receipt; `SKU` is comma‑separated `parent_sku` list; reflects cleaned fact after removals).  
  - **Time Dimension:** `time_dimension.csv` (Year → Day hierarchy).

**Intermediate Cleaned Data:**

- `cleaned_data/sales_transactions.csv`
- `cleaned_data/sales_by_product.csv`

**Primary Output & Supporting Files:**

| File | Purpose |
| ---- | ------- |
| `fact_transaction_dimension.csv` | Cleaned line-level fact (post-removal) |
| `fact_transaction_full.csv` | Pre-removal snapshot with helper flags |
| `fact_transaction_with_flags.csv` | Same as full (reserved for future variant behavior) |
| `outliers_removed.csv` | Value-level outlier log (audit trail) |
| `outlier_rows_snapshot.csv` | Full rows that were removed (data provenance) |
| `numeric_coercion_report.csv` | Summary of coercion-induced NaNs |
| `current_product_dimension.csv` | Current SCD slice (Type 4) |
| `history_product_dimension.csv` | All historical product versions |
| `transaction_records.csv` | Receipt-level basket (post-removal) |
| `time_dimension.csv` | Calendar hierarchy for analytics |
| `cleaned_data/*.csv` | Pre-merge cleaned intermediary sources |

---

## 2. Market Basket Analysis (`mba.py`)

Enhanced to operate on multiple ETL outputs and provide a flexible CLI.

**Sources (`--source`):**
| Option | Description |
| ------ | ----------- |
| `transactions` (default) | Uses `transaction_records.csv` (receipt-level baskets, post-removal) |
| `fact` | Rebuilds baskets from `fact_transaction_dimension.csv` |
| `full` | Rebuilds baskets from `fact_transaction_full.csv` (pre-removal; includes flagged rows) |
| `flags` | Rebuilds baskets from `fact_transaction_with_flags.csv` |

If `transaction_records.csv` is missing and `--source transactions` is chosen, it falls back to `fact`.

**Key CLI Arguments:**
```
python mba.py \
  --source full \
  --exclude-flagged \
  --group-by parent_sku \
  --min-support 0.003 \
  --min-confidence 0.03 \
  --min-lift 1.0 \
  --exclude-cats EXTRA OTHERS \
  --no-category-runs
```

| Flag | Purpose |
| ---- | ------- |
| `--group-by parent_sku|product_id` | Choose item granularity for baskets |
| `--exclude-flagged` | Drop any rows with `__outlier_*` flags (only relevant for `full` / `flags` sources) |
| `--exclude-cats` | Skip categories (default: EXTRA, OTHERS) in itemsets & rules |
| `--no-category-runs` | Skip per-category FOOD / DRINK sub-analyses |
| `--min-support` | Minimum FP-Growth support |
| `--min-confidence` | Minimum rule confidence |
| `--min-lift` | Minimum rule lift |

**Processing Flow:**
1. Load or reconstruct baskets (`Receipt No`, `SKU`).
2. One-hot encode items (comma-separated SKUs).
3. Run FP-Growth → frequent itemsets.
4. Generate association rules (confidence filter) → filter by lift & exclusions.
5. De-duplicate reversed rule pairs & compute `combined_score = lift*0.7 + normalized_support*30`.
6. Export Excel + CSV to `mba_results/` (and category folders if enabled).

**Outputs:**
| File | Description |
| ---- | ----------- |
| `mba_results/frequent_itemsets.csv` | Frequent itemsets + support |
| `mba_results/association_rules.csv` | Ranked rules (support, confidence, lift, leverage, conviction, combined_score) |
| `mba_results/market_basket_analysis_results.xlsx` | Excel with both tabs |
| `mba_foods/*` / `mba_drinks/*` | Category-specific results (if enabled) |

**Choosing a Source:**
- Use `transactions` for production-quality basket mining (cleaned fact, consistent with reporting).
- Use `full` + `--exclude-flagged` to experiment with or without outlier impact.
- Use `fact` when you want baskets after removal but before receipt-level aggregation nuance changes.

**Grain Reference:**
| File | Grain |
| ---- | ----- |
| `fact_transaction_full.csv` | Line item (pre-removal) |
| `fact_transaction_dimension.csv` | Line item (post-removal) |
| `transaction_records.csv` | One row per receipt (basket) |

---

## 3. Forecasting & Prescriptive Analytics (`models/`)

- **Descriptive Analytics (`descriptive.py`):**  
  Visualizes sales trends (daily, monthly, quarterly, annual), top products by revenue/quantity, category breakdowns.

- **Holt-Winters Forecasting (`holtwinters.py`):**
  - Loads bundle pairs from association rules
  - Analyzes demand at different price points
  - Forecasts bundle sales per quarter using Holt-Winters
  - Estimates price elasticity of demand (PED) via regression
  - Simulates impact of new bundle pricing on demand and revenue
  - Plots historical vs. forecasted sales and revenue impact

---

## 🐳 Docker Architecture

```
┌─────────────┐
│  Frontend   │ :80 (React + Nginx)
│  (Browser)  │
└──────┬──────┘
       │
┌──────▼──────────────────────────┐
│     Backend API :8000           │
│     (FastAPI + Python)          │
└─┬────┬────┬────────────────┬────┘
  │    │    │                │
  │    │    │                │
┌─▼────▼────▼─┐  ┌───────┐  │
│ PostgreSQL  │  │ MinIO │  │
│   :5432     │  │ :9000 │  │
└─────────────┘  └───────┘  │
       │                     │
┌──────▼─────────┐   ┌──────▼──────┐
│   Keycloak     │   │  Observer   │
│     :8080      │   │  (Watchdog) │
└────────────────┘   └─────────────┘
```

**Service Order (enforced by health checks):**
1. postgres → 2. minio + keycloak → 3. backend-api → 4. observer + frontend

---

## 🎨 Frontend Architecture

### Technology Stack
- **Framework:** React 19 + TypeScript
- **Build Tool:** Vite 7
- **Authentication:** Keycloak.js 26.2
- **HTTP Client:** Axios
- **Routing:** React Router DOM
- **Styling:** CSS Modules
- **Production Server:** Nginx (Alpine)

### Key Components

#### 1. Authentication (`keycloak.ts`)
- PKCE-enabled OIDC authentication
- Token refresh mechanism (5-minute threshold)
- Login/logout flows
- JWT token management

#### 2. Dashboard (`Dashboard.tsx`)
- Power BI report embedding
- Responsive iframe integration
- Environment-based configuration

#### 3. Data Upload (`DataUpload.tsx`)
- Dual file categories (Sales Transactions + Sales by Product)
- Drag-and-drop interface
- File validation (CSV, XLSX only)
- JWT-authenticated upload to backend
- Real-time upload progress tracking

#### 4. Navigation (`Navigation.tsx`)
- Page routing
- Authenticated logout
- User session management

### Nginx Configuration
- **SPA Routing:** All paths route to `index.html`
- **API Proxy:** `/upload` → `backend-api:8000`
- **Compression:** Gzip enabled for text/JS/CSS
- **Caching:** Static assets cached for 1 year
- **Security Headers:** XSS protection, frame options, content-type sniffing prevention

### Environment Variables
| Variable | Purpose | Default |
|----------|---------|---------|
| `VITE_API_BASE_URL` | Backend API endpoint | `http://localhost:8000` |
| `VITE_KEYCLOAK_URL` | Keycloak server | `http://localhost:8080` |
| `VITE_KEYCLOAK_REALM` | Keycloak realm | `booklatte` |
| `VITE_KEYCLOAK_CLIENT_ID` | Client ID | `frontend` |
| `VITE_POWER_BI_EMBED_URL` | Power BI report URL | (optional) |

---

## ⚙️ Backend Architecture

### Technology Stack
- **Framework:** FastAPI
- **Runtime:** Python 3.11 (slim)
- **Authentication:** JWT (RS256 via Keycloak)
- **Object Storage:** MinIO Python SDK
- **Database:** SQLAlchemy + psycopg2
- **File Watcher:** Watchdog
- **Analytics:** pandas, numpy, scikit-learn, statsmodels, mlxtend

### Service Components

#### 1. Backend API Service (`run_api.py`)
**Purpose:** Serves the REST API

**Key Features:**
- JWT-protected file upload endpoint (`POST /upload/`)
- CORS middleware (configurable origins)
- Health check endpoint (`GET /`)
- Validates file types (CSV, XLSX)
- Routes files to correct MinIO folders based on filename patterns
- Creates trigger file for observer

**Dependencies:**
```
FastAPI, Uvicorn, python-jose, requests
```

#### 2. Observer Service (`run_observer.py`)
**Purpose:** Monitors file system for processing triggers

**Key Features:**
- Watches `trigger/` directory for `complete` file
- Automatically executes full pipeline on trigger detection
- Graceful error handling and cleanup
- Prevents race conditions via file-based synchronization

**Dependencies:**
```
Watchdog
```

### Core Modules

#### `app/api/upload.py`
- **Endpoint:** `POST /upload/`
- **Authentication:** JWT Bearer token (via `get_current_user`)
- **Workflow:**
  1. Validate JWT token
  2. Validate file types and names
  3. Upload files to MinIO (categorized by filename)
  4. Create `_complete` marker in MinIO
  5. Create local trigger file
  6. Return upload confirmation

#### `app/services/auth.py`
- Fetches Keycloak JWKS (JSON Web Key Set) on startup
- Validates JWT signature using RS256
- Verifies token claims (issuer, audience, expiration)
- Returns decoded user payload

#### `app/services/storage.py`
- MinIO client initialization
- Bucket creation (landing, staging)
- Folder marker creation (`.keep` files)
- Async file upload (thread-offloaded)
- Complete marker creation
- File listing and cleanup utilities

#### `app/observer/handler.py`
- Extends `FileSystemEventHandler`
- Detects `complete` file creation
- Executes `run_all.execute_pipeline()`
- Cleans up trigger file after execution

#### `app/pipeline/run_all.py`
**Pipeline Orchestrator**

Executes in sequence:
1. **ETL** (`etl.py`) - Data extraction, transformation, loading
2. **MBA** (`mba.py`) - Market basket analysis
3. **PED** (`ped.py`) - Price elasticity of demand
4. **NLP** (`nlp.py`) - Non-linear programming optimization
5. **Holt-Winters** (`holtwinters.py`) - Time series forecasting

Logs execution time per step and handles failures gracefully.

### Configuration (`app/core/config.py`)

Centralized settings loaded from environment variables:

| Category | Variables |
|----------|-----------|
| **API** | `API_HOST`, `API_PORT` |
| **CORS** | `CORS_ALLOW_ORIGINS` (comma-separated) |
| **Database** | `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` |
| **MinIO** | `MINIO_ENDPOINT`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `MINIO_SECURE` |
| **Keycloak** | `KEYCLOAK_ISSUER`, `KEYCLOAK_CLIENT_ID` |
| **Trigger** | `TRIGGER_DIR` (default: `/app/trigger`) |

### Python Dependencies
```
fastapi, uvicorn, anyio             # Web framework
minio, psycopg2-binary, sqlalchemy  # Storage & DB
python-jose, requests               # Authentication
pandas, numpy, scipy                # Data processing
scikit-learn, mlxtend, statsmodels  # Analytics
watchdog                            # File monitoring
```

---

## 🔄 Data Flow

### Upload & Processing Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User Authentication                                          │
│    Frontend → Keycloak → JWT Token → Stored in Browser         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. File Upload                                                  │
│    User selects files → Frontend validates → Sends to Backend  │
│    (JWT token included in Authorization header)                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. Backend Processing                                           │
│    • Validates JWT token                                        │
│    • Validates file types (CSV, XLSX)                          │
│    • Categorizes files by name pattern                         │
│    • Uploads to MinIO (landing bucket)                         │
│    • Creates '_complete' marker                                │
│    • Creates trigger file in /app/trigger/                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. Observer Detection                                           │
│    Watchdog detects 'complete' file → Triggers pipeline        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. Pipeline Execution                                           │
│    run_all.py orchestrates:                                     │
│    ① ETL: Extract from MinIO → Transform → Load to PostgreSQL │
│    ② MBA: Market basket analysis → association rules           │
│    ③ PED: Calculate price elasticity                           │
│    ④ NLP: Optimize pricing strategies                          │
│    ⑤ Holt-Winters: Generate forecasts                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. Results Storage                                              │
│    • PostgreSQL: Fact tables, dimensions, analytics results    │
│    • MinIO (staging): Processed CSVs, reports                  │
│    • Observer cleans up trigger file                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. Visualization                                                │
│    Frontend Dashboard → Power BI Embed → Interactive reports   │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **File-based trigger** | Prevents race conditions; observer and API are decoupled |
| **JWT authentication** | Stateless, secure; integrates with enterprise SSO (Keycloak) |
| **MinIO object storage** | S3-compatible, containerized, handles large file uploads |
| **Two-service backend** | API (stateless) + Observer (stateful) for clean separation |
| **Multi-stage Docker build** | Optimized frontend image size (Node build → Nginx serve) |
| **Health checks** | Ensures services start in correct order, prevents startup failures |

---

## 🔒 Security Features

### Authentication & Authorization
- **OIDC/OAuth 2.0:** Industry-standard authentication via Keycloak
- **JWT Tokens:** RS256 signature verification with JWKS
- **PKCE Flow:** Enhanced security for public clients (frontend)
- **Token Refresh:** Automatic refresh before expiration (5-min threshold)
- **Protected Endpoints:** All `/upload` endpoints require valid JWT

### Network Security
- **CORS Policy:** Configurable allowed origins (no wildcard in production)
- **Security Headers:**
  - `X-Frame-Options: SAMEORIGIN` (prevents clickjacking)
  - `X-Content-Type-Options: nosniff` (prevents MIME sniffing)
  - `X-XSS-Protection: 1; mode=block` (XSS protection)
- **Docker Network Isolation:** Services communicate via internal network
- **Port Exposure:** Only necessary ports exposed to host

### Data Security
- **File Validation:** Strict file type checking (CSV, XLSX only)
- **Filename Pattern Matching:** Routes files to correct storage locations
- **User Context:** All uploads logged with user email from JWT
- **Async I/O:** Thread-safe file operations prevent race conditions

### Container Security
- **Minimal Base Images:** Alpine Linux, slim Python
- **Non-root Execution:** Services run with least privilege (where applicable)
- **No Secrets in Images:** Environment variable injection via Docker Compose
- **Health Checks:** Detect and restart unhealthy containers

### Development vs Production
| Aspect | Development | Production Recommendation |
|--------|------------|---------------------------|
| **HTTPS** | HTTP (localhost) | HTTPS with valid certificates |
| **CORS** | Multiple origins | Single domain or CDN |
| **Keycloak** | HTTP | HTTPS only |
| **Passwords** | Default values | Strong, unique passwords |
| **Token Expiry** | 5 minutes | Configurable based on security policy |

---

## 📊 Using the Platform

### Via Web Interface (Recommended)
1. Open http://localhost:80
2. Login with Keycloak credentials
3. Upload Excel files through the UI
4. Files are automatically processed by the pipeline
5. View results in dashboard

### Direct Pipeline Execution (Development)
1. Place raw Excel files in `raw_sales/` and `raw_sales_by_product/`
2. Run ETL:
   ```bash
   python etl.py
   ```
3. Run Market Basket Analysis:
   ```bash
   python mba.py
   # Or with options:
   python mba.py --source full --exclude-flagged --min-support 0.002
   ```
4. Run forecasting:
   ```bash
   python models/descriptive.py
   python models/holtwinters.py
   ```

---

## 🔧 Development

### Local Development (without Docker)
Requires: Python 3.10+, Node 18+, PostgreSQL, MinIO, Keycloak running

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Docker Development
```bash
# Rebuild specific service
docker-compose build --no-cache backend-api
docker-compose up -d backend-api

# View logs
docker-compose logs -f backend-api

# Access container
docker exec -it backend_api bash
```

---

## 📝 Notes

- All outputs are regenerated on each run; ensure raw files are up-to-date.
- For bundle pricing analysis, edit the bundle selection and price in `models/holtwinters.py`.
- Docker volumes persist data across restarts. Use `docker-compose down -v` to reset.

---

## 🔗 Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:80 | Web application |
| Backend API | http://localhost:8000 | REST API |
| Keycloak | http://localhost:8080 | Authentication |
| MinIO Console | http://localhost:9001 | Object storage |
| PostgreSQL | localhost:5432 | Database |

---

## 📚 Documentation

- [SETUP.md](SETUP.md) - Complete setup guide
- `backend/README.md` - Backend API documentation
- `frontend/README.md` - Frontend documentation

---

## 🤝 Contributing

1. Create feature branch from `features/connection`
2. Make changes
3. Test with Docker Compose
4. Submit pull request

---
