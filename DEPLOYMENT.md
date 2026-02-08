# 🚀 PriceWatch AI - Deployment Guide

## Deployment Options

### Option 1: Railway.app (Recommended for MVP)

**Pros:**
- Zero-config PostgreSQL and Redis
- Automatic deployments from Git
- Built-in monitoring
- $5/month free credit
- Scales automatically

**Steps:**

1. **Create Railway Account**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli

   # Login
   railway login
   ```

2. **Create New Project**
   ```bash
   cd /data/molt/pricewatch-ai
   railway init
   railway up
   ```

3. **Add Services**
   - PostgreSQL: `railway add postgresql`
   - Redis: `railway add redis`

4. **Set Environment Variables**
   ```bash
   railway variables set SENDGRID_API_KEY=your_key
   railway variables set STRIPE_SECRET_KEY=your_key
   railway variables set FROM_EMAIL=alerts@pricewatch-ai.com
   ```

5. **Deploy**
   ```bash
   git init
   git add .
   git commit -m "Initial deployment"
   railway up
   ```

**Cost:** ~$20-50/month initially

---

### Option 2: Fly.io

**Pros:**
- More control over infrastructure
- Better for global deployment
- Generous free tier

**Steps:**

1. **Install Fly CLI**
   ```bash
   curl -L https://fly.io/install.sh | sh
   fly auth login
   ```

2. **Create fly.toml**
   ```bash
   fly launch
   ```

3. **Set Secrets**
   ```bash
   fly secrets set SENDGRID_API_KEY=your_key
   fly secrets set STRIPE_SECRET_KEY=your_key
   ```

4. **Deploy**
   ```bash
   fly deploy
   ```

**Cost:** ~$15-30/month initially

---

### Option 3: DigitalOcean App Platform

**Pros:**
- Simple UI
- Managed databases
- Predictable pricing

**Steps:**

1. Push code to GitHub
2. Connect GitHub repo to DigitalOcean App Platform
3. Add PostgreSQL and Redis databases
4. Set environment variables in dashboard
5. Deploy

**Cost:** ~$25-50/month

---

### Option 4: Self-Hosted (Docker Compose)

**For complete control and lowest cost**

```bash
# On your VPS (Ubuntu 22.04)
cd /data/molt/pricewatch-ai

# Create .env file
cat > .env <<EOF
POSTGRES_PASSWORD=your_secure_password
SENDGRID_API_KEY=your_key
STRIPE_SECRET_KEY=your_key
FROM_EMAIL=alerts@pricewatch-ai.com
EOF

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f api
```

**Requirements:**
- VPS with 2GB RAM minimum
- Ubuntu 22.04 or similar
- Docker and Docker Compose installed

**Cost:** ~$5-10/month (VPS only)

---

## Environment Variables

Required:
```
DATABASE_URL=postgresql://user:password@host:5432/dbname
REDIS_URL=redis://host:6379/0
SENDGRID_API_KEY=SG.xxx
STRIPE_SECRET_KEY=sk_live_xxx
FROM_EMAIL=alerts@pricewatch-ai.com
```

Optional:
```
SENTRY_DSN=https://xxx@sentry.io/xxx
PROXY_URL=http://proxy-provider.com:port
DEBUG=false
```

---

## Database Setup

### Initial Migration

```bash
# Install Alembic
pip install alembic

# Create migrations
cd backend
alembic init migrations
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

### Backup Strategy

**Automated Daily Backups:**
```bash
# Add to crontab
0 2 * * * pg_dump $DATABASE_URL | gzip > /backups/pricewatch_$(date +\%Y\%m\%d).sql.gz
```

---

## Monitoring & Alerts

### 1. Uptime Monitoring (UptimeRobot)

Create free account at uptimerobot.com

Add monitors:
- https://api.pricewatch-ai.com/health (every 5 minutes)
- Alert via email if down > 5 minutes

### 2. Error Tracking (Sentry)

```bash
# Install Sentry SDK
pip install sentry-sdk

# Add to main.py
import sentry_sdk
sentry_sdk.init(dsn="your_sentry_dsn")
```

### 3. Log Aggregation

**Option A: Papertrail (Free tier: 50MB/month)**
```bash
# Add to Railway/Fly logs
railway logs --follow | papertrail
```

**Option B: Self-hosted Loki + Grafana**
- More complex but free
- Better for high-volume logs

---

## Scaling Strategy

### Phase 1: Single Server (0-100 users)
- **Infrastructure:** Railway basic plan
- **Database:** PostgreSQL 1GB
- **Redis:** 256MB
- **Cost:** ~$20-30/month
- **Handles:** 100 users, 5,000 products tracked

### Phase 2: Horizontal Scaling (100-500 users)
- **Infrastructure:** Multiple Celery workers
- **Database:** PostgreSQL 2GB with read replicas
- **Redis:** 512MB
- **CDN:** Cloudflare for static assets
- **Cost:** ~$100-150/month
- **Handles:** 500 users, 25,000 products tracked

