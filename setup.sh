#!/bin/bash

# Render deployment initialization script
# This runs once to set up the data directory

echo "🚀 Setting up Cooking Bot on Render..."

# CRITICAL: Clear proxy environment variables FIRST
# These cause "unexpected keyword argument 'proxies'" error in telebot
export -n HTTP_PROXY
export -n HTTPS_PROXY
export -n http_proxy
export -n https_proxy
export -n ALL_PROXY
export -n all_proxy
export -n NO_PROXY
export -n no_proxy

# Unset them for this shell too
unset HTTP_PROXY
unset HTTPS_PROXY
unset http_proxy
unset https_proxy
unset ALL_PROXY
unset all_proxy
unset NO_PROXY
unset no_proxy

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
