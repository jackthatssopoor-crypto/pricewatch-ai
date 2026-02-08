# 🚂 Railway Deployment Guide - PriceWatch AI

## Current Status

Your repository is ready for deployment! The Railway token provided (`db3aac8f-9258-4da5-a82e-9432d36a10fe`) appears to be invalid or expired.

## Quick Deployment Options

### Option 1: Railway Dashboard (Recommended - 5 minutes)

This is the **easiest and fastest** method:

1. **Go to Railway Dashboard**
   - Visit: https://railway.app/new
   - Login with GitHub

2. **Deploy from GitHub**
   - Click "Deploy from GitHub repo"
   - Select: `jackthatssopoor-crypto/pricewatch-ai`
   - Branch: `master`
   - Railway will automatically detect the Dockerfile

3. **Configure Services**
   - Your app will start deploying immediately
   - Add PostgreSQL: Click "New" → "Database" → "PostgreSQL"
   - Add Redis: Click "New" → "Database" → "Redis"

4. **Set Environment Variables**
   - Go to your service → "Variables" tab
   - Add these variables:
     ```
     PORT=8000
     SENDGRID_API_KEY=your_sendgrid_key_here
     FROM_EMAIL=alerts@pricewatch-ai.com
     STRIPE_SECRET_KEY=your_stripe_key_here
     ```
   - Railway automatically provides:
     - `DATABASE_URL` (when you add PostgreSQL)
     - `REDIS_URL` (when you add Redis)

5. **Deploy**
   - Click "Deploy" or push to GitHub
   - Monitor logs in the "Deployments" tab

**That's it!** Your app will be live at `https://[your-service].railway.app`

---

### Option 2: Get a Valid Railway Token

If you want to deploy via CLI or API:

1. **Login to Railway**
   ```bash
   railway login
   ```
   - This will open your browser
   - Authorize the CLI

2. **Get Your Token**
   ```bash
   # View your token
   cat ~/.railway/config.json
   ```

3. **Use the Token**
   ```bash
   export RAILWAY_TOKEN="your-new-token-here"
   railway whoami  # Should show your email
   ```

4. **Deploy**
   ```bash
   cd /data/molt/pricewatch-ai
   railway init  # Link to project
   railway up    # Deploy
   ```

---

### Option 3: GitHub Actions (Automated)

I've already created a GitHub Actions workflow for you at `.github/workflows/railway-deploy.yml`.

**Setup:**

1. Get a valid Railway token (see Option 2)

2. Add it to GitHub Secrets:
   - Go to: https://github.com/jackthatssopoor-crypto/pricewatch-ai/settings/secrets/actions
   - Click "New repository secret"
   - Name: `RAILWAY_TOKEN`
   - Value: Your Railway token
   - Click "Add secret"

3. Push to trigger deployment:
   ```bash
   cd /data/molt/pricewatch-ai
   git add .github/workflows/railway-deploy.yml
   git commit -m "Add Railway deployment workflow"
   git push origin master
   ```

4. Monitor deployment:
   - Go to: https://github.com/jackthatssopoor-crypto/pricewatch-ai/actions
   - Watch the deployment progress

**Auto-Deploy:** Every push to `master` will automatically deploy to Railway!

---

## What's Already Configured

✅ **Dockerfile** - Production-ready with Playwright support
✅ **railway.json** - Railway deployment configuration
✅ **Backend Code** - FastAPI app ready to run
✅ **GitHub Actions** - Automated deployment workflow

## Architecture Overview

```
┌─────────────────────────────────────────┐
│         Railway Platform                │
├─────────────────────────────────────────┤
│                                          │
│  ┌────────────────┐  ┌───────────────┐ │
│  │  PriceWatch    │  │  PostgreSQL   │ │
│  │  API Service   │──│  Database     │ │
│  │  (Dockerfile)  │  └───────────────┘ │
│  └────────────────┘                    │
│         │                               │
│         │           ┌───────────────┐  │
│         └───────────│  Redis Cache  │  │
│                     └───────────────┘  │
│                                         │
└─────────────────────────────────────────┘
         │
         │ HTTPS
         ▼
   Your Users
```

