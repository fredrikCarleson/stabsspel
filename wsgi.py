#!/usr/bin/env python3
"""
WSGI entry point for Stabsspelet production deployment
"""

import os
from app import app
from config import config

# Load configuration based on environment
config_name = os.environ.get('FLASK_ENV', 'production')
app.config.from_object(config[config_name])

# Initialize production-specific settings
if config_name == 'production':
    config[config_name].init_app(app)

if __name__ == "__main__":
    app.run()
