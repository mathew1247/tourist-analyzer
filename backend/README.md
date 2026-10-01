# Tourism Footfall and Revenue Analytics - Backend

A company/admin-facing REST API backend for the **Tourism Footfall and Revenue Analytics** web platform, built with Python, Flask, and MySQL.

---

## 1. Project Overview

The backend manages verified monthly tourism data, performs statistical aggregation (visitor volumes, gross revenue, category contributions, destination flows), calculates growth trends, provides simple moving-average and seasonal projections, and generates performance audit reports.

---

## 2. Technology Stack

- **Python 3.10+**
- **Flask 3.x** - REST API framework
- **Flask-CORS** - Cross-Origin Resource Sharing
- **mysql-connector-python** - Official MySQL driver
- **python-dotenv** - Environment variable management
- **Werkzeug** - Secure password hashing (`scrypt`)

---

## 3. Directory Structure

```
backend/
├── app.py                      # Flask app factory, blueprint registration & error handlers
├── config.py                   # Central configuration module loading .env
├── firebase_config.py          # Firebase Admin SDK & Firestore client initialization
├── requirements.txt            # Python dependencies (includes firebase-admin)
├── .env                        # Local database & server secrets (excluded from git)
├── .env.example                # Example template for environment variables
├── README.md                   # Complete backend documentation & setup guide
├── serviceAccountKey.json      # Firebase private key (strictly excluded by .gitignore)
│
├── database/
│   ├── db.py                   # Reusable get_db_connection() with MySQL & local fallback
│   ├── schema.sql              # MySQL DDL schema and initial seed data
│   └── tourism_analytics.db    # Auto-initialized local database for instant development
│
├── routes/
│   ├── auth.py                 # POST /api/login, /api/logout
│   ├── tourism.py              # CRUD: /api/tourism (POST, GET, PUT, DELETE)
│   ├── tourists.py             # Firestore: GET /api/tourists, POST /api/tourists, GET /api/tourists/<id>
│   ├── dashboard.py            # GET /api/dashboard (summary, trends, recent records)
│   ├── analytics.py            # GET /api/analytics (YoY growth, KPIs, factual insights)
│   ├── prediction.py           # GET /api/prediction (1, 3, 6-month seasonal forecasts)
│   ├── reports.py              # GET /api/reports (monthly, yearly, revenue, visitor)
│   └── profile.py              # GET /api/profile, PUT /api/profile
│
├── services/
│   ├── analytics_service.py    # Statistical computations, peak/low analysis, insights
│   ├── prediction_service.py   # Historical moving average and linear trend model
│   └── report_service.py       # Period auditor & executive summary generator
│
└── utils/
    └── validators.py           # Input validation for month, year, visitors, revenue, email, Firestore tourists
```


---

## 4. Database Setup (MySQL)

### Creating the MySQL Database

1. Ensure MySQL server is running on your machine (default port `3306`).
2. Log into MySQL client:
   ```bash
   mysql -u root -p
   ```
3. Execute the provided schema file:
   ```sql
   SOURCE backend/database/schema.sql;
   ```
   Or run directly from shell:
   ```bash
   mysql -u root -p < backend/database/schema.sql
   ```

### Default Credentials Seeded in Database

| Email | Password | Role | Description |
|---|---|---|---|
| `admin@tourism.com` | `Admin@123` | admin | Default Administrator |
| `admin@xploreelite.com` | `admin123` | admin | XploreElite Quick-Fill Admin |

*Passwords are securely hashed using Werkzeug (`generate_password_hash`).*

---

## 5. Environment Variables (`.env`)

Create or update `backend/.env`:

```ini
# Database Configuration (MySQL)
DB_HOST=localhost
DB_PORT=3306
DB_NAME=tourism_analytics
DB_USER=root
DB_PASSWORD=your_mysql_password

# Flask Application Settings
SECRET_KEY=xploreelite_tourism_analytics_secret_2025
PORT=5000
FLASK_ENV=development
CORS_ORIGIN=*
```

---

## 6. Installation & Execution

### 1. Create and Activate Virtual Environment

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### 3. Start the Flask Backend Server

```bash
python -m backend.app
```

The server will start on: **`http://127.0.0.1:5000`**

---

## 7. REST API Endpoints Reference

### System
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health status check |

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/login` | Authenticate user credentials (`email`, `password`) |
| `POST` | `/api/logout` | Terminate session |

### Tourism Data CRUD
| Method | Endpoint | Query Parameters | Description |
|---|---|---|---|
| `POST` | `/api/tourism` | - | Create new monthly tourism record |
| `GET` | `/api/tourism` | `year`, `month`, `category`, `search` | Fetch filtered records |
| `GET` | `/api/tourism/<id>` | - | Retrieve single record |
| `PUT` | `/api/tourism/<id>` | - | Update existing record |
| `DELETE` | `/api/tourism/<id>` | - | Delete record |

### Analytics & Reports
| Method | Endpoint | Query Parameters | Description |
|---|---|---|---|
| `GET` | `/api/dashboard` | `year` | Executive dashboard stats & charts |
| `GET` | `/api/analytics` | `year`, `month`, `category_id` | 4-chart analytical deep dive & insights |
| `GET` | `/api/prediction` | `period` (`1`, `3`, `6`) | Moving average + trend forecast |
| `GET` | `/api/reports` | `type`, `month`, `year` | Generate official audit report |

### Firebase Firestore Tourism Collection (`tourist_data`)
| Method | Endpoint | Query / Path Parameters | Description |
|---|---|---|---|
| `GET` | `/api/tourists` | - | Fetch all documents from Firestore `tourist_data` collection |
| `POST` | `/api/tourists` | - | Insert new document into Firestore `tourist_data` collection |
| `GET` | `/api/tourists/<doc_id>` | `doc_id` | Fetch specific tourist record by Firestore document ID |
| `DELETE` | `/api/tourists/<doc_id>` | `doc_id` | Delete tourist record from Firestore |

### Profile
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/profile` | Retrieve admin profile and security metadata |
| `PUT` | `/api/profile` | Update admin contact name and email |


