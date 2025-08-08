#!/bin/bash

# Byte Bandits MCP Server Setup Script
# This script automates the initial setup process

set -e

echo "🚀 Setting up Byte Bandits MCP Server..."

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
required_version="3.11"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
    echo "❌ Error: Python 3.11 or higher is required. Found: Python $python_version"
    exit 1
fi
echo "✅ Python version check passed: $python_version"

# Create virtual environment
echo "🔧 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "🔧 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -e .

# Install development dependencies (optional)
echo "📦 Installing development dependencies..."
pip install -e ".[dev]"

# Create .env file from example if it doesn't exist
echo "🔧 Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ Created .env file from template"
    echo "⚠️  Please edit .env file with your configuration:"
    echo "   - AUTH_TOKEN: Your secret authentication token"
    echo "   - MY_NUMBER: Your phone number in format {country_code}{number}"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Run the server: python main.py"
echo "3. Make it public via ngrok or cloud deployment"
echo "4. Connect with Puch AI using /mcp connect command"
echo ""
echo "📚 For detailed instructions, see README.md"
