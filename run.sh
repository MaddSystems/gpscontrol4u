#!/bin/bash

# Load environment variables from .env file
set -a
source .env
set +a

# Set additional environment variables
export DJANGO_SETTINGS_MODULE="marketplace_backend.settings"

# Run Django development server
python3 manage.py runserver 0.0.0.0:7008
