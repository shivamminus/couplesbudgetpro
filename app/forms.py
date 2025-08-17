"""Forms for the Money Management App"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, FloatField, SelectField, TextAreaField, DateField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, NumberRange
from datetime import datetime

class LoginForm(FlaskForm):
    """User login form"""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    """User registration form"""
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Register')

class ExpenseForm(FlaskForm):
    """Form for adding/editing expenses"""
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
    """Form for setting budgets"""
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
    """Form for creating goals"""
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
    """Form for partner linking (legacy)"""
    partner_username = StringField('Partner Username', validators=[DataRequired()])
    submit = SubmitField('Link Partner')

class PartnerSearchForm(FlaskForm):
    """Form for searching partners"""
    search_query = StringField('Search Users', validators=[DataRequired(), Length(min=3, max=50)])
    submit = SubmitField('Search')

class PartnerRequestForm(FlaskForm):
    """Form for sending partner requests"""
    partner_id = StringField('Partner ID', validators=[DataRequired()])
    submit = SubmitField('Send Request')

class ProfilePictureForm(FlaskForm):
    """Form for uploading profile pictures"""
    profile_picture = FileField('Profile Picture', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Only image files allowed!')
    ])
    submit = SubmitField('Update Picture')

class ProfileUpdateForm(FlaskForm):
    """Form for updating profile information"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Update Profile')

class ChangePasswordForm(FlaskForm):
    """Form for changing password"""
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired()])
    submit = SubmitField('Change Password')

class InvestmentForm(FlaskForm):
    """Form for adding investments"""
    name = StringField('Investment Name', validators=[DataRequired()])
    type = SelectField('Investment Type', choices=[
        ('stocks', 'Stocks'),
        ('bonds', 'Bonds'),
        ('crypto', 'Cryptocurrency'),
        ('real_estate', 'Real Estate'),
        ('mutual_funds', 'Mutual Funds'),
        ('etf', 'ETF'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    amount = FloatField('Investment Amount (£)', validators=[DataRequired(), NumberRange(min=0.01)])
    purchase_date = DateField('Purchase Date', validators=[DataRequired()], default=datetime.today)
    expected_return = FloatField('Expected Return (%)', validators=[NumberRange(min=0, max=100)])
    risk_level = SelectField('Risk Level', choices=[
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk')
    ], default='medium')
    submit = SubmitField('Add Investment')
