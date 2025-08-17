"""Test configuration and fixtures"""
import unittest
import os
import tempfile
from app import create_app, db
from app.models import User, Expense, Budget, Goal, Investment, PartnerRequest

class TestCase(unittest.TestCase):
    """Base test case class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        # Create test app with in-memory database
        os.environ['FLASK_CONFIG'] = 'testing'
        self.app = create_app('testing')
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['TESTING'] = True
        
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        self.client = self.app.test_client()
        
        # Create all database tables
        db.create_all()
        
    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def create_user(self, username='testuser', email='test@example.com', password='password123'):
        """Helper method to create a test user"""
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user
    
    def login(self, email='test@example.com', password='password123'):
        """Helper method to log in a user"""
        return self.client.post('/auth/login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)
    
    def logout(self):
        """Helper method to log out"""
        return self.client.get('/auth/logout', follow_redirects=True)
