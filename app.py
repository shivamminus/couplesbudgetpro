from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, FloatField, SelectField, TextAreaField, DateField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, NumberRange
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import plotly
import plotly.graph_objs as go
import plotly.express as px
import json
from collections import defaultdict
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import requests
import os
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///money_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    partner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    profile_picture = db.Column(db.String(200), nullable=True, default='default.png')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    expenses = db.relationship('Expense', backref='user', lazy=True)
    budgets = db.relationship('Budget', backref='user', lazy=True)
    goals = db.relationship('Goal', backref='user', lazy=True)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    subcategory = db.Column(db.String(50), nullable=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    is_recurring = db.Column(db.Boolean, default=False)
    frequency = db.Column(db.String(20), nullable=True)  # monthly, weekly, yearly
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    tags = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    alert_threshold = db.Column(db.Float, default=80.0)  # percentage
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0)
    target_date = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # emergency, vacation, investment, etc.
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Investment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # stocks, bonds, crypto, etc.
    amount = db.Column(db.Float, nullable=False)
    purchase_date = db.Column(db.Date, nullable=False)
    current_value = db.Column(db.Float, nullable=True)
    expected_return = db.Column(db.Float, nullable=True)
    risk_level = db.Column(db.String(20), default='medium')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PartnerRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    message = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_requests')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_requests')

# Forms
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Register')

