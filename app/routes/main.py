"""Main routes - index, dashboard, media serving"""

from flask import Blueprint, render_template, send_from_directory, current_app, redirect, url_for
from flask_login import login_required, current_user

from app.models import Expense, Budget, Goal
from app.utils import get_couple_user_ids, calculate_budget_status
from app import db
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Landing page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard with financial overview"""
    # Get user IDs (current user + partner if linked)
    user_ids = get_couple_user_ids(current_user.id)
    
    # Get recent expenses
    recent_expenses = Expense.query.filter(
        Expense.user_id.in_(user_ids)
    ).order_by(Expense.date.desc()).limit(5).all()
    
    # Get current month/year
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # Calculate total spending this month
    monthly_expenses = Expense.query.filter(
        Expense.user_id.in_(user_ids),
        db.extract('month', Expense.date) == current_month,
        db.extract('year', Expense.date) == current_year
    ).all()
    
    monthly_spending = sum(expense.amount for expense in monthly_expenses)
    
    # Calculate category spending for this month
    category_spending = {}
    for expense in monthly_expenses:
        category = expense.category
        if category in category_spending:
            category_spending[category] += expense.amount
        else:
            category_spending[category] = expense.amount
    
    # Get budget status
    budget_status = {}
    for user_id in user_ids:
        user_budget_status = calculate_budget_status(user_id, current_month, current_year)
        for category, status in user_budget_status.items():
            if category in budget_status:
                # Combine with existing data
                budget_status[category]['spent'] += status['spent']
                budget_status[category]['budgeted'] += status['budgeted']
                budget_status[category]['remaining'] = budget_status[category]['budgeted'] - budget_status[category]['spent']
                budget_status[category]['percentage'] = (budget_status[category]['spent'] / budget_status[category]['budgeted']) * 100 if budget_status[category]['budgeted'] > 0 else 0
            else:
                budget_status[category] = status
    
    # Get active goals
    goals = Goal.query.filter(
        Goal.user_id.in_(user_ids),
        Goal.is_active == True
    ).order_by(Goal.target_date.asc()).limit(3).all()
    
    # Calculate total budgets for this month
    monthly_budgets = Budget.query.filter(
        Budget.user_id.in_(user_ids),
        Budget.month == current_month,
        Budget.year == current_year
    ).all()
    
    total_budget = sum(budget.amount for budget in monthly_budgets)
    
    return render_template('dashboard.html',
                         recent_expenses=recent_expenses,
                         monthly_spending=monthly_spending,
                         category_spending=category_spending,
                         total_budget=total_budget,
                         budget_status=budget_status,
                         goals=goals)

@main_bp.route('/media/<path:filename>')
def serve_media(filename):
    """Serve media files (profile pictures, etc.)"""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
