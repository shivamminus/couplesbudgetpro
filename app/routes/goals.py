"""Goal-related routes"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.models import Goal
from app.forms import GoalForm
from app.utils import get_couple_user_ids, calculate_goal_progress
from app import db

goals_bp = Blueprint('goals', __name__)

@goals_bp.route('/')
@login_required
def list_goals():
    """List all goals"""
    user_ids = get_couple_user_ids(current_user.id)
    goals = Goal.query.filter(
        Goal.user_id.in_(user_ids),
        Goal.is_active == True
    ).order_by(Goal.target_date.asc()).all()
    
    # Calculate progress for each goal
    goals_with_progress = []
    for goal in goals:
        progress = calculate_goal_progress(goal)
        goals_with_progress.append({
            'goal': goal,
            'progress': progress
        })
    
    return render_template('goals.html', goals_with_progress=goals_with_progress)

@goals_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_goal():
    """Add new goal"""
    form = GoalForm()
    
    if form.validate_on_submit():
        goal = Goal(
            user_id=current_user.id,
            title=form.title.data,
            description=form.description.data,
            target_amount=form.target_amount.data,
            target_date=form.target_date.data,
            category=form.category.data
        )
        
        db.session.add(goal)
        db.session.commit()
        
        flash(f'Goal "{goal.title}" created successfully!', 'success')
        return redirect(url_for('goals.list_goals'))
    
    return render_template('add_goal.html', form=form)

@goals_bp.route('/update/<int:goal_id>', methods=['POST'])
@login_required
def update_goal_progress(goal_id):
    """Update goal progress"""
    goal = Goal.query.get_or_404(goal_id)
    
    # Check if user owns this goal
    if goal.user_id != current_user.id:
        flash('You can only update your own goals!', 'error')
        return redirect(url_for('goals.list_goals'))
    
    amount = float(request.form.get('amount', 0))
    if amount > 0:
        goal.current_amount += amount
        if goal.current_amount > goal.target_amount:
            goal.current_amount = goal.target_amount
            goal.is_active = False
            flash(f'Congratulations! Goal "{goal.title}" completed!', 'success')
        else:
            flash(f'Added £{amount:.2f} to goal "{goal.title}"', 'success')
        
        db.session.commit()
    
    return redirect(url_for('goals.list_goals'))
