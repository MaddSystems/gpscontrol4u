# Marketplace Web Application

A Django-based web application that serves as a marketplace for the gpscontrol4u iOS and Android apps, implementing a freemium model with bilingual support (English/Spanish) for USA and Mexico markets.

## Features Implemented

### ✅ Core Functionality
- **Django Backend**: Complete Django 4.2 application with custom User model
- **Database**: MySQL integration with comprehensive models
- **Authentication**: User registration, login, and profile management
- **Bilingual Support**: English and Spanish interface
- **Responsive UI**: Bootstrap-based responsive design
- **REST API**: Basic API endpoints for future iOS app integration

### ✅ User Management
- Custom User model with role-based access (free/premium)
- User profiles with extended information
- Language preference management
- Account linking preparation for iOS app
- **Email verification system for secure registration**
- Resend verification email functionality

### ✅ gpscontrol4u Integration
- Form management system (predefined and custom forms)
- Data collection and storage
- Form templates for different use cases
- Freemium model implementation

### ✅ Payment System (Structure)
- Subscription model for premium features
- Pricing plans for USD and MXN currencies
- Payment tracking system (ready for Stripe/Mercado Pago integration)

### ✅ Web Interface
- Modern, responsive landing page
- User dashboard with statistics
- Pricing page with bilingual content
- Profile management interface
- Registration and login forms

### ✅ API Foundation
- REST API structure ready for iOS app
- Token-based authentication
- Health check endpoint
- Extensible for full CRUD operations

## Project Structure

```
marketplace/
├── accounts/               # User management
├── api/                   # REST API endpoints
├── gpscontrol4u/           # Forms and data management
├── payments/              # Subscription and payment handling
├── marketplace_backend/   # Django settings and configuration
├── templates/            # HTML templates
├── static/              # CSS, JS, and images
├── requirements.txt     # Python dependencies
└── manage.py           # Django management
```

## Technology Stack

- **Backend**: Django 4.2, Python 3.10
- **Database**: MySQL 8.0 with PyMySQL driver
- **Frontend**: Bootstrap 5, Font Awesome, HTML5
- **API**: Django REST Framework
- **Authentication**: Django's built-in + Token authentication
- **Static Files**: WhiteNoise for development

## Getting Started

### Prerequisites

Before setting up the marketplace, ensure you have:
- Python 3.10 or higher
- MySQL 8.0 or higher
- Git

### Installation Steps

#### Step 1: Environment Configuration (REQUIRED FIRST)

**Create the `.env` file** with your database and application settings:

```bash
# Navigate to project directory
cd /home/systemd/marketplace

# Create .env file (copy from .env.example if available)
nano .env
```

**Required `.env` configuration:**
```properties
# Database Configuration (REQUIRED)
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_USER=your_mysql_user
DATABASE_PASSWORD=your_mysql_password
DATABASE_NAME=your_database_name

# Email Configuration (REQUIRED for user registration)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=your_smtp_host
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@domain.com
EMAIL_HOST_PASSWORD=your_email_password
DEFAULT_FROM_EMAIL=Marketplace <your_email@domain.com>

# Django Configuration (REQUIRED)
SECRET_KEY=your-super-secret-key-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Mercado Pago Configuration (for payments)
MERCADO_PAGO_ACCESS_TOKEN=your_mercado_pago_token
MERCADO_PAGO_PUBLIC_KEY=your_mercado_pago_public_key
MERCADO_PAGO_SANDBOX=True
```

#### Step 2: Python Environment Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Step 3: Database Setup (Automated)

**Option A: Automated Setup (Recommended)**
```bash
# Make script executable and run
chmod +x setup_database.sh
./setup_database.sh
```

**Option B: Manual Setup**
```bash
# Create MySQL database (using credentials from .env)
mysql -u your_mysql_user -p
# Enter your password, then in MySQL prompt:
CREATE DATABASE your_database_name;
EXIT;

# Run Django migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

#### Step 4: Start Development Server

```bash
python manage.py runserver 0.0.0.0:8000
```

### Quick Setup for New Installation

If you're setting up on a fresh system with the automated setup script:

```bash
# 1. Navigate to project and set up .env file FIRST
cd /home/systemd/marketplace
# Edit .env with your configuration (see Step 1 above)

# 2. Activate virtual environment and install dependencies
source venv/bin/activate
pip install -r requirements.txt

# 3. Run automated database setup
./setup_database.sh

