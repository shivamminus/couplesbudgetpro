#!/usr/bin/env python3

import sys
import os
import PyPDF2
import re

def comprehensive_pdf_analysis():
    """Thorough analysis of every line in the HSBC PDF to find ALL transactions"""
    print("=== COMPREHENSIVE HSBC PDF ANALYSIS ===")
    
    try:
        pdf_path = os.path.join(os.path.dirname(__file__), '2025-08-29_Statement.pdf')
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            
            all_lines = []
            
            # Extract ALL text from ALL pages
            for page_num in range(len(reader.pages)):
                print(f"\n=== PAGE {page_num + 1} FULL CONTENT ===")
                text = reader.pages[page_num].extract_text()
                lines = text.split('\n')
                
                print(f"Total lines on page {page_num + 1}: {len(lines)}")
                
                for i, line in enumerate(lines):
                    line = line.strip()
                    if line:
                        print(f"{i:3d}: {line}")
                        all_lines.append({
                            'page': page_num + 1,
                            'line_num': i,
                            'content': line
                        })
            
            print(f"\n=== TRANSACTION ANALYSIS ===")
            print(f"Total non-empty lines across all pages: {len(all_lines)}")
            
            # Look for ALL potential transaction patterns
            potential_transactions = []
            
            for line_data in all_lines:
                line = line_data['content']
                
                # Pattern 1: Lines starting with date
                date_match = re.match(r'^(\d{2}\s+\w{3}\s+\d{2})', line)
                if date_match:
                    date_str = date_match.group(1)
                    remaining = line[date_match.end():].strip()
                    
                    potential_transactions.append({
                        'type': 'DATE_LINE',
                        'date': date_str,
                        'content': remaining,
                        'full_line': line,
                        'page': line_data['page'],
                        'line_num': line_data['line_num']
                    })
                
                # Pattern 2: Lines with amounts (even without dates)
                amount_matches = re.findall(r'([\d,]+\.\d{2})', line)
                if amount_matches:
                    potential_transactions.append({
                        'type': 'AMOUNT_LINE',
                        'amounts': amount_matches,
                        'full_line': line,
                        'page': line_data['page'],
                        'line_num': line_data['line_num']
                    })
                
                # Pattern 3: Lines with merchant names (Amazon, TFL, VIS, etc.)
                merchant_patterns = ['amazon', 'tfl', 'vis', 'atm', 'fca', 'apple', 'revolut', 'circolo', 'stratford']
                for pattern in merchant_patterns:
                    if pattern.lower() in line.lower():
                        potential_transactions.append({
                            'type': 'MERCHANT_LINE',
                            'merchant': pattern,
                            'full_line': line,
                            'page': line_data['page'],
                            'line_num': line_data['line_num']
                        })
            
            print(f"\n=== POTENTIAL TRANSACTIONS BY TYPE ===")
            
            # Group by type
            by_type = {}
            for trans in potential_transactions:
                trans_type = trans['type']
                if trans_type not in by_type:
                    by_type[trans_type] = []
                by_type[trans_type].append(trans)
            
            for trans_type, transactions in by_type.items():
                print(f"\n{trans_type} ({len(transactions)} items):")
                for trans in transactions:
                    if trans_type == 'DATE_LINE':
                        print(f"  Page {trans['page']} Line {trans['line_num']:3d}: {trans['date']} | {trans['content']}")
                    elif trans_type == 'AMOUNT_LINE':
                        print(f"  Page {trans['page']} Line {trans['line_num']:3d}: {trans['amounts']} | {trans['full_line']}")
                    elif trans_type == 'MERCHANT_LINE':
                        print(f"  Page {trans['page']} Line {trans['line_num']:3d}: {trans['merchant'].upper()} | {trans['full_line']}")
            
            # Try to reconstruct complete transactions
            print(f"\n=== RECONSTRUCTING COMPLETE TRANSACTIONS ===")
            
            date_lines = [t for t in potential_transactions if t['type'] == 'DATE_LINE']
            print(f"Found {len(date_lines)} lines starting with dates")
            
            for date_trans in date_lines:
                print(f"\nDate: {date_trans['date']} (Page {date_trans['page']}, Line {date_trans['line_num']})")
                print(f"  Content: {date_trans['content']}")
                
                # Look for related lines (amounts, merchants) in the next few lines
                start_idx = None
                for i, line_data in enumerate(all_lines):
                    if (line_data['page'] == date_trans['page'] and 
                        line_data['line_num'] == date_trans['line_num']):
                        start_idx = i
                        break
                
                if start_idx:
                    print("  Related lines:")
                    for j in range(1, 5):  # Check next 4 lines
                        if start_idx + j < len(all_lines):
                            next_line = all_lines[start_idx + j]
                            content = next_line['content']
                            print(f"    +{j}: {content}")
                            
                            # Check if this line has amounts
                            amounts = re.findall(r'([\d,]+\.\d{2})', content)
                            if amounts:
                                print(f"         → Amounts found: {amounts}")
                            
                            # Check for merchant patterns
                            for pattern in merchant_patterns:
                                if pattern.lower() in content.lower():
                                    print(f"         → Merchant: {pattern.upper()}")
                
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    comprehensive_pdf_analysis()