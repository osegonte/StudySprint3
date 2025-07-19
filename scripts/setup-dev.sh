#!/bin/bash
# scripts/setup-dev.sh
# StudySprint 3.0 Development Environment Setup

set -e  # Exit on any error

echo "🚀 Setting up StudySprint 3.0 development environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if Python 3.11+ is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi

# Get Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    print_error "Python 3.11+ is required. Found Python $PYTHON_VERSION"
    exit 1
fi

print_success "Docker and Python requirements met"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    print_status "Creating .env file from template..."
    cp .env.example .env
    print_warning "Please review and update the .env file with your configuration"
else
    print_status ".env file already exists"
fi

# Create upload directories
print_status "Creating upload directories..."
mkdir -p backend/uploads

# Set up Python virtual environment for backend
print_status "Setting up Python virtual environment..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
print_status "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements-dev.txt
print_success "Python dependencies installed"

# Return to root directory
cd ..

# Start Docker services
print_status "Starting Docker services..."
docker-compose up -d postgres redis

# Wait for services to be healthy
print_status "Waiting for services to be ready..."
sleep 10

# Check if PostgreSQL is ready
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker-compose exec -T postgres pg_isready -U studysprint -d studysprint3 > /dev/null 2>&1; then
        print_success "PostgreSQL is ready"
        break
    else
        print_status "Waiting for PostgreSQL... ($((RETRY_COUNT + 1))/$MAX_RETRIES)"
        sleep 2
        RETRY_COUNT=$((RETRY_COUNT + 1))
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    print_error "PostgreSQL failed to start within expected time"
    exit 1
fi

# Check if Redis is ready
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    print_success "Redis is ready"
else
    print_error "Redis is not responding"
    exit 1
fi

# Run database migrations
print_status "Setting up database schema..."
cd backend
source venv/bin/activate

# Initialize Alembic if not already done
if [ ! -f "alembic/versions/.gitkeep" ]; then
    print_status "Initializing Alembic..."
    alembic init alembic
fi

# Create initial migration
print_status "Creating initial database migration..."
alembic revision --autogenerate -m "Initial schema"

# Run migrations
print_status "Running database migrations..."
alembic upgrade head

print_success "Database schema setup complete"

cd ..

# Test backend startup
print_status "Testing backend startup..."
cd backend
source venv/bin/activate

# Start backend in background and test health endpoint
python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Test health endpoint
if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
    print_success "Backend health check passed"
else
    print_error "Backend health check failed"
fi

# Stop background backend
kill $BACKEND_PID 2>/dev/null || true

cd ..

# Summary
echo ""
echo "=========================================="
print_success "StudySprint 3.0 development environment setup complete!"
echo "=========================================="
echo ""
echo "📋 Next steps:"
echo "   1. Review and update .env file if needed"
echo "   2. Start the backend development server:"
echo "      cd backend"
echo "      source venv/bin/activate"
echo "      uvicorn main:app --reload"
echo ""
echo "   3. Access the API documentation at:"
echo "      http://localhost:8000/api/docs"
echo ""
echo "🐳 Docker services running:"
echo "   - PostgreSQL: localhost:5432"
echo "   - Redis: localhost:6379"
echo ""
echo "🛠️  To stop Docker services:"
echo "   docker-compose down"
echo ""
echo "🎯 Ready to start building modules!"

# Make script executable
chmod +x scripts/setup-dev.sh