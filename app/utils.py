"""Utility functions and helpers for the Money Management App"""

import os
import uuid
from datetime import datetime, timedelta
from collections import defaultdict
from flask import current_app
from app.models import User, Expense, Budget
from app import db

def get_expense_categories():
    """Get available expense categories with subcategories"""
    return {
        'housing': ['rent', 'mortgage', 'property_tax', 'maintenance', 'utilities'],
        'transportation': ['gas', 'public_transport', 'car_payment', 'insurance', 'maintenance'],
        'food': ['groceries', 'restaurants', 'takeout', 'coffee'],
        'utilities': ['electricity', 'water', 'internet', 'phone', 'gas'],
        'healthcare': ['insurance', 'doctor', 'pharmacy', 'dental', 'vision'],
        'entertainment': ['movies', 'concerts', 'streaming', 'games', 'hobbies'],
        'shopping': ['clothing', 'electronics', 'household', 'gifts'],
        'education': ['tuition', 'books', 'courses', 'training'],
        'insurance': ['health', 'auto', 'home', 'life'],
        'debt': ['credit_card', 'student_loan', 'personal_loan'],
        'savings': ['emergency', 'retirement', 'goals'],
        'investment': ['stocks', 'bonds', 'crypto', 'real_estate'],
        'other': ['miscellaneous']
    }

def get_couple_user_ids(user_id):
    """Get user IDs for both partners in a couple"""
    user = User.query.get(user_id)
    user_ids = [user_id]
    
    if user.partner_id:
        user_ids.append(user.partner_id)
    
    # Also check if someone has this user as their partner
    partner = User.query.filter_by(partner_id=user_id).first()
    if partner and partner.id not in user_ids:
        user_ids.append(partner.id)
    
    return user_ids

def calculate_budget_status(user_id, month, year):
    """Calculate budget status for a user in a specific month/year"""
    budgets = Budget.query.filter_by(user_id=user_id, month=month, year=year).all()
    expenses = Expense.query.filter(
        Expense.user_id == user_id,
        db.extract('month', Expense.date) == month,
        db.extract('year', Expense.date) == year
    ).all()
    
    status = {}
    for budget in budgets:
        category_expenses = [e for e in expenses if e.category == budget.category]
        total_spent = sum(e.amount for e in category_expenses)
        percentage = (total_spent / budget.amount) * 100 if budget.amount > 0 else 0
        
        status[budget.category] = {
            'budgeted': budget.amount,
            'spent': total_spent,
            'remaining': budget.amount - total_spent,
            'percentage': percentage,
            'status': 'over' if percentage > 100 else 'warning' if percentage > budget.alert_threshold else 'good'
        }
    
    return status

def allowed_file(filename):
    """Check if file has an allowed extension"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_profile_picture(file):
    """Save uploaded profile picture and return filename"""
    if file and allowed_file(file.filename):
        # Generate unique filename
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        
        # Save file
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profile_pictures')
        os.makedirs(upload_path, exist_ok=True)
        file_path = os.path.join(upload_path, unique_filename)
        file.save(file_path)
        
        return unique_filename
    return None

def delete_profile_picture(filename):
    """Delete profile picture from filesystem"""
    if filename and filename != 'default.png':
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profile_pictures', filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True
            except OSError:
                return False
    return False

def generate_savings_suggestions(user_id):
    """Generate personalized savings suggestions based on spending patterns"""
    # Get recent expenses
    thirty_days_ago = datetime.now() - timedelta(days=30)
    expenses = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.date >= thirty_days_ago.date()
    ).all()
    
    if not expenses:
        return []
    
    # Analyze spending patterns
    category_spending = defaultdict(float)
    for expense in expenses:
        category_spending[expense.category] += expense.amount
    
    suggestions = []
    
    # Entertainment spending analysis
    if category_spending['entertainment'] > 300:
        suggestions.append({
            'category': 'Entertainment',
            'suggestion': 'Consider reducing entertainment expenses. Look for free events or streaming alternatives.',
            'potential_savings': category_spending['entertainment'] * 0.2,
            'priority': 'medium'
        })
    
    # Food spending analysis
    if category_spending['food'] > 500:
        suggestions.append({
            'category': 'Food & Dining',
            'suggestion': 'Try meal planning and cooking more at home to reduce food expenses.',
            'potential_savings': category_spending['food'] * 0.15,
            'priority': 'high'
        })
    
    # Transportation analysis
    if category_spending['transportation'] > 400:
        suggestions.append({
            'category': 'Transportation',
            'suggestion': 'Consider carpooling, public transport, or combining trips to save on transportation.',
            'potential_savings': category_spending['transportation'] * 0.1,
            'priority': 'medium'
        })
    
    # Shopping analysis
    if category_spending['shopping'] > 200:
        suggestions.append({
            'category': 'Shopping',
            'suggestion': 'Set a monthly shopping budget and stick to it. Wait 24 hours before non-essential purchases.',
            'potential_savings': category_spending['shopping'] * 0.25,
            'priority': 'medium'
        })
    
    return suggestions

def generate_investment_recommendations(user_id, monthly_savings=0):
    """Generate investment recommendations based on user profile and savings"""
    recommendations = []
    
    if monthly_savings >= 100:
        recommendations.append({
            'title': 'High-Yield Savings Account',
            'description': 'Start with a safe, liquid option for emergency funds',
            'min_investment': 100,
            'risk_level': 'low',
            'expected_return': '4-5%',
            'investment_type': 'Savings Account'
        })
    
    if monthly_savings >= 500:
        recommendations.append({
            'title': 'Index Fund ETFs',
            'description': 'Diversified, low-cost investment for long-term growth',
            'min_investment': 500,
            'risk_level': 'medium',
            'expected_return': '7-10%',
            'investment_type': 'ETF'
        })
    
    if monthly_savings >= 1000:
        recommendations.append({
            'title': 'Balanced Portfolio',
            'description': 'Mix of stocks, bonds, and international funds',
            'min_investment': 1000,
            'risk_level': 'medium',
            'expected_return': '8-12%',
            'investment_type': 'Portfolio'
        })
    
    if monthly_savings >= 2000:
        recommendations.append({
            'title': 'Real Estate Investment',
            'description': 'REITs or property investment for diversification',
            'min_investment': 2000,
            'risk_level': 'medium',
            'expected_return': '8-12%',
            'investment_type': 'Real Estate Investment Trusts'
        })
    
    return recommendations

def format_currency(amount):
    """Format amount as British Pounds"""
    return f"£{amount:,.2f}"

def calculate_goal_progress(goal):
    """Calculate progress statistics for a goal"""
    progress_percentage = min((goal.current_amount / goal.target_amount) * 100, 100) if goal.target_amount > 0 else 0
    remaining_amount = max(goal.target_amount - goal.current_amount, 0)
    
    # Calculate days remaining
    today = datetime.now().date()
    days_remaining = (goal.target_date - today).days
    
    # Calculate monthly savings needed
    months_remaining = max(days_remaining / 30, 1)
    monthly_savings_needed = remaining_amount / months_remaining if months_remaining > 0 else remaining_amount
    
    return {
        'progress_percentage': progress_percentage,
        'remaining_amount': remaining_amount,
        'days_remaining': days_remaining,
        'monthly_savings_needed': monthly_savings_needed,
        'is_achievable': monthly_savings_needed <= 500  # Reasonable monthly target
    }
