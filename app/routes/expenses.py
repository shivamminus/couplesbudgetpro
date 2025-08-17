"""Expense-related routes"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime

from app.models import Expense, User
from app.forms import ExpenseForm
from app.utils import get_couple_user_ids
from app import db

expenses_bp = Blueprint('expenses', __name__)

@expenses_bp.route('/')
@login_required
def list_expenses():
    """List all expenses"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    
    # Get user IDs for couple (includes partner if linked)
    user_ids = get_couple_user_ids(current_user.id)
    
    query = Expense.query.filter(Expense.user_id.in_(user_ids))
    if category:
        query = query.filter_by(category=category)
    
    expenses = query.order_by(Expense.date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get categories for filtering (you might need to implement this function)
    categories = ['Food', 'Transport', 'Entertainment', 'Bills', 'Shopping', 'Health', 'Other']
    
    # Get partner info for display
    partner = None
    if current_user.partner_id:
        partner = User.query.get(current_user.partner_id)
    else:
        partner = User.query.filter_by(partner_id=current_user.id).first()
    
    return render_template('expenses.html', expenses=expenses, categories=categories, partner=partner)

@expenses_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    """Add new expense"""
    form = ExpenseForm()
    
    if form.validate_on_submit():
        expense = Expense(
            user_id=current_user.id,
            amount=form.amount.data,
            description=form.description.data,
            category=form.category.data,
            subcategory=form.subcategory.data or None,
            date=form.date.data,
            is_recurring=form.is_recurring.data == 'True',
            frequency=form.frequency.data if form.is_recurring.data == 'True' else None,
            priority=form.priority.data,
            tags=form.tags.data or None
        )
        
        db.session.add(expense)
        db.session.commit()
        
        flash(f'Expense "{expense.description}" added successfully!', 'success')
        return redirect(url_for('expenses.list_expenses'))
    
    return render_template('add_expense.html', form=form)

@expenses_bp.route('/edit/<int:expense_id>', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    """Edit existing expense"""
    expense = Expense.query.get_or_404(expense_id)
    
    # Check if user owns this expense
    if expense.user_id != current_user.id:
        flash('You can only edit your own expenses!', 'error')
        return redirect(url_for('expenses.list_expenses'))
    
    form = ExpenseForm(obj=expense)
    
    # Convert boolean to string for form
    form.is_recurring.data = 'True' if expense.is_recurring else 'False'
    
    if form.validate_on_submit():
        expense.amount = form.amount.data
        expense.description = form.description.data
        expense.category = form.category.data
        expense.subcategory = form.subcategory.data or None
        expense.date = form.date.data
        expense.is_recurring = form.is_recurring.data == 'True'
        expense.frequency = form.frequency.data if form.is_recurring.data == 'True' else None
        expense.priority = form.priority.data
        expense.tags = form.tags.data or None
        
        db.session.commit()
        
        flash(f'Expense "{expense.description}" updated successfully!', 'success')
        return redirect(url_for('expenses.list_expenses'))
    
    return render_template('edit_expense.html', form=form, expense=expense)

@expenses_bp.route('/delete/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    """Delete expense"""
    expense = Expense.query.get_or_404(expense_id)
    
    # Check if user owns this expense
    if expense.user_id != current_user.id:
        flash('You can only delete your own expenses!', 'error')
        return redirect(url_for('expenses.list_expenses'))
    
    description = expense.description
    db.session.delete(expense)
    db.session.commit()
    
    flash(f'Expense "{description}" deleted successfully!', 'success')
    return redirect(url_for('expenses.list_expenses'))
