"""Budget-related routes"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime

from app.models import Budget, Expense
from app.forms import BudgetForm
from app.utils import get_couple_user_ids, calculate_budget_status
from app import db

budgets_bp = Blueprint('budgets', __name__)

@budgets_bp.route('/')
@login_required
def list_budgets():
    """List all budgets"""
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    user_ids = get_couple_user_ids(current_user.id)
    budgets = Budget.query.filter(
        Budget.user_id.in_(user_ids),
        Budget.month == current_month,
        Budget.year == current_year
    ).all()
    
    # Calculate budget status
    budget_status = {}
    for user_id in user_ids:
        user_status = calculate_budget_status(user_id, current_month, current_year)
        budget_status.update(user_status)
    
    return render_template('budgets.html', budgets=budgets, budget_status=budget_status)

@budgets_bp.route('/set', methods=['GET', 'POST'])
@login_required
def set_budget():
    """Set new budget"""
    form = BudgetForm()
    
    if form.validate_on_submit():
        # Check if budget already exists for this category/month/year
        existing_budget = Budget.query.filter_by(
            user_id=current_user.id,
            category=form.category.data,
            month=int(form.month.data),
            year=int(form.year.data)
        ).first()
        
        if existing_budget:
            flash('Budget for this category and month already exists!', 'error')
        else:
            budget = Budget(
                user_id=current_user.id,
                category=form.category.data,
                amount=form.amount.data,
                month=int(form.month.data),
                year=int(form.year.data),
                alert_threshold=form.alert_threshold.data
            )
            
            db.session.add(budget)
            db.session.commit()
            
            flash(f'Budget for {form.category.data} set successfully!', 'success')
            return redirect(url_for('budgets.list_budgets'))
    
    return render_template('set_budget.html', form=form)
