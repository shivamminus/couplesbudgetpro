"""Test script for PDF processing functionality"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.pdf_processor import BankStatementProcessor
from datetime import datetime

def test_text_parsing():
    """Test the text parsing functionality with sample bank statement text"""
    
    # Sample bank statement text (typical format)
    sample_text = """
BANK STATEMENT
Account Number: 12345678
Statement Period: January 2024

Date        Description                     Amount      Balance
01/01/2024  Opening Balance                            1000.00
02/01/2024  TESCO STORES 1234               25.50       974.50
03/01/2024  ATM WITHDRAWAL LONDON           50.00       924.50
04/01/2024  SALARY PAYMENT                 2500.00     3424.50
05/01/2024  SHELL PETROL STATION            45.80       3378.70
06/01/2024  AMAZON MARKETPLACE              19.99       3358.71
07/01/2024  MORTGAGE PAYMENT               1200.00      2158.71
08/01/2024  COUNCIL TAX DIRECT DEBIT        125.00      2033.71
09/01/2024  NETFLIX SUBSCRIPTION            12.99       2020.72
10/01/2024  WAITROSE SUPERMARKET            67.45       1953.27
"""
    
    print("Testing PDF text parsing with sample data...")
    print("=" * 50)
    
    # Test different banks
    banks_to_test = ['generic', 'hsbc', 'barclays', 'other']
    
    for bank_name in banks_to_test:
        print(f"\nTesting with bank: {bank_name}")
        print("-" * 30)
        
        processor = BankStatementProcessor(bank_name)
        transactions = processor.parse_transactions(sample_text)
        
        print(f"Found {len(transactions)} transactions:")
        
        for i, trans in enumerate(transactions, 1):
            category, confidence = processor.categorize_transaction(trans['description'])
            cleaned_desc = processor._clean_description(trans['description'])
            
            print(f"{i}. {trans['date'].strftime('%d/%m/%Y')} - {trans['description']}")
            print(f"   Amount: £{trans['amount']:.2f} ({trans['type']})")
            print(f"   Suggested Category: {category} (confidence: {confidence:.1f})")
            print(f"   Cleaned Description: {cleaned_desc}")
            print()

def test_categorization():
    """Test the auto-categorization functionality"""
    
    print("Testing transaction categorization...")
    print("=" * 50)
    
    processor = BankStatementProcessor('generic')
    
    # Test descriptions and expected categories
    test_cases = [
        ("TESCO STORES 1234", "food"),
        ("SHELL PETROL STATION", "transportation"),  
        ("NETFLIX SUBSCRIPTION", "entertainment"),
        ("MORTGAGE PAYMENT", "housing"),
        ("COUNCIL TAX DIRECT DEBIT", "housing"),
        ("SALARY PAYMENT", "other"),  # Should be income
        ("ATM WITHDRAWAL", "other"),
        ("AMAZON MARKETPLACE", "shopping"),
        ("DOCTOR SURGERY PAYMENT", "healthcare"),
        ("ELECTRICITY BILL", "utilities"),
    ]
    
    for description, expected in test_cases:
        category, confidence = processor.categorize_transaction(description)
        status = "✓" if category == expected else "✗"
        print(f"{status} '{description}' -> {category} (expected: {expected}, confidence: {confidence:.1f})")

if __name__ == "__main__":
    test_text_parsing()
    print("\n" + "=" * 70 + "\n")
    test_categorization()