class ExpenseForm(FlaskForm):
    amount = FloatField('Amount (£)', validators=[DataRequired(), NumberRange(min=0.01)])
    description = StringField('Description', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('housing', 'Housing'),
        ('transportation', 'Transportation'),
        ('food', 'Food & Dining'),
        ('utilities', 'Utilities'),
        ('healthcare', 'Healthcare'),
        ('entertainment', 'Entertainment'),
        ('shopping', 'Shopping'),
        ('education', 'Education'),
        ('insurance', 'Insurance'),
        ('debt', 'Debt Payments'),
        ('savings', 'Savings'),
        ('investment', 'Investment'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    subcategory = StringField('Subcategory')
    date = DateField('Date', validators=[DataRequired()], default=datetime.today)
    is_recurring = SelectField('Recurring?', choices=[('False', 'No'), ('True', 'Yes')])
    frequency = SelectField('Frequency', choices=[
        ('', 'Select Frequency'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly')
    ])
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], default='medium')
    tags = StringField('Tags (comma separated)')
    submit = SubmitField('Add Expense')

class BudgetForm(FlaskForm):
    category = SelectField('Category', choices=[
        ('housing', 'Housing'),
        ('transportation', 'Transportation'),
        ('food', 'Food & Dining'),
        ('utilities', 'Utilities'),
        ('healthcare', 'Healthcare'),
        ('entertainment', 'Entertainment'),
        ('shopping', 'Shopping'),
        ('education', 'Education'),
        ('insurance', 'Insurance'),
        ('debt', 'Debt Payments'),
        ('savings', 'Savings'),
        ('investment', 'Investment'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    amount = FloatField('Budget Amount (£)', validators=[DataRequired(), NumberRange(min=0.01)])
    month = SelectField('Month', choices=[(str(i), str(i)) for i in range(1, 13)], validators=[DataRequired()])
    year = SelectField('Year', choices=[(str(i), str(i)) for i in range(2024, 2030)], validators=[DataRequired()])
    alert_threshold = FloatField('Alert Threshold (%)', validators=[NumberRange(min=1, max=100)], default=80)
    submit = SubmitField('Set Budget')

class GoalForm(FlaskForm):
    title = StringField('Goal Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    target_amount = FloatField('Target Amount (£)', validators=[DataRequired(), NumberRange(min=0.01)])
    target_date = DateField('Target Date', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('emergency', 'Emergency Fund'),
        ('vacation', 'Vacation'),
        ('home', 'Home Purchase'),
        ('car', 'Car Purchase'),
        ('education', 'Education'),
        ('retirement', 'Retirement'),
        ('investment', 'Investment'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    submit = SubmitField('Create Goal')

class PartnerForm(FlaskForm):
    partner_username = StringField('Partner Username', validators=[DataRequired()])
    submit = SubmitField('Link Partner')

class PartnerSearchForm(FlaskForm):
    search_query = StringField('Search Users', validators=[DataRequired(), Length(min=3, max=50)])
    submit = SubmitField('Search')

class PartnerRequestForm(FlaskForm):
    partner_id = StringField('Partner ID', validators=[DataRequired()])
    submit = SubmitField('Send Request')

class ProfilePictureForm(FlaskForm):
    profile_picture = FileField('Profile Picture', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Only image files allowed!')
    ])
    submit = SubmitField('Update Picture')

class ProfileUpdateForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Update Profile')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired()])
    submit = SubmitField('Change Password')

# Helper functions
def get_expense_categories():
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
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], 'profile_pictures')
        os.makedirs(upload_path, exist_ok=True)
        file_path = os.path.join(upload_path, unique_filename)
        file.save(file_path)
        
        return unique_filename
    return None

def delete_profile_picture(filename):
    """Delete profile picture from filesystem"""
    if filename and filename != 'default.png':
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'profile_pictures', filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True
            except OSError:
                return False
    return False

def generate_savings_suggestions(user_id):
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
            'suggestion': 'Try meal planning and cooking at home more often. Reduce restaurant visits.',
            'potential_savings': category_spending['food'] * 0.15,
            'priority': 'high'
        })
    
    # Transportation analysis
    if category_spending['transportation'] > 200:
        suggestions.append({
            'category': 'Transportation',
            'suggestion': 'Consider carpooling, public transport, or combining trips to save on fuel.',
            'potential_savings': category_spending['transportation'] * 0.1,
            'priority': 'low'
        })
    
    # Shopping analysis
    if category_spending['shopping'] > 300:
        suggestions.append({
            'category': 'Shopping',
            'suggestion': 'Wait 24 hours before non-essential purchases. Use shopping lists and compare prices.',
            'potential_savings': category_spending['shopping'] * 0.25,
            'priority': 'medium'
        })
    
    return suggestions

def generate_investment_recommendations(user_id):
    user = User.query.get(user_id)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    # Calculate monthly income (estimated from expenses + savings)
    expenses = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.date >= thirty_days_ago.date()
    ).all()
    
    monthly_expenses = sum(e.amount for e in expenses)
    
    # Get savings amount
    savings_expenses = [e for e in expenses if e.category == 'savings']
    monthly_savings = sum(e.amount for e in savings_expenses) if savings_expenses else 0
    
    recommendations = []
    
    if monthly_savings > 500:
        recommendations.append({
            'type': 'Emergency Fund',
            'description': 'Build an emergency fund covering 3-6 months of expenses',
            'recommended_amount': monthly_expenses * 3,
            'risk_level': 'low',
            'expected_return': '2-3%',
            'investment_type': 'High-yield savings account'
        })
    
    if monthly_savings > 1000:
        recommendations.append({
            'type': 'Index Funds',
            'description': 'Low-cost diversified index funds for long-term growth',
            'recommended_amount': monthly_savings * 0.6,
            'risk_level': 'medium',
            'expected_return': '7-10%',
            'investment_type': 'Stock market index funds'
        })
    
    if monthly_savings > 2000:
        recommendations.append({
            'type': 'Real Estate',
            'description': 'Consider REITs for real estate exposure',
            'recommended_amount': monthly_savings * 0.2,
            'risk_level': 'medium',
            'expected_return': '8-12%',
            'investment_type': 'Real Estate Investment Trusts'
        })
    
    return recommendations

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/media/<path:filename>')
def serve_media(filename):
    """Serve media files (profile pictures, etc.)"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Username already exists')
            return render_template('register.html', form=form)
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data)
        )
        db.session.add(user)
        db.session.commit()
        flash('Registration successful')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    from datetime import datetime as dt
    current_month = dt.now().month
    current_year = dt.now().year
    
    # Get user IDs for couple (includes partner if linked)
    user_ids = get_couple_user_ids(current_user.id)
    
    # Get recent expenses for the couple
    recent_expenses = Expense.query.filter(Expense.user_id.in_(user_ids)).order_by(Expense.date.desc()).limit(10).all()
    
    # Get monthly spending by category for the couple
    monthly_expenses = Expense.query.filter(
        Expense.user_id.in_(user_ids),
        db.extract('month', Expense.date) == current_month,
        db.extract('year', Expense.date) == current_year
    ).all()
    
    category_spending = defaultdict(float)
    for expense in monthly_expenses:
        category_spending[expense.category] += expense.amount
    
    # Get budget status (combine budgets from both partners)
    budget_status = {}
    for uid in user_ids:
        user_budget_status = calculate_budget_status(uid, current_month, current_year)
        for category, status in user_budget_status.items():
            if category in budget_status:
                # Combine budgets for the same category
                budget_status[category]['budgeted'] += status['budgeted']
                budget_status[category]['spent'] += status['spent']
                budget_status[category]['remaining'] = budget_status[category]['budgeted'] - budget_status[category]['spent']
                budget_status[category]['percentage'] = (budget_status[category]['spent'] / budget_status[category]['budgeted']) * 100 if budget_status[category]['budgeted'] > 0 else 0
                budget_status[category]['status'] = 'over' if budget_status[category]['percentage'] > 100 else 'warning' if budget_status[category]['percentage'] > 80 else 'good'
            else:
                budget_status[category] = status
    
    # Get goals progress for the couple
    goals = Goal.query.filter(Goal.user_id.in_(user_ids), Goal.is_active == True).all()
    
    # Generate suggestions based on combined data
    savings_suggestions = []
    investment_recommendations = []
    for uid in user_ids:
        savings_suggestions.extend(generate_savings_suggestions(uid))
        investment_recommendations.extend(generate_investment_recommendations(uid))
    
    # Get partner info if linked
    partner = None
    if current_user.partner_id:
        partner = User.query.get(current_user.partner_id)
    else:
        partner = User.query.filter_by(partner_id=current_user.id).first()
    
    return render_template('dashboard.html',
                         recent_expenses=recent_expenses,
                         category_spending=dict(category_spending),
                         budget_status=budget_status,
                         goals=goals,
                         savings_suggestions=savings_suggestions,
                         investment_recommendations=investment_recommendations,
                         partner=partner,
                         datetime=dt)

@app.route('/expenses')
@login_required
def expenses():
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
    
    categories = get_expense_categories()
    
    # Get partner info for display
    partner = None
    if current_user.partner_id:
        partner = User.query.get(current_user.partner_id)
    else:
        partner = User.query.filter_by(partner_id=current_user.id).first()
    
    return render_template('expenses.html', expenses=expenses, categories=categories, partner=partner)

@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    form = ExpenseForm()
    if form.validate_on_submit():
        expense = Expense(
            user_id=current_user.id,
            amount=form.amount.data,
            description=form.description.data,
            category=form.category.data,
            subcategory=form.subcategory.data,
            date=form.date.data,
            is_recurring=form.is_recurring.data == 'True',
            frequency=form.frequency.data if form.is_recurring.data == 'True' else None,
            priority=form.priority.data,
            tags=form.tags.data
        )
        db.session.add(expense)
        db.session.commit()
        flash('Expense added successfully!')
        return redirect(url_for('expenses'))
    
    return render_template('add_expense.html', form=form)

@app.route('/edit_expense/<int:expense_id>', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    
    # Check if user owns this expense or if it's from their partner
    user_ids = get_couple_user_ids(current_user.id)
    if expense.user_id not in user_ids:
        flash('You can only edit your own expenses or your partner\'s expenses!')
        return redirect(url_for('expenses'))
    
    form = ExpenseForm(obj=expense)
    
    # Convert boolean to string for the form
    if expense.is_recurring:
        form.is_recurring.data = 'True'
    else:
        form.is_recurring.data = 'False'
    
    if form.validate_on_submit():
        expense.amount = form.amount.data
        expense.description = form.description.data
        expense.category = form.category.data
        expense.subcategory = form.subcategory.data
        expense.date = form.date.data
        expense.is_recurring = form.is_recurring.data == 'True'
        expense.frequency = form.frequency.data if form.is_recurring.data == 'True' else None
        expense.priority = form.priority.data
        expense.tags = form.tags.data
        
        db.session.commit()
        flash('Expense updated successfully!')
        return redirect(url_for('expenses'))
    
    return render_template('edit_expense.html', form=form, expense=expense)

@app.route('/delete_expense/<int:expense_id>')
@login_required
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    
    # Check if user owns this expense or if it's from their partner
    user_ids = get_couple_user_ids(current_user.id)
    if expense.user_id not in user_ids:
        flash('You can only delete your own expenses or your partner\'s expenses!')
        return redirect(url_for('expenses'))
    
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted successfully!')
    return redirect(url_for('expenses'))

@app.route('/budgets')
@login_required
def budgets():
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    budgets = Budget.query.filter_by(user_id=current_user.id, month=current_month, year=current_year).all()
    budget_status = calculate_budget_status(current_user.id, current_month, current_year)
    
    return render_template('budgets.html', budgets=budgets, budget_status=budget_status)

@app.route('/set_budget', methods=['GET', 'POST'])
@login_required
def set_budget():
    form = BudgetForm()
    if form.validate_on_submit():
        existing_budget = Budget.query.filter_by(
            user_id=current_user.id,
            category=form.category.data,
            month=int(form.month.data),
            year=int(form.year.data)
        ).first()
        
        if existing_budget:
            existing_budget.amount = form.amount.data
            existing_budget.alert_threshold = form.alert_threshold.data
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
        flash('Budget set successfully!')
        return redirect(url_for('budgets'))
    
    return render_template('set_budget.html', form=form)

@app.route('/goals')
@login_required
def goals():
    from datetime import datetime as dt
    
    # Get user IDs for couple (includes partner if linked)
    user_ids = get_couple_user_ids(current_user.id)
    
    active_goals = Goal.query.filter(Goal.user_id.in_(user_ids), Goal.is_active == True).all()
    completed_goals = Goal.query.filter(Goal.user_id.in_(user_ids), Goal.is_active == False).all()
    
    # Get partner info for display
    partner = None
    if current_user.partner_id:
        partner = User.query.get(current_user.partner_id)
    else:
        partner = User.query.filter_by(partner_id=current_user.id).first()
    
    return render_template('goals.html', active_goals=active_goals, completed_goals=completed_goals, partner=partner, datetime=dt)

@app.route('/add_goal', methods=['GET', 'POST'])
@login_required
def add_goal():
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
        flash('Goal created successfully!')
        return redirect(url_for('goals'))
    
    return render_template('add_goal.html', form=form)

@app.route('/analytics')
@login_required
def analytics():
    # Get user IDs for couple (includes partner if linked)
    user_ids = get_couple_user_ids(current_user.id)
    
    # Get expense data for charts (combined for couple)
    expenses = Expense.query.filter(Expense.user_id.in_(user_ids)).all()
    
    if not expenses:
        return render_template('analytics.html', 
                             spending_chart=None, 
                             trend_chart=None,
                             category_chart=None)
    
    # Create spending by category chart
    category_data = defaultdict(float)
    for expense in expenses:
        category_data[expense.category] += expense.amount
    
    fig1 = px.pie(
        values=list(category_data.values()),
        names=list(category_data.keys()),
        title='Combined Spending by Category'
    )
    spending_chart = json.dumps(fig1, cls=plotly.utils.PlotlyJSONEncoder)
    
    # Create monthly spending trend
    monthly_data = defaultdict(float)
    for expense in expenses:
        month_key = expense.date.strftime('%Y-%m')
        monthly_data[month_key] += expense.amount
    
    sorted_months = sorted(monthly_data.keys())
    amounts = [monthly_data[month] for month in sorted_months]
    
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=sorted_months, y=amounts, mode='lines+markers', name='Combined Monthly Spending'))
    fig2.update_layout(title='Combined Monthly Spending Trend', xaxis_title='Month', yaxis_title='Amount (£)')
    trend_chart = json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder)
    
    # Create category comparison chart
    fig3 = px.bar(x=list(category_data.keys()), y=list(category_data.values()), title='Combined Category Spending Comparison')
    category_chart = json.dumps(fig3, cls=plotly.utils.PlotlyJSONEncoder)
    
    return render_template('analytics.html', 
                         spending_chart=spending_chart,
                         trend_chart=trend_chart,
                         category_chart=category_chart)

@app.route('/suggestions')
@login_required
def suggestions():
    savings_suggestions = generate_savings_suggestions(current_user.id)
    investment_recommendations = generate_investment_recommendations(current_user.id)
    
    return render_template('suggestions.html',
                         savings_suggestions=savings_suggestions,
                         investment_recommendations=investment_recommendations)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    partner_form = PartnerForm()
    profile_form = ProfileUpdateForm()
    picture_form = ProfilePictureForm()
    password_form = ChangePasswordForm()
    partner = None
    
    # Get current partner if exists
    if current_user.partner_id:
        partner = User.query.get(current_user.partner_id)
    else:
        # Check if someone has this user as their partner
        partner = User.query.filter_by(partner_id=current_user.id).first()
    
    # Handle partner linking (legacy)
    if partner_form.validate_on_submit() and 'partner_submit' in request.form:
        partner_user = User.query.filter_by(username=partner_form.partner_username.data).first()
        
        if not partner_user:
            flash('Partner username not found!', 'error')
        elif partner_user.id == current_user.id:
            flash('You cannot link yourself as a partner!', 'error')
        elif current_user.partner_id == partner_user.id:
            flash('This user is already your partner!', 'error')
        else:
            # Link the partner
            current_user.partner_id = partner_user.id
            db.session.commit()
            flash(f'Successfully linked with {partner_user.username}!', 'success')
            return redirect(url_for('profile'))
    
    # Handle profile picture upload
    if picture_form.validate_on_submit() and 'picture_submit' in request.form:
        file = picture_form.profile_picture.data
        filename = save_profile_picture(file)
        
        if filename:
            # Delete old picture if not default
            old_picture = current_user.profile_picture
            if old_picture and old_picture != 'default.png':
                delete_profile_picture(old_picture)
            
            # Update user profile
            current_user.profile_picture = filename
            db.session.commit()
            flash('Profile picture updated successfully!', 'success')
        else:
            flash('Failed to upload profile picture. Please try again.', 'error')
        
        return redirect(url_for('profile'))
    
    # Handle profile update
    if profile_form.validate_on_submit() and 'profile_submit' in request.form:
        # Check if username is taken (excluding current user)
        existing_user = User.query.filter(
            User.username == profile_form.username.data,
            User.id != current_user.id
        ).first()
        
        if existing_user:
            flash('Username is already taken!', 'error')
        else:
            # Check if email is taken (excluding current user)
            existing_email = User.query.filter(
                User.email == profile_form.email.data,
                User.id != current_user.id
            ).first()
            
            if existing_email:
                flash('Email is already in use!', 'error')
            else:
                current_user.username = profile_form.username.data
                current_user.email = profile_form.email.data
                db.session.commit()
                flash('Profile updated successfully!', 'success')
                return redirect(url_for('profile'))
    
    # Handle password change
    if password_form.validate_on_submit() and 'password_submit' in request.form:
        if not check_password_hash(current_user.password_hash, password_form.current_password.data):
            flash('Current password is incorrect!', 'error')
        elif password_form.new_password.data != password_form.confirm_password.data:
            flash('New passwords do not match!', 'error')
        else:
            current_user.password_hash = generate_password_hash(password_form.new_password.data)
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('profile'))
    
    # Pre-populate profile form with current data
    profile_form.username.data = current_user.username
    profile_form.email.data = current_user.email
    
    return render_template('profile.html', 
                         partner_form=partner_form, 
                         profile_form=profile_form,
                         picture_form=picture_form,
                         password_form=password_form,
                         partner=partner)

@app.route('/unlink_partner')
@login_required
def unlink_partner():
    current_user.partner_id = None
    db.session.commit()
    flash('Partner unlinked successfully!')
    return redirect(url_for('profile'))

@app.route('/search_partners', methods=['GET', 'POST'])
@login_required
def search_partners():
    form = PartnerSearchForm()
    users = []
    
    if form.validate_on_submit():
        search_query = form.search_query.data
        # Search users by username or email
        users = User.query.filter(
            db.or_(
                User.username.contains(search_query),
                User.email.contains(search_query)
            ),
            User.id != current_user.id  # Exclude current user
        ).limit(10).all()
        
        if not users:
            flash('No users found matching your search.')
    
    # Get pending requests
    pending_sent = PartnerRequest.query.filter_by(
        sender_id=current_user.id, 
        status='pending'
    ).all()
    
    pending_received = PartnerRequest.query.filter_by(
        receiver_id=current_user.id, 
        status='pending'
    ).all()
    
    return render_template('search_partners.html', 
                         form=form, 
                         users=users, 
                         pending_sent=pending_sent,
                         pending_received=pending_received)

@app.route('/send_partner_request/<int:user_id>')
@login_required
def send_partner_request(user_id):
    target_user = User.query.get_or_404(user_id)
    
    if target_user.id == current_user.id:
        flash('You cannot send a partner request to yourself!')
        return redirect(url_for('search_partners'))
    
    if current_user.partner_id or User.query.filter_by(partner_id=current_user.id).first():
        flash('You already have a partner!')
        return redirect(url_for('search_partners'))
    
    # Check if request already exists
    existing_request = PartnerRequest.query.filter_by(
        sender_id=current_user.id,
        receiver_id=target_user.id,
        status='pending'
    ).first()
    
    if existing_request:
        flash('You have already sent a partner request to this user!')
        return redirect(url_for('search_partners'))
    
    # Check if reverse request exists
    reverse_request = PartnerRequest.query.filter_by(
        sender_id=target_user.id,
        receiver_id=current_user.id,
        status='pending'
    ).first()
    
    if reverse_request:
        flash('This user has already sent you a partner request! Check your pending requests.')
        return redirect(url_for('search_partners'))
    
    # Create new partner request
    partner_request = PartnerRequest(
        sender_id=current_user.id,
        receiver_id=target_user.id,
        message=f'{current_user.username} would like to link as financial partners.'
    )
    
    db.session.add(partner_request)
    db.session.commit()
    
    flash(f'Partner request sent to {target_user.username}!')
    return redirect(url_for('search_partners'))

@app.route('/respond_partner_request/<int:request_id>/<action>')
@login_required
def respond_partner_request(request_id, action):
    partner_request = PartnerRequest.query.get_or_404(request_id)
    
    if partner_request.receiver_id != current_user.id:
        flash('You can only respond to requests sent to you!')
        return redirect(url_for('search_partners'))
    
    if partner_request.status != 'pending':
        flash('This request has already been processed!')
        return redirect(url_for('search_partners'))
    
    if action == 'accept':
        if current_user.partner_id or User.query.filter_by(partner_id=current_user.id).first():
            flash('You already have a partner!')
            partner_request.status = 'rejected'
        else:
            # Link the partners
            current_user.partner_id = partner_request.sender_id
            partner_request.sender.partner_id = current_user.id
            partner_request.status = 'accepted'
            
            # Cancel any other pending requests for both users
            PartnerRequest.query.filter(
                db.or_(
                    db.and_(PartnerRequest.sender_id == current_user.id, PartnerRequest.status == 'pending'),
                    db.and_(PartnerRequest.receiver_id == current_user.id, PartnerRequest.status == 'pending', PartnerRequest.id != request_id),
                    db.and_(PartnerRequest.sender_id == partner_request.sender_id, PartnerRequest.status == 'pending', PartnerRequest.id != request_id),
                    db.and_(PartnerRequest.receiver_id == partner_request.sender_id, PartnerRequest.status == 'pending')
                )
            ).update({'status': 'rejected'})
            
            flash(f'You are now linked with {partner_request.sender.username}!')
    
    elif action == 'reject':
        partner_request.status = 'rejected'
        flash(f'Partner request from {partner_request.sender.username} rejected.')
    
    db.session.commit()
    return redirect(url_for('search_partners'))

@app.route('/cancel_partner_request/<int:request_id>')
@login_required
def cancel_partner_request(request_id):
    partner_request = PartnerRequest.query.get_or_404(request_id)
    
    if partner_request.sender_id != current_user.id:
        flash('You can only cancel requests you sent!')
        return redirect(url_for('search_partners'))
    
    if partner_request.status != 'pending':
        flash('This request cannot be cancelled!')
        return redirect(url_for('search_partners'))
    
    db.session.delete(partner_request)
    db.session.commit()
    
    flash(f'Partner request to {partner_request.receiver.username} cancelled.')
    return redirect(url_for('search_partners'))

@app.before_request
def create_tables():
    """Create database tables before first request"""
    if not hasattr(app, 'tables_created'):
        try:
            db.create_all()
            app.tables_created = True
            print("Database tables created successfully!")
        except Exception as e:
            print(f"Error creating database tables: {e}")

if __name__ == '__main__':
    with app.app_context():
        try:
            # Drop all tables and recreate them (for development)
            db.create_all()
            print("Database initialized successfully!")
        except Exception as e:
            print(f"Error initializing database: {e}")
    app.run(debug=True)
