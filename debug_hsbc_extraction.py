#!/usr/bin/env python3

import sys
import os
import PyPDF2

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.pdf_processor import BankStatementProcessor

def debug_hsbc_extraction():
    """Debug HSBC PDF text extraction"""
    print("=== Debugging HSBC PDF Text Extraction ===")
    
    try:
        # Read the HSBC PDF file with PyPDF2 directly
        pdf_path = os.path.join(os.path.dirname(__file__), '2025-08-29_Statement.pdf')
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            
            for page_num in range(len(reader.pages)):
                print(f"\n--- Page {page_num + 1} Raw Text ---")
                text = reader.pages[page_num].extract_text()
                lines = text.split('\n')
                
                for i, line in enumerate(lines):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Look for transaction lines
                    if any(pattern in line for pattern in ['Jul 25', 'Aug 25']):
                        print(f"Line {i:3d}: '{line}'")
                        
                        # Try to identify the parts
                        import re
                        date_match = re.match(r'^(\d{2}\s+\w{3}\s+\d{2})', line)
                        if date_match:
                            date_str = date_match.group(1)
                            remaining = line[date_match.end():].strip()
                            print(f"         Date: '{date_str}'")
                            print(f"         Rest: '{remaining}'")
                            
                            # Look for transaction type
                            type_match = re.match(r'^([A-Z]{2,4})(.+)', remaining)
                            if type_match:
                                trans_type = type_match.group(1)
                                details = type_match.group(2).strip()
                                print(f"         Type: '{trans_type}'")
                                print(f"         Details: '{details}'")
                            print()
                            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_hsbc_extraction()