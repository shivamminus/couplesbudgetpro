#!/usr/bin/env python3

import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.pdf_processor import BankStatementProcessor, process_pdf_statement

def test_hsbc_pdf():
    """Test HSBC PDF processing with the actual statement"""
    print("=== Testing HSBC PDF Processing ===")
    
    try:
        # Read the HSBC PDF file
        with open('2025-08-29_Statement.pdf', 'rb') as f:
            pdf_content = f.read()
        
        print(f"PDF file size: {len(pdf_content)} bytes")
        
        # Process the PDF using the standalone function
        result = process_pdf_statement(pdf_content, 'hsbc', 8, 2025)  # August 2025
        
        if result['success']:
            print(f"✓ Successfully processed {result['total_transactions']} transactions")
            print(f"Batch ID: {result['batch_id']}")
            print()
            
            # Show all transactions
            print("All transactions:")
            for i, trans in enumerate(result['transactions']):
                print(f"{i+1:2d}. {trans['date']} | {trans['description'][:50]:<50} | {trans.get('hsbc_type', 'N/A'):<4} | {trans['type']:<6} | £{trans['amount']:<8.2f} | {trans['suggested_category']}")
                
            print()
            
            # Show category distribution
            categories = {}
            for trans in result['transactions']:
                cat = trans['suggested_category']
                categories[cat] = categories.get(cat, 0) + 1
                
            print("Category distribution:")
            for cat, count in sorted(categories.items()):
                print(f"  {cat}: {count} transactions")
                
            # Show transaction type distribution
            print("\nTransaction type distribution:")
            types = {}
            for trans in result['transactions']:
                trans_type = trans.get('hsbc_type', 'Unknown')
                types[trans_type] = types.get(trans_type, 0) + 1
                
            for trans_type, count in sorted(types.items()):
                print(f"  {trans_type}: {count} transactions")
                
        else:
            print(f"✗ Processing failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_hsbc_pdf()