#!/usr/bin/env bash
# Start script for Render deployment

# Set environment variables for production
export FLASK_ENV=production
export DATABASE_URL=sqlite:///instance/marketplace.db

# Create necessary directories if they don't exist
mkdir -p instance
mkdir -p uploads/kyc_documents
mkdir -p uploads/payment_proofs
mkdir -p uploads/screenshots

# Start the application
exec gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 1 --timeout 120 main:app