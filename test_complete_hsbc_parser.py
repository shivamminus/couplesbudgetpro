#!/usr/bin/env python3
"""Test the completely rewritten HSBC parser to capture ALL transactions"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.pdf_processor import process_pdf_statement

def main():
    # Test with the HSBC statement
    pdf_path = "f:/development/moneymanagementapp/2025-08-29_Statement.pdf"
    
    print("Testing the COMPLETE HSBC parser...")
    print("=" * 60)
    
    try:
        # Read PDF as bytes
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        result = process_pdf_statement(pdf_content, 'hsbc', statement_month=None, statement_year=None)
        
        if result['success']:
            transactions = result['transactions']
            
            print(f"\n✅ SUCCESSFULLY PARSED {len(transactions)} TRANSACTIONS")
            print("\nCOMPLETE TRANSACTION LIST:")
            print("-" * 80)
            
            # Sort transactions by date for easier review
            sorted_transactions = sorted(transactions, key=lambda x: x['date'])
            
            total_amount = 0
            for i, transaction in enumerate(sorted_transactions, 1):
                date_str = transaction['date'].strftime('%d %b %y')
                amount = transaction['amount']
                direction = transaction['type']
                hsbc_type = transaction.get('hsbc_type', 'UNKNOWN')
                description = transaction['description']
                
                if direction == 'income':
                    total_amount += amount
                    sign = "+"
                else:
                    total_amount -= amount
                    sign = "-"
                
                print(f"{i:2d}. {date_str} | {hsbc_type:4s} | {sign}£{amount:8.2f} | {description}")
            
            print("-" * 80)
            print(f"TOTAL NET MOVEMENT: £{total_amount:.2f}")
            print(f"TRANSACTION COUNT: {len(transactions)}")
            
            # Group by transaction type
            print("\nTRANSACTION TYPES SUMMARY:")
            type_counts = {}
            for t in transactions:
                hsbc_type = t.get('hsbc_type', 'UNKNOWN')
                if hsbc_type not in type_counts:
                    type_counts[hsbc_type] = 0
                type_counts[hsbc_type] += 1
            
            for trans_type, count in sorted(type_counts.items()):
                print(f"  {trans_type}: {count} transactions")
            
            # Check for specific missing transactions we know about
            print("\nCHECKING FOR SPECIFIC TRANSACTIONS:")
            descriptions = [t['description'].lower() for t in transactions]
            
            checks = [
                ('Amazon Prime', any('amazon' in desc and 'prime' in desc for desc in descriptions)),
                ('Apple.com', any('apple' in desc for desc in descriptions)),
                ('ATM Cash', any('cash' in desc for desc in descriptions)),
                ('Circolo Popolare', any('circolo' in desc or 'popolare' in desc for desc in descriptions)),
                ('Ristorante Venezia', any('ristorante' in desc or 'venezia' in desc for desc in descriptions)),
                ('Revolut transactions', any('revolut' in desc for desc in descriptions)),
                ('FCA Stratford', any('fca' in desc and 'stratford' in desc for desc in descriptions)),
            ]
            
            for check_name, found in checks:
                status = "✅ FOUND" if found else "❌ MISSING"
                print(f"  {status}: {check_name}")
            
        else:
            print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()