#!/bin/bash

# Render deployment initialization script
# This runs once to set up the data directory

echo "🚀 Setting up Cooking Bot on Render..."

# Clear proxy environment variables that cause conflicts with telebot
unset HTTP_PROXY
unset HTTPS_PROXY
unset http_proxy
unset https_proxy
unset ALL_PROXY
unset all_proxy

# Create data directory if it doesn't exist
mkdir -p data

# Initialize empty JSON files if they don't exist
if [ ! -f data/receipts.json ]; then
    echo "[]" > data/receipts.json
    echo "✅ Created receipts.json"
fi

if [ ! -f data/comments.json ]; then
    echo "[]" > data/comments.json
    echo "✅ Created comments.json"
fi

echo "✅ Data directory initialized"
echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🎉 Setup complete! Starting server..."