# Server will start automatically, or run manually:
python manage.py runserver 0.0.0.0:8000
```

### Access Points

- **Web Interface**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin ,  https://store.gpscontrol4u.mx/admin/
- **API Health**: http://localhost:8000/api/health/

### Test Accounts

#### Admin Access
- **Admin Panel**: http://localhost:8000/admin
- **Default Credentials**: admin@marketplace.com / admin123
  _(Created automatically by setup script, or manually during superuser creation)_

#### Regular Users
You can create test accounts through the registration page at http://localhost:8000/register

### Troubleshooting

#### Database Connection Issues
If you encounter database connection errors:

1. **Verify .env Configuration**:
   ```bash
   # Check that your .env file has all required database variables
   grep "DATABASE_" .env
   ```

2. **Create MySQL User** (if not exists):
   ```sql
   # Use the credentials from your .env file
   CREATE USER 'your_db_user'@'localhost' IDENTIFIED BY 'your_db_password';
   GRANT ALL PRIVILEGES ON your_database_name.* TO 'your_db_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

3. **Verify Database Exists**:
   ```bash
   # Use credentials from your .env file
   mysql -u your_db_user -p -e "SHOW DATABASES;"
   # Should show your database name in the list
   ```

4. **Check Connection**:
   ```bash
   python manage.py dbshell
   # Should connect to MySQL without errors
   ```

#### Migration Issues

**If you get "Duplicate column name" errors during migration:**
```bash
# The setup script handles this automatically, but if needed:
# Delete problematic migration files and recreate database
mysql -u your_db_user -p
# In MySQL prompt:
DROP DATABASE your_database_name;
CREATE DATABASE your_database_name;
EXIT;
python manage.py migrate
```

**If other migration errors occur:**
```bash
# Show migration status
python manage.py showmigrations

# Reset all migrations (development only - deletes all data)
python manage.py migrate --fake-initial
```

#### Permission Issues
Ensure your user has permissions to read the project files:
```bash
chmod -R 755 /home/systemd/marketplace
```

## Database Configuration

The application uses MySQL database with configuration defined in your `.env` file:

```properties
DATABASE_HOST=localhost          # Database server host
DATABASE_PORT=3306              # Database server port
DATABASE_USER=your_mysql_user   # MySQL username
DATABASE_PASSWORD=your_password # MySQL password
DATABASE_NAME=your_database     # Database name
```

**Important**: Always configure your `.env` file with your specific database credentials before running the setup script.

## API Endpoints

### Available Endpoints
- `GET /api/health/` - API health check
- `POST /api/auth/register/` - User registration (ready for implementation)
- `POST /api/auth/login/` - User login (ready for implementation)
- `GET /api/profile/` - User profile (ready for implementation)

### Future iOS App Integration
The API structure is prepared for:
- Form synchronization
- Data submission and retrieval
- Subscription management
- Language preference sync

## Freemium Model

### Free Tier
- Access to predefined forms
- Basic data collection (100 records limit)
- Mobile app access
- Bilingual support

### Premium Tier
- Unlimited custom forms
- Advanced data analytics
- 10,000 records limit
- Data export capabilities
- Priority support

## Payment Integration (Ready for Implementation)

### Stripe (USD)
- Structure ready for subscription billing
- Webhook handling prepared
- USD currency support for USA market

### Mercado Pago (MXN)
- Structure ready for Mexico market
- MXN currency support
- Localized payment experience

## Bilingual Support

### Implementation
- Django i18n framework ready
- User language preference storage
- Template structure for translations
- API responses prepared for localization

### Supported Languages
- **English (en)**: Primary language for USA market
- **Spanish (es)**: Primary language for Mexico market

## Development Features

### Admin Interface
Complete Django admin with:
- User management
- Form and data viewing
- Subscription tracking
- Payment monitoring

### Models
- **User**: Custom user model with role and language
- **Form**: gpscontrol4u form definitions
- **DataRecord**: User-submitted data
- **Subscription**: Premium subscriptions
- **Payment**: Payment transaction logs

## Next Steps for Full Implementation

### Phase 1: Payment Integration
1. **Stripe Setup**:
   - Add Stripe API keys to environment
   - Implement subscription webhooks
   - Create payment flows

2. **Mercado Pago Setup**:
   - Add Mercado Pago credentials
   - Implement checkout flows
   - Handle currency conversion

### Phase 2: API Completion
1. **Complete REST API**:
   - Implement all CRUD operations
   - Add authentication decorators
   - Create comprehensive serializers

2. **iOS App Integration**:
   - Form synchronization endpoints
   - Real-time data sync
   - Push notification support

### Phase 3: Advanced Features
1. **Analytics Dashboard**:
   - Data visualization
   - Export functionality
   - Advanced reporting

2. **Team Features**:
   - Multi-user workspaces
   - Permission management
   - Collaboration tools

## Security Features

### Implemented
- CSRF protection
- Secure password handling
- SQL injection prevention via ORM
- XSS protection

### Production Ready
- Environment variable configuration
- Database credential security
- Static file serving optimization

## Deployment Considerations

### Environment Variables
Configure these for production:
```env
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=mp.armaddia.lat
DATABASE_HOST=localhost
DATABASE_USER=gpscontrol
DATABASE_PASSWORD=qazwsxedc
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
MERCADO_PAGO_ACCESS_TOKEN=...
```