### Phase 3: Multi-Region (500-2000 users)
- **Infrastructure:** Multi-region deployment (Fly.io)
- **Database:** PostgreSQL 4GB with failover
- **Redis:** Cluster mode
- **Scraping:** Dedicated proxy pool
- **Cost:** ~$500-800/month
- **Handles:** 2,000 users, 100,000 products tracked

---

## Security Checklist

Before going live:

- [ ] Set strong database passwords
- [ ] Enable HTTPS only (no HTTP)
- [ ] Add rate limiting (10 req/sec per IP)
- [ ] Enable CORS restrictions
- [ ] Set up API key rotation policy
- [ ] Configure Stripe webhook signatures
- [ ] Add input validation on all endpoints
- [ ] Enable database SSL connections
- [ ] Set up firewall rules
- [ ] Configure CSP headers
- [ ] Add login attempt throttling
- [ ] Enable audit logging
- [ ] Set up automated security scanning

---

## Performance Optimization

### Database Indexing
```sql
CREATE INDEX idx_products_user_id ON products(user_id);
CREATE INDEX idx_price_history_product_id ON price_history(product_id);
CREATE INDEX idx_price_history_timestamp ON price_history(timestamp);
CREATE INDEX idx_alerts_user_id ON alerts(user_id);
```

### Caching Strategy
- Cache user sessions in Redis (30 min TTL)
- Cache product data (5 min TTL)
- Cache dashboard stats (1 min TTL)
- Cache API responses for read-heavy endpoints

### Scraping Optimization
- Batch scraping requests (10 at a time)
- Implement exponential backoff on failures
- Use rotating proxies for high volume
- Cache DNS lookups
- Reuse browser contexts

---

## Disaster Recovery

### Backup Plan

**What to backup:**
1. PostgreSQL database (daily)
2. Environment variables (stored securely)
3. Application code (Git)

**Recovery Time Objective (RTO):** 1 hour
**Recovery Point Objective (RPO):** 24 hours

### Disaster Scenarios

**1. Database Corruption**
```bash
# Restore from latest backup
gunzip < /backups/latest.sql.gz | psql $DATABASE_URL
```

**2. Complete Server Failure**
- Spin up new Railway/Fly project
- Restore database from backup
- Deploy latest code from Git
- Update DNS records
- Test all systems

**3. Data Breach**
- Immediately rotate all API keys
- Force password resets for all users
- Notify affected users within 72 hours
- Conduct security audit
- Implement additional security measures

---

## Launch Checklist

### Pre-Launch (Day -7)
- [ ] Deploy to production
- [ ] Test all user flows end-to-end
- [ ] Set up monitoring and alerts
- [ ] Configure backups
- [ ] Load test (simulate 100 concurrent users)
- [ ] Security audit
- [ ] Legal documents (ToS, Privacy Policy)

### Launch Day (Day 0)
- [ ] Post on Product Hunt
- [ ] Post on Hacker News
- [ ] Reddit outreach (r/ecommerce, r/shopify)
- [ ] Send launch email to beta users
- [ ] Monitor error rates closely
- [ ] Be ready to handle support requests

### Post-Launch (Day +1 to +7)
- [ ] Daily check of error logs
- [ ] Monitor signup conversion rates
- [ ] Track user activation (products added)
- [ ] Respond to all feedback
- [ ] Fix critical bugs immediately
- [ ] Weekly user survey

---

## Cost Breakdown (Monthly)

### Startup Phase (Month 1-3)
| Item | Cost |
|------|------|
| Railway/Fly hosting | $20-30 |
| PostgreSQL managed | $0-15 |
| Redis managed | $0-10 |
| SendGrid (email) | $0 (free tier) |
| Scraping proxies | $0-50 |
| Domain name | $1 |
| SSL certificate | $0 (Let's Encrypt) |
| Monitoring tools | $0 (free tiers) |
| **Total** | **$21-106** |

### Growth Phase (Month 6-12)
| Item | Cost |
|------|------|
| Infrastructure | $100-200 |
| Database | $50-100 |
| Proxies | $200-500 |
| Email | $50-100 |
| CDN | $20-50 |
| Monitoring | $50-100 |
| **Total** | **$470-1,050** |

**Break-even:** 2-3 paying customers

---

## Support & Maintenance

### Weekly Tasks
- Review error logs
- Check scraping success rates
- Monitor churn metrics
- Review customer feedback
- Update competitor list

### Monthly Tasks
- Database optimization
- Security patches
- Performance review
- Cost optimization
- Feature prioritization

### Quarterly Tasks
- Infrastructure audit
- Security audit
- Pricing review
- Market analysis
- Strategic planning

---

## Next Steps

1. **Choose deployment platform** (Railway recommended for MVP)
2. **Set up Stripe account** and get API keys
3. **Configure SendGrid** and verify domain
4. **Deploy to production**
5. **Test end-to-end flow**
6. **Begin beta testing**

---

**Ready to deploy? Let's go! 🚀**
