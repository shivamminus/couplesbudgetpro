#!/usr/bin/env python3
"""
Main application entry point for CouplesBudget Pro
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

from app import create_app, db
from app.models import User, Expense, Budget, Goal, Investment, PartnerRequest
from flask_migrate import upgrade

# Create application instance
app = create_app(os.getenv('FLASK_CONFIG') or 'default')

@app.shell_context_processor
def make_shell_context():
    """Make database models available in Flask shell"""
    return {
        'db': db,
        'User': User,
        'Expense': Expense,
        'Budget': Budget,
        'Goal': Goal,
        'Investment': Investment,
        'PartnerRequest': PartnerRequest
    }

@app.cli.command()
def deploy():
    """Run deployment tasks"""
    # Create or upgrade database
    upgrade()

if __name__ == '__main__':
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        print("Database tables created successfully!")
    
    print("Starting CouplesBudget Pro...")
    print("Access the application at: http://localhost:5000")
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=app.config.get('DEBUG', False)
    )
