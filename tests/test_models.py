"""Test models functionality"""
import unittest
from datetime import date, datetime
from tests import TestCase
from app.models import User, Expense, Budget, Goal, PartnerRequest
from app import db

class ModelTestCase(TestCase):
    """Test database models"""
    
    def test_user_model(self):
        """Test User model functionality"""
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        
        # Test password hashing
        self.assertTrue(user.check_password('password123'))
        self.assertFalse(user.check_password('wrongpassword'))
        
        # Test string representation
        self.assertEqual(str(user), '<User testuser>')
        
        db.session.add(user)
        db.session.commit()
        
        # Test database persistence
        retrieved_user = User.query.filter_by(email='test@example.com').first()
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.username, 'testuser')
    
    def test_expense_model(self):
        """Test Expense model functionality"""
        user = self.create_user()
        
        expense = Expense(
            amount=50.75,
            description='Test expense',
            category='Food',
            user_id=user.id,
            date=date.today(),
            priority='medium'
        )
        
        db.session.add(expense)
        db.session.commit()
        
        # Test relationships
        self.assertEqual(expense.user.username, 'testuser')
        self.assertEqual(user.expenses[0].description, 'Test expense')
        
        # Test string representation
        self.assertEqual(str(expense), '<Expense Test expense: £50.75>')
    
    def test_budget_model(self):
        """Test Budget model functionality"""
        user = self.create_user()
        
        budget = Budget(
            category='Food',
            amount=500.00,
            month=12,
            year=2023,
            user_id=user.id
        )
        
        db.session.add(budget)
        db.session.commit()
        
        # Test relationships
        self.assertEqual(budget.user.username, 'testuser')
        
        # Test string representation
        self.assertEqual(str(budget), '<Budget Food: £500.0 for 12/2023>')
    
    def test_goal_model(self):
        """Test Goal model functionality"""
        user = self.create_user()
        target_date = date.today()
        
        goal = Goal(
            title='Test Goal',
            description='A test goal',
            target_amount=1000.00,
            current_amount=250.00,
            target_date=target_date,
            category='savings',
            user_id=user.id
        )
        
        db.session.add(goal)
        db.session.commit()
        
        # Test relationships
        self.assertEqual(goal.user.username, 'testuser')
        
        # Test progress calculation (should be implemented in model or utils)
        progress_percentage = (goal.current_amount / goal.target_amount) * 100
        self.assertEqual(progress_percentage, 25.0)
        
        # Test string representation
        self.assertEqual(str(goal), '<Goal Test Goal: £250.0/£1000.0>')
    
    def test_partner_request_model(self):
        """Test PartnerRequest model functionality"""
        sender = self.create_user(username='sender', email='sender@example.com')
        receiver = User(username='receiver', email='receiver@example.com')
        receiver.set_password('password123')
        db.session.add(receiver)
        db.session.commit()
        
        partner_request = PartnerRequest(
            sender_id=sender.id,
            receiver_id=receiver.id,
            message='Let\'s be financial partners!',
            status='pending'
        )
        
        db.session.add(partner_request)
        db.session.commit()
        
        # Test relationships
        self.assertEqual(partner_request.sender.username, 'sender')
        self.assertEqual(partner_request.receiver.username, 'receiver')
        
        # Test string representation
        self.assertIn('sender', str(partner_request))
        self.assertIn('receiver', str(partner_request))
    
    def test_user_partner_relationship(self):
        """Test user partner linking functionality"""
        user1 = self.create_user(username='user1', email='user1@example.com')
        user2 = User(username='user2', email='user2@example.com')
        user2.set_password('password123')
        db.session.add(user2)
        db.session.commit()
        
        # Link users as partners
        user1.partner_id = user2.id
        user2.partner_id = user1.id
        db.session.commit()
        
        # Test partner relationship
        self.assertEqual(user1.partner_id, user2.id)
        self.assertEqual(user2.partner_id, user1.id)
