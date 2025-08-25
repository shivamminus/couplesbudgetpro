import PyPDF2
import pdfplumber

# Analyze with PyPDF2
print("=== PyPDF2 Analysis ===")
try:
    with open('2025_July_Statement.pdf', 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        print(f'Pages: {len(reader.pages)}')
        
        # Extract text from first page
        text = reader.pages[0].extract_text()
        print('First page text (first 1000 chars):')
        print(repr(text[:1000]))
        print('\n--- Formatted text preview ---')
        print(text[:1000])
except Exception as e:
    print(f'PyPDF2 error: {e}')

print("\n" + "="*60)

# Analyze with pdfplumber
print("=== pdfplumber Analysis ===")
try:
    with pdfplumber.open('2025_July_Statement.pdf') as pdf:
        print(f'Pages: {len(pdf.pages)}')
        
        # Extract text from first page
        first_page = pdf.pages[0]
        text = first_page.extract_text()
        print('First page text (first 1000 chars):')
        print(repr(text[:1000]))
        
        # Try to extract tables
        tables = first_page.extract_tables()
        if tables:
            print(f'\nFound {len(tables)} table(s)')
            print('First table preview:')
            for i, row in enumerate(tables[0][:5]):
                print(f'Row {i}: {row}')
        else:
            print('\nNo tables found')
            
except Exception as e:
    print(f'pdfplumber error: {e}')
