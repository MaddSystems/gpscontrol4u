#!/bin/bash

echo "🚀 Setting up gpscontrol4u Marketplace Project"
echo "============================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Copy environment file
echo "⚙️  Setting up environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file from template. Please edit it with your configuration."
else
    echo "ℹ️  .env file already exists."
fi

# Run migrations
echo "🗄️  Setting up database..."
python manage.py migrate

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser (optional)
read -p "👤 Do you want to create a superuser? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python manage.py createsuperuser
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To start the development server:"
echo "  source venv/bin/activate"
echo "  python manage.py runserver"
echo ""
echo "Admin panel: http://localhost:8000/admin/"
echo "Main site: http://localhost:8000/"
echo ""
echo "Don't forget to:"
echo "  1. Edit .env with your actual configuration"
echo "  2. Set up your database"
echo "  3. Configure email settings"
echo "  4. Set up Mercado Pago credentials"
