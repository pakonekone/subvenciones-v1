# Deployment Guide - Sistema de Subvenciones v1.0

## Architecture Overview

This application uses a split deployment strategy:
- **Frontend (React/Vite)**: Deployed on **Vercel**
- **Backend (FastAPI)**: Deployed on **Railway** or **Render**
- **Database (PostgreSQL)**: Hosted on Railway/Render or external service

---

## Prerequisites

1. GitHub account with this repository pushed
2. Vercel account (https://vercel.com)
3. Railway account (https://railway.app) OR Render account (https://render.com)
4. Environment variables ready (see `.env.example` files)

---

## Part 1: Deploy Backend (Railway - Recommended)

### Step 1: Create Railway Project

1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your `subvenciones-v1` repository
4. Railway will auto-detect it's a Python project

### Step 2: Configure Backend Service

1. In Railway dashboard, click on your service
2. Go to **Settings** → **Service**
3. Set **Root Directory**: `backend`
4. Set **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Step 3: Add PostgreSQL Database

1. In Railway project, click "New" → "Database" → "PostgreSQL"
2. Railway will automatically create a database and set `DATABASE_URL`

### Step 4: Set Environment Variables

Go to **Variables** tab and add:

```bash
# Database (automatically set by Railway if you added PostgreSQL)
DATABASE_URL=postgresql://...

# CORS - Add your Vercel frontend URL once deployed
CORS_ORIGINS=http://localhost:3000,https://your-app.vercel.app

# N8n Integration
N8N_WEBHOOK_URL=your-n8n-webhook-url

# API Configuration
BDNS_MAX_RESULTS=100
MIN_RELEVANCE_SCORE=0.0
LOG_LEVEL=INFO

# Secrets (generate secure values)
SECRET_KEY=your-secret-key-here
```

### Step 5: Deploy

1. Railway will automatically deploy
2. Get your backend URL: `https://your-app.railway.app`
3. Test it: `https://your-app.railway.app/docs` (should show FastAPI docs)

### Step 6: Run Database Migrations

1. In Railway dashboard, click on your backend service
2. Go to **Settings** → click "Terminal"
3. Run:
```bash
cd backend
alembic upgrade head
```

---

## Part 2: Deploy Frontend (Vercel)

### Step 1: Import Project to Vercel

1. Go to https://vercel.com
2. Click "New Project" → "Import Git Repository"
3. Select your `subvenciones-v1` repository

### Step 2: Configure Build Settings

Vercel should auto-detect Vite, but verify:
- **Framework Preset**: Vite
- **Root Directory**: `frontend` (IMPORTANT)
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Install Command**: `npm install`

### Step 3: Set Environment Variables

Add these in Vercel project settings:

```bash
# Backend API URL (from Railway step 5)
VITE_API_URL=https://your-backend.railway.app
```

### Step 4: Deploy

1. Click "Deploy"
2. Vercel will build and deploy your frontend
3. You'll get a URL like: `https://your-app.vercel.app`

### Step 5: Update Backend CORS

Go back to Railway and update `CORS_ORIGINS` to include your Vercel URL:
```bash
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000
```

### Step 6: Update vercel.json

Update the `vercel.json` file in the root to point to your Railway backend:

```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://your-backend.railway.app/api/:path*"
    }
  ]
}
```

Then commit and push - Vercel will auto-redeploy.

---

## Alternative: Deploy Backend on Render

If you prefer Render over Railway:

### Step 1: Create Web Service

1. Go to https://render.com
2. Click "New" → "Web Service"
3. Connect your GitHub repository

### Step 2: Configure Service

- **Name**: subvenciones-backend
- **Root Directory**: `backend`
- **Environment**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Step 3: Add PostgreSQL

1. Click "New" → "PostgreSQL"
2. Copy the **Internal Database URL**
3. Add it to your web service as `DATABASE_URL`

### Step 4: Environment Variables

Same as Railway (see Part 1, Step 4)

### Step 5: Deploy

Render will deploy automatically. Continue with frontend deployment on Vercel.

---

## Post-Deployment Checklist

- [ ] Backend is accessible at `/docs` endpoint
- [ ] Frontend loads without errors
- [ ] Frontend can fetch grants from backend
- [ ] Database migrations have run (`alembic upgrade head`)
- [ ] CORS is properly configured
- [ ] N8n webhook integration is working
- [ ] Test BDNS capture functionality
- [ ] Test BOE capture functionality
- [ ] Test grant export to Google Sheets

---

## Environment Variables Reference

### Backend Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `CORS_ORIGINS` | Allowed frontend origins (comma-separated) | `https://app.vercel.app,http://localhost:3000` |
| `N8N_WEBHOOK_URL` | N8n webhook for grant analysis | `https://n8n.example.com/webhook/...` |
| `SECRET_KEY` | JWT/session secret key | Generate with `openssl rand -hex 32` |
| `BDNS_MAX_RESULTS` | Max results per BDNS capture | `100` |
| `MIN_RELEVANCE_SCORE` | Minimum relevance threshold | `0.0` (disabled) or `0.3` |
| `LOG_LEVEL` | Logging verbosity | `INFO`, `DEBUG`, `WARNING` |

### Frontend Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API base URL | `https://your-backend.railway.app` |

---

## Troubleshooting

### Frontend can't connect to backend
- Check `VITE_API_URL` is set correctly in Vercel
- Verify backend `CORS_ORIGINS` includes your Vercel URL
- Check browser console for CORS errors

### Database connection errors
- Verify `DATABASE_URL` is set correctly
- Ensure database is running and accessible
- Check if migrations have run: `alembic current`

### N8n webhook not receiving data
- Verify `N8N_WEBHOOK_URL` is correct
- Check N8n webhook is active
- Review backend logs for webhook errors

### Build failures
- Check all dependencies are in `requirements.txt` (backend) or `package.json` (frontend)
- Verify Python version compatibility (3.9+)
- Check Node version (18+)

---

## Maintenance

### Update Frontend
1. Push changes to GitHub
2. Vercel auto-deploys from `main` branch

### Update Backend
1. Push changes to GitHub
2. Railway/Render auto-deploys from `main` branch
3. If database schema changed, run migrations in Railway terminal:
   ```bash
   cd backend && alembic upgrade head
   ```

### Monitor Logs
- **Vercel**: Project → Deployments → click deployment → Runtime Logs
- **Railway**: Project → Service → Deployments → View Logs
- **Render**: Dashboard → Web Service → Logs

---

## Security Notes

1. **Never commit** `.env` files to Git
2. Use **strong secret keys** (minimum 32 characters)
3. **Rotate secrets** regularly
4. Enable **SSL/HTTPS** (automatic on Vercel/Railway/Render)
5. Set up **database backups** (automatic on Railway/Render paid plans)
6. Review **CORS origins** - don't use `*` in production

---

## Cost Estimates (as of 2024)

### Free Tier Available
- **Vercel**: Free for hobby projects (includes custom domains)
- **Railway**: $5/month credit (usually enough for small projects)
- **Render**: Free tier available (with limitations)

### Recommended Paid Plans (for production)
- **Vercel Pro**: $20/month (better performance, analytics)
- **Railway**: ~$10-20/month (depending on usage)
- **Render**: ~$7-15/month (starter plan)

**Total estimated cost**: $0 (free tier) to $50/month (production-ready)

---

## Support

For deployment issues:
- Railway: https://railway.app/help
- Render: https://render.com/docs
- Vercel: https://vercel.com/docs

For application issues:
- Check project README.md
- Review CLAUDE.md for architecture details
- Check STATUS.md for known issues
