# Health API

## Setup
1. Create a Postgres database named `health_app`.
2. Set `DATABASE_URL` if you need custom credentials:
   - Example: `postgresql+psycopg2://user:pass@localhost:5432/health_app`
3. Set Google Flash credentials:
   - `GOOGLE_FLASH_API_KEY="your_key_here"`
   - Optional: `GOOGLE_FLASH_BASE_URL="https://your.flash.endpoint"`
3. Install dependencies:
   - `pip install -r requirements.txt`
4. Run the server:
   - `uvicorn app.main:app --reload`

## Endpoints
- `POST /health-data`
- `GET /health-summary/{user_id}`
- `GET /health-insights/{user_id}`
- `POST /health-insights`
