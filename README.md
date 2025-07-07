# 🇷🇴 Piața RO - Modern Romanian Marketplace Platform

<div align="center">

![Django](https://img.shields.io/badge/Django-4.2+-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.0-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)

**A comprehensive, feature-rich marketplace platform built for the Romanian market**

[🚀 Live Demo](#) • [📚 Documentation](#documentation) • [🤝 Contributing](#contributing) • [🐛 Report Bug](https://github.com/valentinuuiuiu/piata-ro-project/issues)

</div>

---

## 📋 Table of Contents

- [🎯 Overview](#-overview)
- [✨ Key Features](#-key-features)
- [🤖 AI-Powered Features](#-ai-powered-features)
- [🛠️ Tech Stack](#️-tech-stack)
- [🏗️ Architecture](#️-architecture)
- [🚀 Quick Start](#-quick-start)
- [📱 Usage](#-usage)
- [🔧 Configuration](#-configuration)
- [🤖 MCP Agents](#-mcp-agents)
- [🧪 Testing](#-testing)
- [📦 Deployment](#-deployment)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## 🎯 Overview

**Piața RO** is a modern, full-featured marketplace platform specifically designed for the Romanian market. Built with Django and modern web technologies, it provides a seamless experience for buying and selling items across Romania, featuring AI-powered tools and comprehensive marketplace functionality.

### 🌟 Why Piața RO?

- **🇷🇴 Romanian-First**: Built specifically for Romanian users with local market intelligence
- **🤖 AI-Enhanced**: Integrated AI agents for listing optimization and market analysis
- **📱 Mobile-Ready**: Responsive design optimized for all devices
- **🔒 Secure**: Enterprise-grade security with Django's built-in protections
- **⚡ Fast**: Optimized performance with efficient database queries
- **🎨 Modern UI**: Clean, intuitive interface built with Tailwind CSS

---

## ✨ Key Features

### 🛍️ **Marketplace Core**
- **📋 Comprehensive Listings** - Browse thousands of items across multiple categories
- **🔍 Advanced Search & Filters** - Smart filtering with location, price, and category options
- **🏷️ Category Management** - Organized hierarchical categories for easy navigation
- **🖼️ Image Gallery** - Multiple photos per listing with lightbox preview
- **📍 Location Services** - GPS-based location detection and mapping
- **📱 Mobile-First Design** - Optimized responsive experience

### 👥 **User Management**
- **🔐 Secure Authentication** - User registration, login, and session management handled by Clerk (see [AUTH_CLERK.md](AUTH_CLERK.md) for details).
- **👤 User Profiles** - Detailed seller profiles with contact information
- **💬 Messaging System** - Direct communication between buyers and sellers
- **⭐ Rating & Reviews** - Trust building through user feedback
- **📞 Phone Display** - Secure phone number reveal functionality
- **❤️ Favorites** - Save and manage favorite listings

### 💰 **Advanced Features**
- **💳 Credit System** - Internal currency for premium features
- **🔥 Featured Listings** - Boost visibility with promoted posts
- **📊 Analytics Dashboard** - Track listing performance and views
- **🔔 Notifications** - Real-time alerts for messages and updates
- **🗺️ Interactive Maps** - Leaflet-powered location visualization
- **📱 RESTful API** - Complete API for mobile app development

---

## 🤖 AI-Powered Features

### 🚀 **MCP Advertising Helper Agent**

Our advanced **Model Context Protocol (MCP)** agent provides intelligent marketplace optimization:

#### 📝 **Content Optimization**
- **Smart Title Generation** - AI-powered title suggestions with SEO optimization
- **Description Templates** - Professional, category-specific listing descriptions
- **Keyword Integration** - Local Romanian keywords and search terms

#### 💰 **Market Intelligence**
- **Dynamic Pricing Strategy** - Market-based pricing recommendations
- **Competitor Analysis** - Real-time pricing and trend analysis
- **Local Market Data** - City-specific insights (București, Cluj-Napoca, etc.)

#### 📱 **Social Media Integration**
- **Auto-Generated Content** - Ready-to-post content for Facebook, Instagram, WhatsApp
- **Optimal Timing** - Best posting schedules based on Romanian user behavior
- **A/B Testing** - Automated testing for different listing approaches

---

## 🛠️ Tech Stack

<table>
<tr>
<td>

**Backend**
- Python 3.8+
- Django 4.2+
- Django REST Framework
- SQLite/PostgreSQL
- FastMCP (AI Agents)

</td>
<td>

**Frontend**
- Django Templates
- HTML5/CSS3/JavaScript
- Tailwind CSS 3.0
- Leaflet Maps
- Font Awesome Icons

</td>
<td>

**Tools & Infrastructure**
- Git Version Control
- Node.js (Build Tools)
- npm Package Manager
- Docker Support
- VS Code Integration

</td>
</tr>
</table>

---

## 🏗️ Architecture

```
piata-ro-project/
├── 🎨 marketplace/                 # Main Django application
│   ├── 📄 templates/              # HTML templates
│   │   ├── marketplace/
│   │   │   ├── base.html
│   │   │   ├── listing_detail.html
│   │   │   ├── listings.html
│   │   │   └── ...
│   ├── 🎯 static/                 # Static assets
│   ├── 📊 models.py               # Database models
│   ├── 🔧 views.py                # View logic
│   ├── 🛣️ urls.py                 # URL routing
│   ├── ⚙️ admin.py                # Admin interface
│   ├── 📋 forms.py                # Django forms
│   └── 🔗 signals.py              # Database signals
├── 🔌 api/                        # REST API endpoints
│   ├── 📊 models.py               # API models
│   ├── 🔄 serializers.py          # Data serialization
│   ├── 🎯 views.py                # API views
│   └── 🛣️ urls.py                 # API routing
├── ⚙️ piata_ro/                   # Project configuration
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── 🤖 awesome-mcp-servers/        # AI Agents
│   ├── advertising-agent.py       # Marketing optimization
│   ├── django_sql_agent.py        # Database operations
│   └── stock_agent.py             # Inventory management
├── 🗃️ migrations/                 # Database migrations
├── 📦 requirements.txt            # Python dependencies
└── 📄 package.json               # Node.js configuration
```

---

## 🚀 Quick Start

### Prerequisites

Make sure you have the following installed:
- 🐍 **Python 3.8+** - [Download](https://python.org)
- 📦 **Node.js 16+** - [Download](https://nodejs.org)
- 🔧 **Git** - [Download](https://git-scm.com)

### Installation

1. **📥 Clone the repository**
   ```bash
   git clone https://github.com/valentinuuiuiu/piata-ro-project.git
   cd piata-ro-project
   ```

2. **🐍 Set up Python environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   source venv/bin/activate  # Linux/Mac
   # venv\Scripts\activate   # Windows
   
   # Install Python dependencies
   pip install -r requirements.txt
   ```

3. **🗃️ Set up the database**
   ```bash
   # Run database migrations
   python manage.py migrate
   
   # Create superuser (optional)
   python manage.py createsuperuser
   
   # Load sample data (optional)
   python add_sample_images.py
   ```

4. **🎨 Build frontend assets**
   ```bash
   # Install Node.js dependencies
   npm install
   
   # Build Tailwind CSS
   npm run build:css
   ```

5. **🚀 Start the development server**
   ```bash
   python manage.py runserver
   ```

6. **🌐 Open your browser**
   
   Navigate to `http://localhost:8000` to see your marketplace!

---

## 📱 Usage

### For Users

1. **🔐 Register/Login** - Create an account or sign in
2. **🏠 Browse Listings** - Explore items by category or search
3. **📍 Set Location** - Enable location services for nearby listings
4. **❤️ Save Favorites** - Add interesting items to your favorites
5. **💬 Contact Sellers** - Use the messaging system to communicate
6. **📞 Get Phone Numbers** - Click "Afișează telefon" to reveal contact info

### For Sellers

1. **➕ Add Listings** - Create detailed product listings
2. **📸 Upload Photos** - Add multiple high-quality images
3. **📍 Set Location** - Add precise location for better visibility
4. **💰 Set Pricing** - Use AI recommendations for competitive pricing
5. **📊 Track Performance** - Monitor views and engagement
6. **🔥 Promote Listings** - Use credits to feature your items

### Admin Features

- **👥 User Management** - Manage users and profiles
- **📋 Content Moderation** - Review and approve listings
- **📊 Analytics** - Monitor platform performance
- **💳 Credit Management** - Manage credit packages and transactions

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (optional - SQLite is default)
DATABASE_URL=sqlite:///db.sqlite3

# Clerk Authentication (see AUTH_CLERK.md for more details)
CLERK_PUBLISHABLE_KEY=pk_test_your_clerk_publishable_key
CLERK_SECRET_KEY=sk_test_your_clerk_secret_key

# Stripe (for payments)
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...

# Email (for notifications)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Django Settings

Key settings can be modified in `piata_ro/settings.py`:

- **ALLOWED_HOSTS** - Add your domain
- **DATABASES** - Switch to PostgreSQL for production
- **STATIC_ROOT** - Configure static files for production
- **MEDIA_ROOT** - Configure media uploads

---

## 🤖 MCP Agents

Our AI agents enhance the marketplace experience:

### 📢 Advertising Agent

Optimize your listings with AI-powered recommendations:

```bash
# Start the advertising agent
cd awesome-mcp-servers
python advertising-agent.py
```

**Features:**
- Title optimization
- Description generation
- Pricing recommendations
- SEO improvements

### 🗄️ Django SQL Agent

Manage database operations efficiently:

```bash
# Start the SQL agent
cd awesome-mcp-servers
python django_sql_agent.py
```

**Features:**
- Database queries
- User management
- Listing operations
- Analytics

### 📊 Stock Agent

Monitor inventory and performance:

```bash
# Start the stock agent
cd awesome-mcp-servers
python stock_agent.py
```

**Features:**
- Inventory tracking
- Performance analytics
- Stock alerts
- Trend analysis

---

## 🧪 Testing

### Run Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test marketplace
python manage.py test api

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

### Test Data

```bash
# Load test fixtures
python manage.py loaddata sample-data.json

# Create sample images
python add_sample_images.py

# Create test users
python manage.py shell
# >>> from django.contrib.auth.models import User
# >>> User.objects.create_user('testuser', 'test@example.com', 'password')
```

---

## 📦 Deployment

### Production Setup

1. **🔧 Configure settings**
   ```python
   # piata_ro/settings.py
   DEBUG = False
   ALLOWED_HOSTS = ['yourdomain.com']
   ```

2. **🗃️ Set up database**
   ```bash
   # Use PostgreSQL in production
   pip install psycopg2-binary
   ```

3. **📁 Collect static files**
   ```bash
   python manage.py collectstatic
   ```

4. **🐳 Docker deployment**
   ```bash
   docker-compose up -d
   ```

### Docker

```dockerfile
# Dockerfile included for easy deployment
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Development Workflow

1. **🍴 Fork the repository**
2. **🌿 Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **💾 Commit your changes**
   ```bash
   git commit -m 'Add amazing feature'
   ```
4. **📤 Push to the branch**
   ```bash
   git push origin feature/amazing-feature
   ```
5. **📝 Open a Pull Request**

### Code Standards

- Follow PEP 8 for Python code
- Use meaningful commit messages
- Add tests for new features
- Update documentation as needed

### Areas for Contribution

- 🐛 Bug fixes
- ✨ New features
- 📚 Documentation improvements
- 🎨 UI/UX enhancements
- 🧪 Test coverage
- 🌍 Internationalization

---

## 📄 License

This project is licensed under the **Unlicense** - see the [LICENSE](LICENSE) file for details.

**Why Unlicense?** We believe in open knowledge sharing and want this project to be freely usable, modifiable, and distributable by anyone for any purpose.

---

## 🙏 Acknowledgments

### Special Recognition

**🤖 AI Development Partner**: This project was built through an incredible collaboration with **Claude Sonnet 4**, showcasing the power of human-AI partnership in modern software development.

### Key Contributors

- **👨‍💻 Ionut Baltag** - Project Vision & Implementation  
- **🤖 Claude Sonnet 4** - AI Development Partner & Code Architect
- **🛠️ Sourcery AI & OpenHands** - Development Tools & Integration

### Technologies & Libraries

- **Django Team** - For the amazing web framework
- **Tailwind CSS** - For the utility-first CSS framework
- **Leaflet** - For interactive maps
- **Font Awesome** - For beautiful icons
- **OpenStreetMap** - For map tiles and data

---

## 📞 Contact & Support

<div align="center">

**🇷🇴 Piața RO Development Team**

📧 **Email**: [ionutbaltag3@gmail.com](mailto:ionutbaltag3@gmail.com)  
🔗 **GitHub**: [valentinuuiuiu/piata-ro-project](https://github.com/valentinuuiuiu/piata-ro-project)  
🐛 **Issues**: [Report a Bug](https://github.com/valentinuuiuiu/piata-ro-project/issues)  
💡 **Discussions**: [Ideas & Feedback](https://github.com/valentinuuiuiu/piata-ro-project/discussions)

---

*"The future of development is not human vs AI, but human WITH AI"* 🚀

**Built with ❤️ in Romania through human-AI collaboration**

</div>
