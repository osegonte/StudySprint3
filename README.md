
# StudySprint 3.0

> **Advanced Study Management Platform with PDF Integration and Smart Analytics**

## 🎯 Current Status: Stage 2 Complete

✅ **Users Module** - Complete authentication, preferences, and session management  
✅ **Topics Module** - Complete topic organization, hierarchy, and goal tracking  
🎯 **Next: PDFs Module** - File upload, storage, and metadata extraction

## 🚀 Quick Start

### Development Setup

1. **Clone and setup:**
   ```bash
   git clone <repository>
   cd StudySprint3
   ```

2. **Backend setup:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```

3. **Environment configuration:**
   ```bash
   cp .env.example .env
   # Edit .env with your database settings
   ```

4. **Database setup:**
   ```bash
   docker-compose up -d postgres redis
   alembic upgrade head
   ```

5. **Start development server:**
   ```bash
   uvicorn main:app --reload
   ```

6. **Access API documentation:**
   - API Docs: http://localhost:8000/api/docs
   - Health Check: http://localhost:8000/api/health

## 🏗️ Architecture

### Modular Backend Structure
```
backend/
├── modules/                 # Feature modules
│   ├── users/              # Authentication & user management
│   ├── topics/             # Topic organization & goals  
│   ├── pdfs/               # PDF upload & management (next)
│   ├── exercises/          # Exercise management (pending)
│   ├── sessions/           # Study session tracking (pending)
│   ├── notes/              # Note-taking system (pending)
│   └── analytics/          # Analytics & insights (pending)
├── common/                 # Shared utilities
│   ├── config.py          # Configuration management
│   ├── database.py        # Database connections
│   └── errors.py          # Exception handling
└── main.py                # FastAPI application
```

### Database Schema
- **Users**: Authentication, preferences, sessions
- **Topics**: Hierarchical organization, goals, progress tracking
- **Future**: PDFs, exercises, notes, analytics, study sessions

## 📡 API Endpoints

### Authentication (`/api/v1/auth`)
- `POST /register` - User registration
- `POST /login` - User login  
- `POST /logout` - User logout
- `GET /me` - Get current user
- `PUT /me` - Update user profile
- `POST /change-password` - Change password
- `GET /preferences` - Get user preferences
- `PUT /preferences` - Update preferences

### Topics (`/api/v1/topics`)
- `GET /` - Get all topics
- `POST /` - Create topic
- `GET /{id}` - Get specific topic
- `PUT /{id}` - Update topic
- `DELETE /{id}` - Delete topic
- `GET /search` - Search topics
- `POST /{id}/toggle-completion` - Toggle completion
- `POST /{id}/goals` - Create goal
- `GET /{id}/goals` - Get topic goals
- `GET /{id}/stats` - Get statistics

## 🛠️ Development

### Testing
```bash
# Run specific module tests
python -m pytest modules/users/tests/ -v
python -m pytest modules/topics/tests/ -v

# Run all tests with coverage
python -m pytest --cov=modules --cov-report=html
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Check current revision
alembic current
```

### Code Quality
```bash
# Format code
black modules/
isort modules/

# Type checking
mypy modules/

# Linting
flake8 modules/
```

## 🐳 Docker Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

## 🗃️ Database

### PostgreSQL (Main Database)
- Host: localhost:5432
- Database: studysprint3
- User: studysprint

### Redis (Cache & Sessions)
- Host: localhost:6379
- Used for: Session storage, caching, background tasks

## 📋 Roadmap

### ✅ Stage 1: Foundation (Complete)
- Modular project structure
- Database schema design
- Docker development environment

### ✅ Stage 2: Core Backend (In Progress)
- ✅ Users Module - Authentication & management
- ✅ Topics Module - Organization & goals
- 🎯 PDFs Module - File upload & management
- ⏳ Exercises Module - Exercise management
- ⏳ Sessions Module - Study tracking
- ⏳ Notes Module - Note-taking system
- ⏳ Analytics Module - Progress tracking

### ⏳ Stage 3: Integration & Testing
- Module integration
- End-to-end testing
- Performance optimization

### ⏳ Stage 4: Frontend Foundation
- React application setup
- Authentication UI
- Layout & navigation

### ⏳ Stage 5-11: Feature Development
- Core UI modules
- Advanced features
- Deployment & launch

## 🤝 Contributing

1. Follow the modular architecture
2. Write tests for all new features
3. Use type hints and docstrings
4. Follow existing code style
5. Update documentation

## 📄 License

[Your License Here]

---

**Built with:** FastAPI, SQLAlchemy, PostgreSQL, Redis, React (planned)