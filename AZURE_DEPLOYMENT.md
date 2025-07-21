# Piața RO - Deployment Guide

This guide provides instructions for deploying Piața RO to Azure using Docker containers.

## Prerequisites

- Azure account with active subscription
- Azure CLI installed and configured
- Docker and Docker Compose installed
- Domain name purchased and ready to configure

## Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/piata-ro-project.git
   cd piata-ro-project
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the development environment**
   ```bash
   docker-compose up -d
   ```

4. **Migrate from SQLite to PostgreSQL (if needed)**
   ```bash
   ./migrate_to_postgres.sh
   ```

5. **Access the application**
   - Web: http://localhost:8000
   - Admin: http://localhost:8000/admin

## Azure Deployment

### 1. Create Azure Resources

```bash
# Login to Azure
az login

# Create Resource Group
az group create --name piata-ro-rg --location westeurope

# Create Azure Container Registry
az acr create --resource-group piata-ro-rg --name piataroacr --sku Basic

# Login to ACR
az acr login --name piataroacr

# Create Azure Database for PostgreSQL
az postgres flexible-server create \
  --resource-group piata-ro-rg \
  --name piata-ro-db \
  --location westeurope \
  --admin-user piata_ro \
  --admin-password "YourStrongPassword" \
  --sku-name Standard_B1ms \
  --version 16 \
  --storage-size 32

# Create Azure Cache for Redis
az redis create \
  --resource-group piata-ro-rg \
  --name piata-ro-redis \
  --location westeurope \
  --sku Basic \
  --vm-size C0
```

### 2. Build and Push Docker Images

```bash
# Build images
docker-compose build

# Tag images
docker tag piata-ro-project_web piataroacr.azurecr.io/piata-ro-web:latest

# Push to ACR
docker push piataroacr.azurecr.io/piata-ro-web:latest
```

### 3. Deploy to Azure Container Apps

```bash
# Create Container App Environment
az containerapp env create \
  --name piata-ro-env \
  --resource-group piata-ro-rg \
  --location westeurope

# Create Container App
az containerapp create \
  --name piata-ro-app \
  --resource-group piata-ro-rg \
  --environment piata-ro-env \
  --image piataroacr.azurecr.io/piata-ro-web:latest \
  --target-port 8000 \
  --ingress external \
  --registry-server piataroacr.azurecr.io \
  --env-vars \
    DB_HOST=piata-ro-db.postgres.database.azure.com \
    DB_NAME=piata_ro \
    DB_USER=piata_ro \
    DB_PASSWORD="YourStrongPassword" \
    REDIS_HOST=piata-ro-redis.redis.cache.windows.net \
    REDIS_PASSWORD="YourRedisKey" \
    DEBUG=False \
    ENVIRONMENT=production
```

### 4. Configure Domain and SSL

1. Go to Azure Portal > Container Apps > piata-ro-app > Custom domains
2. Add your domain (e.g., piata.ro)
3. Configure DNS settings with your domain provider
4. Azure will automatically provision an SSL certificate

### 5. Set up CI/CD with GitHub Actions

Create a GitHub workflow file at `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Azure

on:
  push:
    branches: [ main ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
      
    - name: Login to ACR
      uses: docker/login-action@v2
      with:
        registry: piataroacr.azurecr.io
        username: ${{ secrets.ACR_USERNAME }}
        password: ${{ secrets.ACR_PASSWORD }}
        
    - name: Build and push
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: piataroacr.azurecr.io/piata-ro-web:latest
        
    - name: Azure login
      uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}
        
    - name: Deploy to Azure Container Apps
      uses: azure/CLI@v1
      with:
        inlineScript: |
          az containerapp update \
            --name piata-ro-app \
            --resource-group piata-ro-rg \
            --image piataroacr.azurecr.io/piata-ro-web:latest
```

## Monitoring and Maintenance

- **View logs**: 
  ```bash
  az containerapp logs show --name piata-ro-app --resource-group piata-ro-rg
  ```

- **Scale the application**:
  ```bash
  az containerapp update --name piata-ro-app --resource-group piata-ro-rg --min-replicas 2 --max-replicas 10
  ```

- **Database backups**:
  ```bash
  az postgres flexible-server backup list --resource-group piata-ro-rg --server-name piata-ro-db
  ```

## MCP Server Integration

The MCP (Model Context Protocol) server is integrated into the Docker Compose setup and will be automatically deployed. Make sure to set the appropriate environment variables in your Azure deployment:

```bash
az containerapp update \
  --name piata-ro-app \
  --resource-group piata-ro-rg \
  --set-env-vars \
    MCP_SERVER_URL=https://your-mcp-server-url \
    MCP_API_KEY=your-mcp-api-key \
    OPENAI_API_KEY=your-openai-api-key
```

## Troubleshooting

- **Database connection issues**: Check firewall rules and connection strings
- **Container startup failures**: Review container logs for error messages
- **SSL/Domain issues**: Verify DNS configuration and certificate status

For more help, contact the development team at support@piata.ro