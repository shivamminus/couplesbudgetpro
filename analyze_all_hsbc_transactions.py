#!/usr/bin/env python3

import sys
import os
import PyPDF2
import re

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def analyze_all_hsbc_transactions():
    """Find ALL potential HSBC transactions including missed ones"""
    print("=== Comprehensive HSBC Transaction Analysis ===")
    
    try:
        # Read the HSBC PDF file with PyPDF2 directly
        pdf_path = os.path.join(os.path.dirname(__file__), '2025-08-29_Statement.pdf')
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            
            all_transactions = []
            
            for page_num in range(len(reader.pages)):
                print(f"\n--- Page {page_num + 1} Analysis ---")
                text = reader.pages[page_num].extract_text()
                lines = text.split('\n')
                
                for i, line in enumerate(lines):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Look for lines that start with a date pattern
                    date_match = re.match(r'^(\d{2}\s+\w{3}\s+\d{2})', line)
                    if date_match:
                        date_str = date_match.group(1)
                        remaining = line[date_match.end():].strip()
                        
                        # Skip certain patterns that are not transactions
                        if any(skip in line for skip in ['BALANCEBROUGHTFORWARD', 'BALANCECARRIEDFORWARD']):
                            continue
                            
                        print(f"  {date_str} | {remaining}")
                        
                        # Try to identify what type of transaction this is
                        transaction_info = {
                            'date': date_str,
                            'line': line,
                            'remaining': remaining,
                            'page': page_num + 1
                        }
                        
                        # Check if it starts with known HSBC codes
                        hsbc_codes = ['CR', 'TFR', 'ATM', 'VIS', 'BP', 'DD', 'OBP']
                        found_code = None
                        for code in hsbc_codes:
                            if remaining.startswith(code):
                                found_code = code
                                break
                        
                        if found_code:
                            transaction_info['type'] = found_code
                            transaction_info['description'] = remaining[len(found_code):].strip()
                            print(f"    → Known Type: {found_code}")
                        elif remaining.startswith(')))'):
                            transaction_info['type'] = 'CARD'
                            transaction_info['description'] = remaining[3:].strip()
                            print(f"    → Card Transaction: {remaining[3:].strip()}")
                        else:
                            transaction_info['type'] = 'UNKNOWN'
                            transaction_info['description'] = remaining
                            print(f"    → Unknown Type: {remaining}")
                            
                        all_transactions.append(transaction_info)
                        
                        # Look for amount on this line or next few lines
                        amount_pattern = r'([\d,]+\.\d{2})'
                        amount_match = re.search(amount_pattern, line)
                        if amount_match:
                            transaction_info['amount'] = amount_match.group(1)
                            print(f"    → Amount: £{amount_match.group(1)}")
                        else:
                            # Check next few lines for amount
                            for j in range(1, 4):
                                if i + j < len(lines):
                                    next_line = lines[i + j].strip()
                                    amount_match = re.search(amount_pattern, next_line)
                                    if amount_match:
                                        transaction_info['amount'] = amount_match.group(1)
                                        transaction_info['amount_line'] = next_line
                                        print(f"    → Amount (next line): £{amount_match.group(1)} | {next_line}")
                                        break
                        
                        print()
            
            print(f"\n=== SUMMARY ===")
            print(f"Total potential transactions found: {len(all_transactions)}")
            
            # Group by type
            by_type = {}
            for trans in all_transactions:
                trans_type = trans['type']
                if trans_type not in by_type:
                    by_type[trans_type] = []
                by_type[trans_type].append(trans)
            
            for trans_type, transactions in by_type.items():
                print(f"\n{trans_type} transactions ({len(transactions)}):")
                for trans in transactions:
                    amount = trans.get('amount', 'NO AMOUNT')
                    print(f"  {trans['date']} | {trans['description'][:50]:<50} | £{amount}")
                    
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_all_hsbc_transactions()