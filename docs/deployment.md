# Deployment Guide

## Local (Docker Compose)

```bash
cp .env.example .env
# fill in .env
docker-compose up --build
```

## Backend → Render

1. Push to GitHub
2. Create a new Web Service on Render, select the repo
3. Set Build Command: `pip install -r requirements.txt`
4. Set Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Root Directory: `backend`
6. Add all environment variables from `.env.example`

## Frontend → Vercel

```bash
cd frontend
vercel deploy
```

Set `NEXT_PUBLIC_API_URL` to your Render backend URL.

## Database → Supabase

1. Create a Supabase project
2. Copy the PostgreSQL connection string
3. Set `DATABASE_URL` in Render environment variables
