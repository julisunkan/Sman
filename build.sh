#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit  # exit on error

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p instance
mkdir -p uploads/kyc_documents
mkdir -p uploads/payment_proofs
mkdir -p uploads/screenshots

echo "Build completed successfully"