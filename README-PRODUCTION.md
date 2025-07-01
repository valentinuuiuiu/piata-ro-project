# Piața.ro - Production Deployment Guide

## 🚀 Quick Start

### Local Development with Docker
```bash
# Clone and setup
git clone <repository>
cd piata-ro-project

# Deploy with one command
./deploy.sh
```

### Azure Deployment

#### Option 1: Azure Container Instances (Recommended for MVP)
```bash
# Build and push image
docker build -t piata-ro .
docker tag piata-ro your-registry.azurecr.io/piata-ro:latest
docker push your-registry.azurecr.io/piata-ro:latest

# Deploy to Azure
az container create --resource-group piata-ro-rg --file azure-deploy.yml
```

#### Option 2: Azure App Service
```bash
# Create App Service
az webapp create --resource-group piata-ro-rg --plan piata-ro-plan --name piata-ro --deployment-container-image-name piata-ro:latest
```

## 🏗️ Architecture

### Services
- **Web App**: Django application (Port 8000)
- **MCP Agents**: AI agents for admin (Ports 8001-8003)
- **Database**: PostgreSQL
- **Cache**: Redis
- **Storage**: Azure Blob Storage (production)

### Key Features
- ✅ DeepSeek AI Integration (User & Admin chat)
- ✅ OpenStreetMap Location Services
- ✅ Real-time MCP Agents
- ✅ Stripe Payment Integration
- ✅ Image Upload & Processing
- ✅ Multi-language Support (Romanian)
- ✅ Production-ready Docker Setup

## 🔧 Configuration

### Environment Variables
```bash
# Core Settings
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0

# AI Services
DEEPSEEK_API_KEY=sk-your-key

# Azure Storage
AZURE_STORAGE_ACCOUNT_NAME=your-account
AZURE_STORAGE_ACCOUNT_KEY=your-key
AZURE_STORAGE_CONTAINER=media

# Payment
STRIPE_PUBLISHABLE_KEY=pk_your-key
STRIPE_SECRET_KEY=sk_your-key
```

## 🧪 Testing

### Run Tests
```bash
./venv/bin/python manage.py test
```

### Load Sample Data
```bash
./venv/bin/python manage.py populate_sample_data
```

## 📊 Monitoring

### Health Checks
- Main app: `http://your-domain/api/health/`
- MCP Agents: `http://your-domain:8001/health`

### Logs
```bash
# Docker logs
docker-compose logs -f web

# Azure logs
az webapp log tail --name piata-ro --resource-group piata-ro-rg
```

## 🔒 Security Checklist

- [x] HTTPS enabled
- [x] CSRF protection
- [x] SQL injection protection
- [x] XSS protection
- [x] Secure headers
- [x] Environment variables for secrets
- [x] User authentication
- [x] Admin panel protection

## 🚀 Performance Optimizations

- [x] Redis caching
- [x] Static file optimization
- [x] Database indexing
- [x] Image compression
- [x] CDN ready (Azure Blob)
- [x] Async API calls

## 📱 Features

### User Features
- User registration/login
- Listing creation with images
- Search and filtering
- Messaging system
- Favorites
- Payment system (credits)
- AI chatbot (Romanian)

### Admin Features
- Django admin panel
- AI assistant with MCP agents
- User management
- Listing moderation
- Analytics
- Payment tracking

## 🛠️ Maintenance

### Database Migrations
```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

### Backup
```bash
# Database backup
docker-compose exec db pg_dump -U piata_user piata_ro > backup.sql

# Media files backup (if using local storage)
tar -czf media-backup.tar.gz media/
```

### Updates
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose build
docker-compose up -d
```

## 🆘 Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check DATABASE_URL
   - Ensure PostgreSQL is running
   - Verify credentials

2. **Static Files Not Loading**
   - Run `collectstatic`
   - Check STATIC_ROOT settings
   - Verify Azure storage config

3. **AI Chat Not Working**
   - Check DEEPSEEK_API_KEY
   - Verify API quota
   - Check network connectivity

4. **Images Not Displaying**
   - Check media file permissions
   - Verify MEDIA_URL settings
   - Check Azure storage configuration

### Support
- Check logs: `docker-compose logs`
- Database shell: `docker-compose exec web python manage.py shell`
- Admin panel: `http://your-domain/admin`

## 📈 Scaling

### Horizontal Scaling
- Use Azure Container Instances with load balancer
- Separate database server
- Redis cluster
- CDN for static files

### Vertical Scaling
- Increase container resources
- Optimize database queries
- Add caching layers
- Use async processing

## 🎯 Production Checklist

- [ ] Domain configured
- [ ] SSL certificate installed
- [ ] Database optimized
- [ ] Monitoring setup
- [ ] Backup strategy
- [ ] Error tracking (Sentry)
- [ ] Performance monitoring
- [ ] Security audit
- [ ] Load testing
- [ ] Documentation updated