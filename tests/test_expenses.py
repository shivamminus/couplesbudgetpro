"""Test expense management functionality"""
import unittest
from datetime import date
from tests import TestCase
from app.models import User, Expense
from app import db

class ExpenseTestCase(TestCase):
    """Test expense management functionality"""
    
    def test_create_expense(self):
        """Test creating a new expense"""
        user = self.create_user()
        self.login(email=user.email)
        
        response = self.client.post('/expenses/add', data={
            'amount': 50.00,
            'description': 'Test expense',
            'category': 'Food',
            'date': date.today().strftime('%Y-%m-%d'),
            'priority': 'medium'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Check expense was created
        expense = Expense.query.first()
        self.assertIsNotNone(expense)
        self.assertEqual(expense.amount, 50.00)
        self.assertEqual(expense.description, 'Test expense')
        self.assertEqual(expense.user_id, user.id)
    
    def test_view_expenses(self):
        """Test viewing expense list"""
        user = self.create_user()
        
        # Create test expenses
        expense1 = Expense(
            amount=25.50,
            description='Lunch',
            category='Food',
            user_id=user.id,
            date=date.today()
        )
        expense2 = Expense(
            amount=100.00,
            description='Gas',
            category='Transport',
            user_id=user.id,
            date=date.today()
        )
        db.session.add(expense1)
        db.session.add(expense2)
        db.session.commit()
        
        self.login(email=user.email)
        response = self.client.get('/expenses/')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Lunch', response.data)
        self.assertIn(b'Gas', response.data)
    
    def test_edit_expense(self):
        """Test editing an expense"""
        user = self.create_user()
        expense = Expense(
            amount=25.50,
            description='Original description',
            category='Food',
            user_id=user.id,
            date=date.today()
        )
        db.session.add(expense)
        db.session.commit()
        
        self.login(email=user.email)
        
        response = self.client.post(f'/expenses/edit/{expense.id}', data={
            'amount': 30.00,
            'description': 'Updated description',
            'category': 'Food',
            'date': date.today().strftime('%Y-%m-%d'),
            'priority': 'high'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Check expense was updated
        updated_expense = Expense.query.get(expense.id)
        self.assertEqual(updated_expense.amount, 30.00)
        self.assertEqual(updated_expense.description, 'Updated description')
    
    def test_delete_expense(self):
        """Test deleting an expense"""
        user = self.create_user()
        expense = Expense(
            amount=25.50,
            description='To be deleted',
            category='Food',
            user_id=user.id,
            date=date.today()
        )
        db.session.add(expense)
        db.session.commit()
        expense_id = expense.id
        
        self.login(email=user.email)
        
        response = self.client.post(f'/expenses/delete/{expense_id}', 
                                  follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Check expense was deleted
        deleted_expense = Expense.query.get(expense_id)
        self.assertIsNone(deleted_expense)
    
    def test_expense_belongs_to_user(self):
        """Test that users can only access their own expenses"""
        user1 = self.create_user(email='user1@example.com')
        user2 = User(username='user2', email='user2@example.com')
        user2.set_password('password123')
        db.session.add(user2)
        db.session.commit()
        
        # Create expense for user1
        expense = Expense(
            amount=25.50,
            description='User1 expense',
            category='Food',
            user_id=user1.id,
            date=date.today()
        )
        db.session.add(expense)
        db.session.commit()
        
        # Login as user2 and try to access user1's expense
        self.login(email='user2@example.com')
        response = self.client.get(f'/expenses/edit/{expense.id}')
        
        # Should not be able to access other user's expense
        self.assertEqual(response.status_code, 404)
