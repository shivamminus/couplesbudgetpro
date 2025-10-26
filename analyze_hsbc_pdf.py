import PyPDF2
import pdfplumber

# Analyze HSBC PDF statement
print("=== HSBC PDF Analysis ===")
try:
    with open('2025-08-29_Statement.pdf', 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        print(f'Pages: {len(reader.pages)}')
        
        # Extract text from each page
        for i in range(min(3, len(reader.pages))):  # First 3 pages max
            print(f'\n--- Page {i+1} ---')
            text = reader.pages[i].extract_text()
            print(f'Page {i+1} text length: {len(text)} characters')
            if text.strip():
                print('First 1000 characters:')
                print(text[:1000])
            else:
                print('No text extracted from this page')
            
except Exception as e:
    print(f'PyPDF2 error: {e}')

print("\n" + "="*80)

# Try with pdfplumber for better table extraction
print("=== pdfplumber Analysis ===")
try:
    with pdfplumber.open('2025-08-29_Statement.pdf') as pdf:
        print(f'Pages: {len(pdf.pages)}')
        
        for i in range(min(2, len(pdf.pages))):
            print(f'\n--- Page {i+1} with pdfplumber ---')
            page = pdf.pages[i]
            text = page.extract_text()
            
            if text:
                print(f'Page {i+1} text (first 800 chars):')
                print(text[:800])
                
                # Try to extract tables
                tables = page.extract_tables()
                if tables:
                    print(f'\nFound {len(tables)} table(s) on page {i+1}')
                    for j, table in enumerate(tables):
                        print(f'Table {j+1} (first 5 rows):')
                        for k, row in enumerate(table[:5]):
                            print(f'  Row {k+1}: {row}')
                        print()
            else:
                print(f'No text found on page {i+1}')
                
except Exception as e:
    print(f'pdfplumber error: {e}')