---

## 8. Example Requests & Responses

### 1. Add Tourism Data (`POST /api/tourism`)

**Request:**
```http
POST /api/tourism HTTP/1.1
Host: 127.0.0.1:5000
Content-Type: application/json

{
  "month": "April",
  "year": 2025,
  "visitors": 5430,
  "revenue": 890000,
  "category": "Hill Stations"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Tourism data added successfully",
  "data": {
    "id": 25
  }
}
```

---

### 2. Dashboard Summary (`GET /api/dashboard?year=2025`)

**Response (200 OK):**
```json
{
  "success": true,
  "summary": {
    "total_visitors": 48520,
    "total_revenue": 3275000.0,
    "average_visitors": 4038,
    "average_revenue": 273000.0
  },
  "monthly_visitors": [
    {"month": "January", "visitors": 3200},
    {"month": "February", "visitors": 3850}
  ],
  "monthly_revenue": [
    {"month": "January", "revenue": 520000.0},
    {"month": "February", "revenue": 615000.0}
  ],
  "peak_month": {
    "month": "May 2025",
    "visitors": 6120
  },
  "lowest_month": {
    "month": "January 2025",
    "visitors": 3200
  }
}
```

### 3. Firestore Tourist Collection (`GET /api/tourists` & `POST /api/tourists`)

**POST /api/tourists:**
```json
{
  "location": "Ooty",
  "district": "Nilgiris",
  "state": "Tamil Nadu",
  "visit_date": "2026-09-30",
  "visitor_count": 1250,
  "visitor_type": "Domestic",
  "revenue": 450000
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Tourist record added successfully",
  "id": "we8r74BBnfWLaoz1WEKk",
  "data": {
    "id": "we8r74BBnfWLaoz1WEKk",
    "location": "Ooty",
    "district": "Nilgiris",
    "state": "Tamil Nadu",
    "visit_date": "2026-09-30",
    "visitor_count": 1250,
    "visitor_type": "Domestic",
    "revenue": 450000.0
  }
}
```

**GET /api/tourists Response (200 OK):**
```json
[
  {
    "id": "DRcf3pKMghLMt8w40GNL",
    "location": "ooty",
    "district": "Nilgiris",
    "state": "Tamil Nadu",
    "visit_date": "2026-09-30",
    "visitor_count": 1250,
    "visitor_type": "domestic",
    "revenue": 450000
  }
]
```

---

## 9. Frontend Connection

The frontend ([static/js/data.js](file:///c:/Users/mathe/OneDrive/Desktop/tourist-analyzer/static/js/data.js)) automatically directs all REST API queries to:
- `http://127.0.0.1:5000` when running the frontend on a different development server (e.g. port 8000).
- Relative `/api/*` routes when served directly from Flask on port 5000.

`TourismAPI.getTourists()` and `TourismAPI.saveTourist(payload)` provide direct frontend access to the Firestore collections.

CORS headers (`Access-Control-Allow-Origin: *`) are enabled to allow cross-origin requests during local development.

---

## 10. Production & Render Deployment (Firebase Security)

When deploying to Render, Railway, or another cloud provider:
1. **Never commit `serviceAccountKey.json`**: This file is safely excluded in `.gitignore`.
2. **Environment Variable Configuration**:
   - On Render, go to **Environment** > **Add Environment Variable**.
   - Set Key: `FIREBASE_CREDENTIALS_JSON`
   - Set Value: The raw JSON string of your service account key file (or base64 encoded string).
   - Alternatively, use Render's **Secret Files** feature: upload `serviceAccountKey.json` as a secret file and set `FIREBASE_CREDENTIALS_PATH=/etc/secrets/serviceAccountKey.json`.
3. Set `PORT=5000` or use the dynamic port assigned by `$PORT`.

---

## 11. Running the Automated Test Suite

To verify all 13 endpoints, validations, and database/Firestore operations in one command:

```bash
python -m unittest backend.test_api
```

Output:
```
Ran 13 tests in ~2.5s

OK
[PASS] Health check endpoint
[PASS] Auth login success
[PASS] Auth login invalid rejection
[PASS] Auth login missing fields rejection
[PASS] Tourism CREATE
[PASS] Tourism GET ALL
[PASS] Tourism GET ONE
[PASS] Tourism UPDATE
[PASS] Tourism DELETE
[PASS] Tourism 404 verification
[PASS] Input validation error handling
[PASS] Dashboard API
[PASS] Analytics API
[PASS] Prediction API
[PASS] Reports API
[PASS] Profile GET and PUT
[PASS] Firestore GET /api/tourists
[PASS] Firestore POST /api/tourists
[PASS] Firestore GET /api/tourists/<doc_id> verified
```

