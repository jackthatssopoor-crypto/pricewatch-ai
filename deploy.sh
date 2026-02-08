#!/bin/bash

# PriceWatch AI - Automated Deployment Script
# This script automates the deployment process to GitHub and Railway

set -e  # Exit on any error

echo "🚀 PriceWatch AI - Deployment Automation"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    print_error "GitHub CLI (gh) is not installed"
    echo "Install it with: sudo apt-get install gh"
    exit 1
fi

print_success "GitHub CLI is installed"

# Check if authenticated with GitHub
if ! gh auth status &> /dev/null; then
    print_warning "Not authenticated with GitHub"
    echo ""
    echo "Please run: gh auth login"
    echo "Then run this script again"
    exit 1
fi

print_success "Authenticated with GitHub"

# Check if git repo is initialized
if [ ! -d .git ]; then
    print_status "Initializing git repository..."
    git init
    git config user.email "molt@pricewatch.ai"
    git config user.name "Molt Bot"
    print_success "Git repository initialized"
fi

# Check if there are uncommitted changes
if [[ -n $(git status -s) ]]; then
    print_status "Uncommitted changes found. Committing..."
    git add -A
    git commit -m "Update: Latest changes before deployment

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
    print_success "Changes committed"
fi

# Ask for repository name
echo ""
print_status "Repository Configuration"
read -p "Repository name [pricewatch-ai]: " REPO_NAME
REPO_NAME=${REPO_NAME:-pricewatch-ai}

read -p "Make repository private? (y/N): " MAKE_PRIVATE
if [[ $MAKE_PRIVATE =~ ^[Yy]$ ]]; then
    VISIBILITY="--private"
else
    VISIBILITY="--public"
fi

# Check if remote origin already exists
if git remote get-url origin &> /dev/null; then
    print_warning "Remote 'origin' already exists"
    read -p "Do you want to push to existing remote? (Y/n): " PUSH_EXISTING
    if [[ ! $PUSH_EXISTING =~ ^[Nn]$ ]]; then
        print_status "Pushing to existing remote..."
        git push -u origin master || git push -u origin main
        print_success "Code pushed to GitHub"
        GITHUB_URL=$(git remote get-url origin)
        echo ""
        echo "📦 GitHub Repository: $GITHUB_URL"
    fi
else
    # Create new GitHub repository
    print_status "Creating GitHub repository: $REPO_NAME"
    gh repo create "$REPO_NAME" $VISIBILITY --source=. --remote=origin --push
    print_success "Repository created and code pushed"

    GITHUB_URL="https://github.com/$(gh api user --jq .login)/$REPO_NAME"
    echo ""
    echo "📦 GitHub Repository: $GITHUB_URL"
fi

echo ""
echo "=========================================="
echo "✅ GitHub Deployment Complete!"
echo "=========================================="
echo ""

# Railway deployment
echo "🚂 Railway Deployment"
echo "====================="
echo ""

if ! command -v railway &> /dev/null; then
    print_warning "Railway CLI is not installed"
    echo ""
    echo "Install it with: npm install -g @railway/cli"
    echo ""
    read -p "Do you want to install Railway CLI now? (Y/n): " INSTALL_RAILWAY

    if [[ ! $INSTALL_RAILWAY =~ ^[Nn]$ ]]; then
        print_status "Installing Railway CLI..."
        sudo npm install -g @railway/cli
        print_success "Railway CLI installed"
    else
        print_warning "Skipping Railway deployment"
        echo ""
        echo "📖 Manual Railway deployment instructions:"
        echo "1. Install Railway CLI: npm install -g @railway/cli"
        echo "2. Login: railway login"
        echo "3. Initialize: railway init"
        echo "4. Deploy: railway up"
        echo "5. Add database: railway add --database postgres"
        echo "6. Add Redis: railway add --database redis"
        echo ""
        echo "Or deploy via web: https://railway.app"
        exit 0
    fi
fi

# Check if authenticated with Railway
if ! railway whoami &> /dev/null; then
    print_warning "Not authenticated with Railway"
    echo ""
    print_status "Logging in to Railway..."
    railway login
fi

print_success "Authenticated with Railway"

# Check if Railway project exists
if [ ! -f railway.json ] || ! railway status &> /dev/null; then
    print_status "Initializing Railway project..."
    railway init
    print_success "Railway project initialized"
fi

# Deploy to Railway
print_status "Deploying to Railway..."
railway up

print_success "Deployment triggered"

# Add PostgreSQL
print_status "Adding PostgreSQL database..."
railway add --database postgres || print_warning "PostgreSQL might already exist"

# Add Redis
print_status "Adding Redis..."
railway add --database redis || print_warning "Redis might already exist"

# Generate secret key
SECRET_KEY=$(openssl rand -hex 32)

print_status "Setting environment variables..."
railway variables set SECRET_KEY="$SECRET_KEY"

echo ""
print_warning "⚠️  IMPORTANT: Set these variables manually:"
echo ""
echo "railway variables set STRIPE_SECRET_KEY=sk_test_YOUR_KEY"
echo "railway variables set SENDGRID_API_KEY=SG.YOUR_KEY"
echo "railway variables set SENDGRID_FROM_EMAIL=noreply@yourdomain.com"
echo ""

# Get deployment URL
print_status "Getting deployment URL..."
RAILWAY_URL=$(railway domain 2>/dev/null || echo "Not available yet")

echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "📦 GitHub: $GITHUB_URL"
echo "🚂 Railway: $RAILWAY_URL"
echo ""
echo "📋 Next Steps:"
echo "1. Set Stripe and SendGrid API keys (see above)"
echo "2. Wait for deployment to complete (~2-3 minutes)"
echo "3. Visit your Railway app URL to test"
echo "4. Check logs: railway logs"
echo ""
echo "📖 Full instructions: DEPLOYMENT_INSTRUCTIONS.md"
echo ""
echo "🎉 Ready to launch!"
