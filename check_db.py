#!/usr/bin/env python3

from app import app, db, User, Expense, Budget, Goal, Investment, PartnerRequest
import sqlite3

def check_database():
    with app.app_context():
        # Check if all tables exist
        print('=== Database Tables ===')
        conn = sqlite3.connect('couples_budget.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        for table in tables:
            print(f'Table: {table[0]}')
        
        print('\n=== Table Schemas ===')
        for table in tables:
            table_name = table[0]
            cursor.execute(f'PRAGMA table_info({table_name});')
            columns = cursor.fetchall()
            print(f'\n{table_name} columns:')
            for col in columns:
                print(f'  {col[1]} {col[2]} (PK: {col[5]}, NotNull: {col[3]}, Default: {col[4]})')
        
        print('\n=== Foreign Key Constraints ===')
        for table in tables:
            table_name = table[0]
            cursor.execute(f'PRAGMA foreign_key_list({table_name});')
            fks = cursor.fetchall()
            if fks:
                print(f'\n{table_name} foreign keys:')
                for fk in fks:
                    print(f'  {fk[3]} -> {fk[2]}.{fk[4]}')
        
        print('\n=== Sample Data Check ===')
        
        # Check users
        users = User.query.all()
        print(f'\nUsers in database: {len(users)}')
        for user in users:
            print(f'  User {user.id}: {user.username} ({user.email})')
            
        # Check expenses
        expenses = Expense.query.all()
        print(f'\nExpenses in database: {len(expenses)}')
        for expense in expenses[:5]:  # Show first 5
            print(f'  Expense {expense.id}: £{expense.amount} - {expense.description} (User: {expense.user_id})')
            
        # Check partner relationships
        partner_requests = PartnerRequest.query.all()
        print(f'\nPartner requests in database: {len(partner_requests)}')
        for req in partner_requests:
            status_text = "Accepted" if req.is_accepted else "Pending"
            print(f'  Request {req.id}: User {req.requester_id} -> User {req.requested_id} ({status_text})')
        
        conn.close()

if __name__ == "__main__":
    check_database()
