#!/usr/bin/env python3

import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.routes.imports import process_lloyds_csv

# Read the Lloyds CSV file
try:
    with open('13398462_20253125_0808.csv', 'r', encoding='utf-8') as f:
        csv_content = f.read()
    
    print("=== Testing Lloyds CSV Processing ===")
    print(f"CSV content length: {len(csv_content)} characters")
    print(f"Number of lines: {len(csv_content.splitlines())}")
    print()
    
    # Process the CSV
    result = process_lloyds_csv(csv_content, "test_lloyds.csv")
    
    if result['success']:
        print(f"✓ Successfully processed {result['total_transactions']} transactions")
        print(f"Bank: {result.get('bank_name', 'N/A')}")
        print(f"Format: {result.get('format', 'N/A')}")
        print(f"Batch ID: {result['batch_id']}")
        print()
        
        # Show first few transactions
        print("First 5 transactions:")
        for i, trans in enumerate(result['transactions'][:5]):
            print(f"{i+1}. {trans['date']} | {trans['description'][:40]:<40} | {trans['lloyds_type']} | {trans['type']:<6} | £{trans['amount']:<8.2f} | {trans['suggested_category']}")
            
        print()
        
        # Show category distribution
        categories = {}
        for trans in result['transactions']:
            cat = trans['suggested_category']
            categories[cat] = categories.get(cat, 0) + 1
            
        print("Category distribution:")
        for cat, count in sorted(categories.items()):
            print(f"  {cat}: {count} transactions")
            
    else:
        print(f"✗ Processing failed: {result.get('error', 'Unknown error')}")
        
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
