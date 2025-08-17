"""Database models for the Money Management App"""

from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    """User model for authentication and profile"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256))
    partner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    profile_picture = db.Column(db.String(200), nullable=True, default='default.png')
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    expenses = db.relationship('Expense', backref='user', lazy=True, cascade='all, delete-orphan')
    budgets = db.relationship('Budget', backref='user', lazy=True, cascade='all, delete-orphan')
    goals = db.relationship('Goal', backref='user', lazy=True, cascade='all, delete-orphan')
    investments = db.relationship('Investment', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_partner(self):
        """Get partner user object"""
        if self.partner_id:
            return User.query.get(self.partner_id)
        return User.query.filter_by(partner_id=self.id).first()
    
    def __repr__(self):
        return f'<User {self.username}>'

class Expense(db.Model):
    """Expense model for tracking spending"""
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
    
    def __repr__(self):
        return f'<Expense {self.description}: £{self.amount}>'

class Budget(db.Model):
    """Budget model for setting spending limits"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    alert_threshold = db.Column(db.Float, default=80.0)  # percentage
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Budget {self.category}: £{self.amount}>'

class Goal(db.Model):
    """Goal model for financial targets"""
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
    
    @property
    def progress_percentage(self):
        """Calculate completion percentage"""
        if self.target_amount > 0:
            return min((self.current_amount / self.target_amount) * 100, 100)
        return 0
    
    def __repr__(self):
        return f'<Goal {self.title}: £{self.current_amount}/£{self.target_amount}>'

class Investment(db.Model):
    """Investment model for tracking investments"""
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
    
    @property
    def return_percentage(self):
        """Calculate return percentage"""
        if self.amount > 0 and self.current_value:
            return ((self.current_value - self.amount) / self.amount) * 100
        return 0
    
    def __repr__(self):
        return f'<Investment {self.name}: £{self.amount}>'

class PartnerRequest(db.Model):
    """Partner request model for linking couples"""
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    message = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_requests')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_requests')
    
    def __repr__(self):
        return f'<PartnerRequest from {self.sender_id} to {self.receiver_id}: {self.status}>'