### Cloudflare Integration
- Domain: mp.armaddia.lat
- SSL certificate handling
- CDN for static files
- DDoS protection

### Production Checklist
- [ ] Configure production database
- [ ] Set up Stripe/Mercado Pago accounts
- [ ] Configure email backend
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy
- [ ] Set up CI/CD pipeline

## Support and Documentation

### Resources
- **gpscontrol4u iOS App**: https://apps.apple.com/us/app/gpscontrol4u/id1524505384
- **gpscontrol4u Android App**: https://play.google.com/store/apps/details?id=mx.com.madd.gpscontrol4uego
- **Django Documentation**: https://docs.djangoproject.com/
- **Django REST Framework**: https://www.django-rest-framework.org/
- **Bootstrap Documentation**: https://getbootstrap.com/docs/

### Contact
For development questions or support, refer to the PRD.md file for detailed requirements and specifications.

---

**Status**: ✅ Core application completed and ready for testing
**Next**: Payment integration and API completion for iOS app

## Email Configuration

### Setup Email Backend

The application supports email verification for user registration. Configure email settings in your `.env` file:

#### For Development (Console Backend)
```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```
This will print emails to the console for testing.

#### For Production (SMTP Backend)
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=Marketplace <your-email@gmail.com>
```

### Gmail Configuration
1. Enable 2-Factor Authentication in your Gmail account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
   - Use this password in `EMAIL_HOST_PASSWORD`

### Email Features
- **User Registration**: Email verification required for account activation
- **Admin Interface**: View email verification status in Django admin
- **Management Commands**: Test email configuration
- **Resend Verification**: Users can request new verification emails
- **Bilingual Templates**: Email templates available in English and Spanish

### Testing Email
Test your email configuration:
```bash
python manage.py test_email --to your-email@example.com
```

### Admin Features
In Django admin (`/admin/`), you can:
- View email verification status for all users
- Send verification emails to selected users
- Manually mark emails as verified
- Filter users by verification status

### Troubleshooting

#### Email Verification Issues

**If email verification links show "example.com" instead of your domain:**

This happens when Django's Sites framework is not updated with your domain from `.env`.

```bash
# Fix: Update site domain from .env file
python manage.py update_site

# Verify the fix
python manage.py shell -c "
from django.contrib.sites.models import Site
site = Site.objects.get(pk=1)
print(f'Site domain: {site.domain}')
"
```

**The setup script automatically handles this**, but for existing databases you may need to run the update manually.

**Note**: The `DOMAIN` variable in your `.env` file should contain only the domain name (e.g., `mp.armaddia.lat`), not the full URL with protocol.

```
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export HOME="/home/systemd"
export USER="systemd"
export DJANGO_SETTINGS_MODULE="marketplace_backend.settings"
export DATABASE_HOST="localhost"
export DATABASE_PORT="3306"
export DATABASE_USER="gpscontrol"
export DATABASE_PASSWORD="qazwsxedc"
export DATABASE_NAME="marketplace_db_4"
export EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend"
export EMAIL_HOST="pro.turbo-smtp.com"
export EMAIL_PORT="465"
export EMAIL_USE_TLS="False"
export EMAIL_USE_SSL="True"
export EMAIL_HOST_USER="orders@gpscontrol4u.mx"
export EMAIL_HOST_PASSWORD="GPSc0ntr0l01"
export DEFAULT_FROM_EMAIL="gpscontrol4u <orders@gpscontrol4u.mx>"
export SECRET_KEY="your-super-secret-key-change-this-in-production"
export DEBUG="True"
export ALLOWED_HOSTS="localhost,127.0.0.1,mp.armaddia.lat"
export STRIPE_TEST_PUBLIC_KEY="pk_test_YOUR_ACTUAL_PUBLIC_KEY_HERE"
export STRIPE_TEST_SECRET_KEY="sk_test_YOUR_ACTUAL_SECRET_KEY_HERE"
export STRIPE_WEBHOOK_SECRET="whsec_YOUR_WEBHOOK_SECRET_HERE"
export MERCADO_PAGO_ACCESS_TOKEN="APP_USR-6799654648924759-041901-f777239afb0ed2e912526aba5827152e-2392505242"
export MERCADO_PAGO_PUBLIC_KEY="APP_USR-e7f9e8b4-3a9d-4246-876f-a60a8988af36"
export MERCADO_PAGO_SANDBOX="True"
export MERCADO_PAGO_TEST_BUYER_EMAIL="TESTUSER632906111@testuser.com"
export MERCADO_PAGO_TEST_BUYER_PASSWORD="PVOlNBKTEK"
export DOMAIN="store.gpscontrol4u.mx"
export CLOUD_PLATFORM="RAILWAY"
export LANGUAGES="en,es"
export REDIS_URL="redis://localhost:6379/0"
```