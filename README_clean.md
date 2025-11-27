# gpscontrol4u Marketplace - Clean Version

A Django-based marketplace platform for data collection services with integrated payment processing via Mercado Pago.

## Features

- **User Registration & Authentication**: Email verification, custom user model
- **Admin Dashboard**: Custom admin interface with user and payment statistics
- **Payment Integration**: Mercado Pago integration for plan subscriptions
- **Multi-language Support**: English and Spanish (es-MX)
- **External API Integration**: RFC/TIN validation service
- **Responsive Design**: Modern UI with custom styling

## Project Structure

```
marketplace_clean/
├── manage.py                    # Django management script
├── marketplace_backend/         # Django project settings
├── accounts/                    # User accounts app
├── gpscontrol4u/                 # Data collection forms app
├── payments/                    # Payment processing app
├── api/                         # REST API endpoints
├── templates/                   # HTML templates
├── static/                      # CSS, JS, images
├── locale/                      # Translation files
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment configuration template
└── setup.sh                     # Automated setup script
```

## Quick Start

1. **Clone or copy this project** to your desired location

2. **Run the setup script**:
   ```bash
   ./setup.sh
   ```

3. **Configure your environment**:
   - Edit `.env` with your database, email, and payment credentials
   - Set up your MySQL database
   - Configure Mercado Pago credentials

4. **Start the development server**:
   ```bash
   source venv/bin/activate
   python manage.py runserver
   ```

5. **Access the application**:
   - Main site: http://localhost:8000/
   - Admin panel: http://localhost:8000/admin/

## Configuration

### Required Environment Variables

Copy `.env.example` to `.env` and configure:

- **Database**: MySQL connection settings
- **Email**: SMTP configuration for notifications
- **Mercado Pago**: Access token and public key for payments
- **External API**: Credentials for RFC validation service

### Database Setup

1. Create a MySQL database
2. Update database credentials in `.env`
3. Run migrations: `python manage.py migrate`

### Email Configuration

Configure SMTP settings in `.env` for user registration and notifications.

### Payment Setup

1. Create a Mercado Pago account
2. Get your access token and public key
3. Configure in `.env`

## Apps Overview

### Accounts App
- User registration and authentication
- Email verification
- Profile management
- Custom admin dashboard

### gpscontrol4u App
- Data collection forms
- Form management
- Data recording

### Payments App
- Plan subscriptions
- Mercado Pago integration
- Payment processing

### API App
- REST API endpoints
- Health checks

## Development

### Running Tests
```bash
python manage.py test
```

### Creating Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Collecting Static Files
```bash
python manage.py collectstatic
```

## Deployment

This project is configured for deployment with:
- Gunicorn for WSGI server
- Whitenoise for static files
- PostgreSQL/MySQL database
- Redis for Celery (background tasks)

## License

This project is proprietary software.

## Support

For support, please contact the development team.