## Environment Variables Required

### Essential (Set these first)
```bash
PORT=8000                          # Auto-set by Railway
DATABASE_URL=postgresql://...      # Auto-set when you add PostgreSQL
REDIS_URL=redis://...              # Auto-set when you add Redis
```

### API Keys (You need to provide)
```bash
SENDGRID_API_KEY=SG.xxxxx         # Get from: https://sendgrid.com/
FROM_EMAIL=alerts@pricewatch-ai.com
STRIPE_SECRET_KEY=sk_live_xxxxx    # Get from: https://stripe.com/
```

### Optional
```bash
SENTRY_DSN=https://...             # Error tracking (optional)
DEBUG=false                        # Set to true for debugging
PROXY_URL=http://...               # For scraping (optional)
```

## Post-Deployment Checklist

After deployment succeeds:

- [ ] **Test Health Endpoint**
  ```bash
  curl https://your-service.railway.app/health
  # Should return: {"status":"ok"}
  ```

- [ ] **Test API**
  ```bash
  curl https://your-service.railway.app/docs
  # Should show FastAPI Swagger docs
  ```

- [ ] **Check Logs**
  - Railway Dashboard → Your Service → "Logs" tab
  - Look for any errors

- [ ] **Configure Domain** (Optional)
  - Railway Dashboard → Your Service → "Settings" → "Domains"
  - Add custom domain: `api.pricewatch-ai.com`

- [ ] **Set up Monitoring**
  - Add UptimeRobot: https://uptimerobot.com
  - Monitor: `https://your-service.railway.app/health`

- [ ] **Enable Auto-Deploy**
  - Railway Dashboard → Your Service → "Settings"
  - Enable "Auto Deploy" from GitHub

## Troubleshooting

### ❌ Build Fails

**Problem:** Docker build fails
**Solution:**
```bash
# Test locally first
cd /data/molt/pricewatch-ai
docker build -t pricewatch-test .
docker run -p 8000:8000 pricewatch-test
```

### ❌ App Crashes on Start

**Problem:** Service starts but crashes immediately
**Solution:**
- Check logs in Railway Dashboard
- Verify all environment variables are set
- Make sure DATABASE_URL and REDIS_URL are available

### ❌ Database Connection Fails

**Problem:** Can't connect to PostgreSQL
**Solution:**
- Make sure you added PostgreSQL service
- Check that DATABASE_URL is set
- Verify the database is running (Railway Dashboard)

### ❌ Playwright Errors

**Problem:** Browser automation fails
**Solution:**
- The Dockerfile includes all Playwright dependencies
- If issues persist, check Railway logs for specific errors
- May need to increase memory allocation

## Cost Estimate

### Starter Plan (First Month)
| Service | Cost |
|---------|------|
| API Service (512MB RAM) | $5 |
| PostgreSQL (1GB) | $5 |
| Redis (256MB) | $3 |
| **Total** | **~$13/month** |

### With Free Trial
- Railway gives $5 free credit/month
- **Actual cost: ~$8/month**

### Scaling (1000+ users)
| Service | Cost |
|---------|------|
| API Service (2GB RAM, 2 replicas) | $40 |
| PostgreSQL (4GB + backups) | $30 |
| Redis (1GB) | $10 |
| **Total** | **~$80/month** |

## Next Steps

1. **Choose your deployment method** (Dashboard recommended)
2. **Deploy the application**
3. **Add database services** (PostgreSQL + Redis)
4. **Set environment variables**
5. **Test the deployment**
6. **Configure custom domain** (optional)
7. **Set up monitoring**

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- PriceWatch AI Repo: https://github.com/jackthatssopoor-crypto/pricewatch-ai

---

**Ready to deploy? Start with Option 1 (Dashboard) - it's the fastest! 🚀**
