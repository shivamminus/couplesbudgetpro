"""Test authentication functionality"""
import unittest
from tests import TestCase
from app.models import User
from app import db

class AuthTestCase(TestCase):
    """Test authentication functionality"""
    
    def test_user_registration(self):
        """Test user registration"""
        response = self.client.post('/auth/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'password2': 'password123'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Check user was created in database
        user = User.query.filter_by(email='newuser@example.com').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'newuser')
    
    def test_user_registration_duplicate_email(self):
        """Test registration with duplicate email"""
        # Create first user
        self.create_user(email='duplicate@example.com')
        
        # Try to register with same email
        response = self.client.post('/auth/register', data={
            'username': 'newuser',
            'email': 'duplicate@example.com',
            'password': 'password123',
            'password2': 'password123'
        })
        
        self.assertIn(b'Please use a different email address', response.data)
    
    def test_user_login_valid_credentials(self):
        """Test login with valid credentials"""
        user = self.create_user()
        
        response = self.login(email=user.email, password='password123')
        self.assertEqual(response.status_code, 200)
    
    def test_user_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        user = self.create_user()
        
        response = self.client.post('/auth/login', data={
            'email': user.email,
            'password': 'wrongpassword'
        })
        
        self.assertIn(b'Invalid username or password', response.data)
    
    def test_user_logout(self):
        """Test user logout"""
        user = self.create_user()
        self.login(email=user.email)
        
        response = self.logout()
        self.assertEqual(response.status_code, 200)
    
    def test_password_hashing(self):
        """Test password hashing"""
        user = self.create_user()
        
        # Password should be hashed
        self.assertNotEqual(user.password_hash, 'password123')
        
        # Check password verification
        self.assertTrue(user.check_password('password123'))
        self.assertFalse(user.check_password('wrongpassword'))
    
    def test_protected_route_requires_login(self):
        """Test that protected routes require authentication"""
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
    def test_authenticated_user_can_access_dashboard(self):
        """Test authenticated user can access dashboard"""
        user = self.create_user()
        self.login(email=user.email)
        
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
