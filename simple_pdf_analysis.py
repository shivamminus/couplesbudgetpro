import PyPDF2

# Analyze with PyPDF2 only
print("=== PyPDF2 Analysis ===")
try:
    with open('2025_July_Statement.pdf', 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        print(f'Pages: {len(reader.pages)}')
        
        # Extract text from each page
        for i in range(min(3, len(reader.pages))):  # First 3 pages max
            print(f'\n--- Page {i+1} ---')
            text = reader.pages[i].extract_text()
            print(f'Page {i+1} text length: {len(text)} characters')
            if text.strip():
                print('First 800 characters:')
                print(text[:800])
            else:
                print('No text extracted from this page')
            
except Exception as e:
    print(f'PyPDF2 error: {e}')
