#!/bin/bash

# Deployment script for Stabsspelet
echo "🚀 Preparing Stabsspelet for deployment..."

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Make sure you're in the project root directory."
    exit 1
fi

# Check if required files exist
echo "📋 Checking required files..."
required_files=("requirements.txt" "Procfile" "runtime.txt" "app.py")
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file found"
    else
        echo "❌ $file missing"
        exit 1
    fi
done

# Generate a secret key if needed
echo "🔑 Generating secret key..."
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(16))")
echo "Generated SECRET_KEY: $SECRET_KEY"
echo "Remember to set this as an environment variable in Render!"

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit for deployment"
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already exists"
fi

echo ""
echo "🎉 Preparation complete!"
echo ""
echo "Next steps:"
echo "1. Push your code to GitHub:"
echo "   git remote add origin <your-github-repo-url>"
echo "   git push -u origin main"
echo ""
echo "2. Go to https://render.com and create a new Web Service"
echo "3. Connect your GitHub repository"
echo "4. Set the following environment variables:"
echo "   SECRET_KEY: $SECRET_KEY"
echo "   FLASK_ENV: production"
echo ""
echo "5. Deploy and enjoy your live app! 🚀"
