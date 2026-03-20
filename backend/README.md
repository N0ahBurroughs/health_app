# Health API

## Setup
1. Create a Postgres database named `health_app`.
2. Set `DATABASE_URL` if you need custom credentials:
   - Example: `postgresql+psycopg2://user:pass@localhost:5432/health_app`
3. Set Google Flash credentials:
   - `GOOGLE_FLASH_API_KEY="your_key_here"`
   - Optional: `GOOGLE_FLASH_BASE_URL="https://your.flash.endpoint"`
4. Set a session secret for login cookies:
   - `SESSION_SECRET="replace-this-in-prod"`
5. Set a JWT secret for mobile tokens:
   - `JWT_SECRET="replace-this-in-prod"`
   - Optional: `JWT_EXP_DAYS="7"`
6. Admin username (defaults to `admin`):
   - `ADMIN_USERNAME="admin"`
7. Install dependencies:
   - `pip install -r requirements.txt`
8. Run the server:
   - `uvicorn app.main:app --reload`

## Endpoints
- `POST /health-data`
- `GET /health-summary/{user_id}`
- `GET /health-insights/{user_id}`
- `POST /health-insights`
- `GET /api/health-summary` (auth required)
- `GET /api/health-insights` (auth required)
- `GET /api/health-trends` (auth required)
- `POST /api/health-data` (auth required)
- `POST /api/token` (returns JWT for mobile clients)
