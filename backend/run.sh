#!/bin/bash
set -e

ENV_FILE="$(cd "$(dirname "$0")" && pwd)/.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "Creating .env..."
  read -r -p "Google Flash API key (leave blank to skip for now): " GOOGLE_FLASH_API_KEY

  JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
  SESSION_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

  cat > "$ENV_FILE" <<EOL
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/health_app
GOOGLE_FLASH_API_KEY=$GOOGLE_FLASH_API_KEY
JWT_SECRET=$JWT_SECRET
SESSION_SECRET=$SESSION_SECRET
JWT_EXP_MINUTES=30
REFRESH_EXP_DAYS=30
ADMIN_USERNAME=admin
EOL

  echo ".env created at $ENV_FILE"
fi

set -a
source "$ENV_FILE"
set +a

cd "$(dirname "$0")"
exec uvicorn app.main:app --reload
