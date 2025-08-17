#!/usr/bin/python3.10
"""
WSGI configuration for PythonAnywhere deployment
"""
import sys
import os

# Add your project directory to sys.path
path = '/home/yourusername/couplesbudgetpro'  # Replace 'yourusername' with your actual username
if path not in sys.path:
    sys.path.insert(0, path)

# Load environment variables from .env file
from dotenv import load_dotenv
dotenv_path = os.path.join(path, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# Import your Flask app
from run import app as application

if __name__ == "__main__":
    application.run()
