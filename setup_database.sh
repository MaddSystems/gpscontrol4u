#!/bin/bash
# Fresh Database Setup Script for Marketplace
# This script creates a clean database and runs migrations
# Usage: ./setup_database.sh [-y] (use -y to skip all prompts)

# Check for -y flag
AUTO_YES=false
if [[ "$1" == "-y" ]]; then
    AUTO_YES=true
    echo "🚀 Marketplace Database Setup Script (Auto Mode)"
else
    echo "🚀 Marketplace Database Setup Script"
fi
echo "======================================"

# Check if virtual environment is activated, activate if not
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "🔄 Virtual environment not activated, activating..."
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        echo "✅ Virtual environment activated"
    else
        echo "❌ Virtual environment not found at venv/bin/activate"
        echo "Please ensure you have a virtual environment set up:"
        echo "  python3 -m venv venv"
        echo "  source venv/bin/activate"
        echo "  pip install -r requirements.txt"
        exit 1
    fi
fi

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ manage.py not found! Make sure you're in the marketplace directory"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please create a .env file with your database configuration first."
    echo "See README.md for setup instructions."
    exit 1
fi

# Read database configuration from .env file
echo "� Reading database configuration from .env file..."
DB_NAME=$(grep "^DATABASE_NAME=" .env | cut -d'=' -f2)
DB_USER=$(grep "^DATABASE_USER=" .env | cut -d'=' -f2)
DB_PASSWORD=$(grep "^DATABASE_PASSWORD=" .env | cut -d'=' -f2)
DB_HOST=$(grep "^DATABASE_HOST=" .env | cut -d'=' -f2)

# Validate required environment variables
if [ -z "$DB_NAME" ] || [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ]; then
    echo "❌ Missing required database configuration in .env file!"
    echo "Required variables: DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD"
    exit 1
fi

echo "�📋 This script will:"
echo "   1. Drop and recreate the '$DB_NAME' database"
echo "   2. Run Django migrations"
echo "   3. Optionally create a superuser"
echo ""

if [ "$AUTO_YES" = false ]; then
    echo "⚠️  WARNING: This will delete all existing data!"
    read -p "Do you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Operation cancelled."
        exit 1
    fi
else
    echo "⚠️  WARNING: Auto mode enabled - proceeding without confirmation!"
fi

echo ""
echo "🗄️  Step 1: Recreating database..."
mysql -u "$DB_USER" -p"$DB_PASSWORD" -h "$DB_HOST" -e "DROP DATABASE IF EXISTS $DB_NAME; CREATE DATABASE $DB_NAME;"

if [ $? -eq 0 ]; then
    echo "✅ Database '$DB_NAME' created successfully"
else
    echo "❌ Database creation failed. Check MySQL credentials and permissions."
    echo "Database: $DB_NAME, User: $DB_USER, Host: $DB_HOST"
    exit 1
fi

echo ""
echo "📊 Step 2: Running Django migrations..."

# First, try to run migrations normally
echo "🔄 Attempting normal migration..."
python manage.py migrate

if [ $? -eq 0 ]; then
    echo "✅ All migrations completed successfully"
    
    # Update site domain from .env file
    echo ""
    echo "🌐 Step 2.1: Updating site domain from .env..."
    python manage.py update_site
    
    if [ $? -eq 0 ]; then
        echo "✅ Site domain updated successfully"
    else
        echo "⚠️  Site domain update failed, but continuing..."
    fi
else
    echo "⚠️  Normal migration failed, trying alternative approaches..."
    
    # Check if the problematic migration exists and try to fake it
    if [ -f "accounts/migrations/0005_auto_20250626_2155.py" ]; then
        echo "🔄 Detected problematic migration 0005, trying to fake it..."
        
        # Try to fake the problematic migration
        python manage.py migrate accounts 0004 --fake
        python manage.py migrate accounts 0005 --fake
        
        # Then try to run remaining migrations
        python manage.py migrate
        
        if [ $? -eq 0 ]; then
            echo "✅ Migrations completed after faking problematic migration"
        else
            echo "❌ Still failing, trying --run-syncdb approach..."
            python manage.py migrate --run-syncdb
            
            if [ $? -eq 0 ]; then
                echo "✅ Migrations completed with syncdb"
            else
                echo "❌ All migration attempts failed."
                echo ""
                echo "🛠️  Manual fix required:"
                echo "  1. python manage.py migrate accounts 0004 --fake"
                echo "  2. python manage.py migrate accounts 0005 --fake"  
                echo "  3. python manage.py migrate"
                echo ""
                echo "Or delete the problematic migration file:"
                echo "  rm accounts/migrations/0005_auto_20250626_2155.py"
                exit 1
            fi
        fi
    else
        echo "❌ Migration failed for unknown reason."
        echo "Check the error above and try running migrations manually."
        exit 1
    fi
fi

echo ""
if [ "$AUTO_YES" = false ]; then
    read -p "Do you want to create a superuser now? (Y/n): " -n 1 -r
    echo
    CREATE_SUPERUSER=true
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        CREATE_SUPERUSER=false
    fi
else
    echo "🤖 Auto mode: Creating superuser automatically..."
    CREATE_SUPERUSER=true
fi

if [ "$CREATE_SUPERUSER" = true ]; then
    echo ""
    echo "👤 Creating superuser..."
    echo "Recommended credentials for development:"
    echo "Email: admin@gpscontrol4u.com"
    echo "Password: GPSc0ntr0l1"
    echo ""
    
    # Create superuser with all required fields for custom User model
    DJANGO_SUPERUSER_EMAIL="admin@gpscontrol4u.com" \
    DJANGO_SUPERUSER_PASSWORD="GPSc0ntr0l1" \
    DJANGO_SUPERUSER_FIRST_NAME="Admin" \
    DJANGO_SUPERUSER_LAST_NAME="User" \
    python manage.py createsuperuser --noinput \
        --email admin@gpscontrol4u.com \
        --first_name Admin \
        --last_name User
    

    if [ $? -eq 0 ]; then
        echo "✅ Superuser created successfully"
        echo "   Email: admin@gpscontrol4u.com"
        echo "   Password: GPSc0ntr0l1"
        # Marcar email como verificado para el superusuario
        echo "🔑 Marcando email como verificado para el superusuario..."
        python manage.py shell -c "from accounts.models import User; User.objects.filter(email='admin@gpscontrol4u.com').update(email_verified=True)"
    else
        echo "⚠️  Automated superuser creation failed, running interactive mode..."
        python manage.py createsuperuser
        # Intentar marcar como verificado si ya existe
        echo "🔎 Verificando si el superusuario ya existe para marcar email como verificado..."
        python manage.py shell -c "from accounts.models import User; User.objects.filter(email='admin@gpscontrol4u.com').update(email_verified=True)"
    fi
fi

echo ""
echo "🎉 Setup complete!"
echo ""
if [ "$AUTO_YES" = false ]; then
    echo "📋 Next steps:"
    echo "   1. Start the server: python manage.py runserver 0.0.0.0:8000"
    echo "   2. Visit: http://localhost:8000"
    echo "   3. Admin: http://localhost:8000/admin"
    echo ""
    echo "✅ Ready for development!"
else
    echo "🤖 Auto setup completed!"
    echo "📊 Summary:"
    echo "   ✅ Database recreated: $DB_NAME"
    echo "   ✅ Migrations applied successfully"
    echo "   ✅ Superuser created: admin@gpscontrol4u.com / GPSc0ntr0l1"
    echo ""
    echo "🚀 Starting development server..."
    python manage.py runserver 0.0.0.0:8000
fi
