"""PDF processing utilities for bank statement import"""

import re
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import PyPDF2
from io import BytesIO


class BankStatementProcessor:
    """Base class for processing bank statements"""
    
    def __init__(self, bank_name: str):
        self.bank_name = bank_name.lower()
        self.patterns = self._get_patterns()
        
    def _get_patterns(self) -> Dict[str, str]:
        """Get regex patterns for different banks"""
        patterns = {
            'generic': {
                'date': r'(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
                'amount': r'[\£\$]?(\d+(?:,\d{3})*\.?\d{0,2})',
                'balance': r'[Bb]alance:?\s*[\£\$]?(\d+(?:,\d{3})*\.?\d{0,2})',
                'transaction': r'(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\s+(.+?)\s+([\£\$]?\d+(?:,\d{3})*\.?\d{0,2})'
            },
            'hsbc': {
                'transaction_line': r'(\d{2}\s+\w{3}\s+\d{2})\s+([A-Z]{2,4})\s*(.+?)\s+([\d,]+\.\d{2})\s*$',
                'transaction_multiline': r'(\d{2}\s+\w{3}\s+\d{2})\s+([A-Z]{2,4})\s*(.+?)(?:\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})|\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2}))',
                'date_format': '%d %b %y',
                'balance_line': r'BALANCEBROUGHTFORWARD\s+([\d,]+\.\d{2})|BALANCECARRIEDFORWARD\s+([\d,]+\.\d{2})'
            },
            'barclays': {
                'transaction': r'(\d{2}\s\w{3}\s\d{4})\s+(.+?)\s+(\d+\.\d{2})',
                'date_format': '%d %b %Y'
            },
            'lloyds': {
                'transaction_pdf': r'Date\s+(\d{2}\s+\w{3}\s+\d{2})\s*[\.\s]*Description\s*[\.\s]*(.+?)\s*[\.\s]*Type\s*[\.\s]*([A-Z]{3})\s*[\.\s]*Money\s+In\s+\(£\)\s*[\.\s]*([\d,]*\.?\d*)\s*[\.\s]*Money\s+Out\s+\(£\)\s*[\.\s]*([\d,]*\.?\d*)\s*[\.\s]*Balance\s+\(£\)\s*[\.\s]*([\d,]+\.\d{2})',
                'transaction_line': r'(\d{2}\s+\w{3}\s+\d{2})\s*[\.\s]*(.+?)\s*[\.\s]*([A-Z]{3})\s*[\.\s]*([\d,]*\.?\d*)\s*[\.\s]*([\d,]*\.?\d*)\s*[\.\s]*([\d,]+\.\d{2})',
                'date_format_pdf': '%d %b %y',
                'date_format_csv': '%d/%m/%Y'
            },
            'natwest': {
                'transaction': r'(\d{2}\s\w{3}\s\d{4})\s+(.+?)\s+(\d+\.\d{2})\s+(\d+\.\d{2})',
                'date_format': '%d %b %Y'
            }
        }
        
        return patterns.get(self.bank_name, patterns['generic'])
    
    def extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """Extract text content from PDF"""
        try:
            pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_content))
            text = ""
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                text += page_text + "\n"
                
            print(f"DEBUG: Extracted {len(text)} characters from PDF")
            print(f"DEBUG: First 500 characters:\n{text[:500]}")
            return text
        except Exception as e:
            print(f"DEBUG: Error extracting PDF: {str(e)}")
            raise Exception(f"Error extracting text from PDF: {str(e)}")
    
    def parse_transactions(self, text: str) -> List[Dict]:
        """Parse transactions from extracted text"""
        transactions = []
        lines = text.split('\n')
        
        # Try bank-specific patterns first
        if self.bank_name in ['hsbc', 'barclays', 'lloyds', 'natwest']:
            transactions = self._parse_bank_specific(text)
        
        # Fall back to generic parsing if no transactions found
        if not transactions:
            transactions = self._parse_generic(text)
            
        return transactions
    
    def _parse_bank_specific(self, text: str) -> List[Dict]:
        """Parse using bank-specific patterns"""
        transactions = []
        
        # Special handling for specific banks
        if self.bank_name == 'lloyds':
            return self._parse_lloyds_pdf(text)
        elif self.bank_name == 'hsbc':
            return self._parse_hsbc_pdf(text)
        
        pattern = self.patterns.get('transaction', '')
        date_format = self.patterns.get('date_format', '%d/%m/%Y')
        
        if not pattern:
            return transactions
            
        matches = re.finditer(pattern, text, re.MULTILINE)
        
        for match in matches:
            try:
                groups = match.groups()
                if len(groups) >= 3:
                    date_str = groups[0]
                    description = groups[1].strip()
                    amount_str = groups[2]
                    balance_str = groups[3] if len(groups) > 3 else None
                    
                    # Parse date
                    try:
                        transaction_date = datetime.strptime(date_str, date_format).date()
                    except ValueError:
                        # Try alternative date formats
                        for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y', '%d %b %Y']:
                            try:
                                transaction_date = datetime.strptime(date_str, fmt).date()
                                break
                            except ValueError:
                                continue
                        else:
                            continue  # Skip if date can't be parsed
                    
                    # Parse amount
                    amount = self._parse_amount(amount_str)
                    balance = self._parse_amount(balance_str) if balance_str else None
                    
                    # Determine transaction type
                    transaction_type = self._determine_transaction_type(description, amount)
                    
                    transaction = {
                        'date': transaction_date,
                        'description': description,
                        'amount': abs(amount),  # Store as positive, use type for direction
                        'balance': balance,
                        'type': transaction_type,
                        'raw_text': match.group(0)
                    }
                    
                    transactions.append(transaction)
                    
            except Exception as e:
                continue  # Skip problematic transactions
                
        return transactions
        
    def _parse_lloyds_pdf(self, text: str) -> List[Dict]:
        """Parse Lloyds Bank PDF statements with specialized logic"""
        transactions = []
        lines = text.split('\n')
        
        print(f"DEBUG: Parsing Lloyds PDF with {len(lines)} lines")
        
        # Look for transaction lines in the format we discovered
        # Date: "21 Jul 25", Description, Type: "DEB", Money In/Out, Balance
        transaction_pattern = r'(\d{2}\s+\w{3}\s+\d{2})\s*[\.\s]*(.+?)\s*[\.\s]*([A-Z]{3})\s*[\.\s]*blank[\.\s]*([\d,]*\.?\d*)\s*[\.\s]*([\d,]+\.\d{2})|(\d{2}\s+\w{3}\s+\d{2})\s*[\.\s]*(.+?)\s*[\.\s]*([A-Z]{3})\s*[\.\s]*([\d,]*\.?\d*)\s*[\.\s]*blank[\.\s]*([\d,]+\.\d{2})'
        
        # Also try to find transactions in a more flexible way
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Look for date pattern at start of line
            date_match = re.match(r'^(\d{2}\s+\w{3}\s+\d{2})', line)
            if not date_match:
                continue
                
            print(f"DEBUG: Found potential transaction line: {line}")
            
            # Try to extract transaction details from this line and possibly next lines
            date_str = date_match.group(1)
            remaining = line[date_match.end():].strip()
            
            # Look for balance at the end (format: 1,566.83)
            balance_match = re.search(r'([\d,]+\.\d{2})(?:\s*$)', remaining)
            if not balance_match:
                continue
                
            balance_str = balance_match.group(1)
            before_balance = remaining[:balance_match.start()].strip()
            
            # Look for amount before balance (format: 30.48 or blank)
            amount_match = re.search(r'([\d,]*\.?\d*)\s*$', before_balance)
            amount_str = ""
            description_and_type = before_balance
            
            if amount_match:
                amount_str = amount_match.group(1)
                description_and_type = before_balance[:amount_match.start()].strip()
            
            # Look for transaction type (DEB, FPI, FPO, TFR, CPT)
            type_match = re.search(r'\b([A-Z]{3})\b', description_and_type)
            trans_type = type_match.group(1) if type_match else "UNK"
            
            # Extract description (everything before the type)
            if type_match:
                description = description_and_type[:type_match.start()].strip()
            else:
                description = description_and_type.strip()
                
            # Clean up description
            description = re.sub(r'[\.]+', ' ', description).strip()
            description = re.sub(r'\s+', ' ', description)
            
            # Skip if description is too short
            if len(description) < 3:
                continue
                
            try:
                # Parse date (format: "21 Jul 25")
                transaction_date = datetime.strptime(date_str, '%d %b %y').date()
                
                # Parse amount and balance
                amount = self._parse_amount(amount_str) if amount_str else 0.0
                balance = self._parse_amount(balance_str)
                
                # Determine transaction direction based on Lloyds type codes
                transaction_direction = self._lloyds_transaction_type(trans_type, description)
                
                if amount > 0:
                    transaction = {
                        'date': transaction_date,
                        'description': description,
                        'amount': amount,
                        'balance': balance,
                        'type': transaction_direction,
                        'lloyds_type': trans_type,
                        'raw_text': line
                    }
                    
                    transactions.append(transaction)
                    print(f"DEBUG: Parsed Lloyds transaction: {date_str} - {description} - {trans_type} - £{amount}")
                    
            except Exception as e:
                print(f"DEBUG: Error parsing Lloyds transaction: {str(e)}")
                continue
        
        print(f"DEBUG: Successfully parsed {len(transactions)} Lloyds transactions")
        return transactions
    
    def _parse_hsbc_pdf(self, text: str) -> List[Dict]:
        """Parse HSBC Bank PDF statements with comprehensive logic to capture ALL transactions"""
        transactions = []
        lines = text.split('\n')
        
        print(f"DEBUG: Parsing HSBC PDF with {len(lines)} lines")
        
        # Build a comprehensive transaction list
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
                
            # Skip header/footer lines
            if any(skip in line for skip in ['Contact tel', 'Text phone', 'www.hsbc.co.uk', 'Your Statement', 
                                            'Account Name', 'Sortcode', 'Account Number', 'Sheet Number',
                                            'Opening Balance', 'Payments In', 'Payments Out', 'Closing Balance',
                                            'International Bank Account Number', 'Bank Identifier Code',
                                            'see reverse for call times', 'used by deaf or speech impaired',
                                            'BALANCEBROUGHTFORWARD', 'BALANCECARRIEDFORWARD']):
                i += 1
                continue
                
            # Look for date pattern at start of line
            date_match = re.match(r'^(\d{2}\s+\w{3}\s+\d{2})', line)
            if date_match:
                date_str = date_match.group(1)
                remaining = line[date_match.end():].strip()
                
                print(f"DEBUG: Found date line: {date_str} | {remaining}")
                
                # Parse transactions starting with this date
                transactions_found = self._parse_hsbc_transaction_group(date_str, remaining, lines, i)
                transactions.extend(transactions_found)
            
            i += 1
        
        print(f"DEBUG: Successfully parsed {len(transactions)} HSBC transactions")
        return transactions
    
    def _parse_hsbc_transaction_group(self, date_str: str, first_line_content: str, all_lines: List[str], start_idx: int) -> List[Dict]:
        """Parse a group of transactions starting from a date line"""
        transactions = []
        
        try:
            transaction_date = datetime.strptime(date_str, '%d %b %y').date()
        except ValueError:
            print(f"DEBUG: Could not parse date: {date_str}")
            return transactions
        
        # Look ahead for related transaction lines
        current_line_content = first_line_content
        
        # Parse the first transaction on the date line itself
        first_transaction = self._parse_single_hsbc_transaction(date_str, current_line_content, all_lines, start_idx)
        if first_transaction:
            transactions.append(first_transaction)
        
        # Look for additional transactions in the following lines (without dates)
        i = start_idx + 1
        while i < len(all_lines) and i < start_idx + 10:  # Look ahead up to 10 lines
            line = all_lines[i].strip()
            if not line:
                i += 1
                continue
                
            # Stop if we hit another date line
            if re.match(r'^(\d{2}\s+\w{3}\s+\d{2})', line):
                break
                
            # Skip balance/header lines
            if any(skip in line for skip in ['BALANCE', 'Contact tel', 'Text phone', 'Account Name']):
                i += 1
                continue
            
            # Look for transaction patterns without dates
            additional_transaction = self._parse_undated_hsbc_transaction(date_str, line, all_lines, i)
            if additional_transaction:
                transactions.append(additional_transaction)
                print(f"DEBUG: Found additional transaction on {date_str}: {additional_transaction['description']} - £{additional_transaction['amount']}")
            
            i += 1
        
        return transactions
    
    def _parse_single_hsbc_transaction(self, date_str: str, line_content: str, all_lines: List[str], line_idx: int) -> Optional[Dict]:
        """Parse a single HSBC transaction from the main date line"""
        
        # Known HSBC codes: CR, TFR, ATM, VIS, BP, DD, OBP
        hsbc_codes = ['CR', 'TFR', 'ATM', 'VIS', 'BP', 'DD', 'OBP']
        
        trans_type = None
        details = line_content
        
        # Try to match known HSBC transaction codes at the start
        for code in hsbc_codes:
            if line_content.startswith(code):
                trans_type = code
                details = line_content[len(code):].strip()
                break
        
        # Check for card transactions that start with )))
        if not trans_type and line_content.startswith(')))'):
            trans_type = 'CARD'
            details = line_content[3:].strip()
        
        if trans_type:
            # Try to find amount on this line or next few lines
            amount = None
            description = details
            
            # First try to extract amount from current line
            amount_match = re.search(r'([\d,]+\.\d{2})', line_content)
            if amount_match:
                amount = self._parse_amount(amount_match.group(1))
                # Remove amount from description
                description = re.sub(r'\s*[\d,]+\.\d{2}.*$', '', details).strip()
            else:
                # Look for amount in next few lines
                for j in range(1, 4):
                    if line_idx + j < len(all_lines):
                        next_line = all_lines[line_idx + j].strip()
                        amount_match = re.search(r'([\d,]+\.\d{2})', next_line)
                        if amount_match:
                            amount = self._parse_amount(amount_match.group(1))
                            # For multi-line, include the description from next line too
                            description_part = re.sub(r'\s*[\d,]+\.\d{2}.*$', '', next_line).strip()
                            if description_part and len(description_part) > 2:
                                description = f"{details} {description_part}".strip()
                            break
            
            if amount and amount > 0:
                try:
                    transaction_date = datetime.strptime(date_str, '%d %b %y').date()
                    transaction_direction = self._hsbc_transaction_type(trans_type, description)
                    
                    return {
                        'date': transaction_date,
                        'description': description,
                        'amount': amount,
                        'type': transaction_direction,
                        'hsbc_type': trans_type,
                        'raw_text': f"{date_str} {line_content}"
                    }
                except Exception as e:
                    print(f"DEBUG: Error creating transaction: {str(e)}")
        
        return None
    
    def _parse_undated_hsbc_transaction(self, date_str: str, line: str, all_lines: List[str], line_idx: int) -> Optional[Dict]:
        """Parse transactions that appear on lines without dates (continuation transactions)"""
        
        # Look for patterns that indicate transactions:
        # 1. VIS pattern: "VISAmazon Prime*RM5QQ" or "VISRevolut**9937*"
        # 2. Card patterns: ")))FCA STRATFORD", ")))Circolo Popolare"  
        # 3. ATM patterns: "ATMCASH YCSH JUL31"
        # 4. Direct payments: "BPRitika Sneh wise", "CRRitika Sneh"
        # 5. Direct debits: "DDHSBC CARD PYMT"
        
        trans_type = None
        description = line
        
        # VIS transactions
        if line.startswith('VIS'):
            trans_type = 'VIS'
            description = line[3:].strip()
        # Card transactions starting with )))
        elif line.startswith(')))'):
            trans_type = 'CARD'
            description = line[3:].strip()
        # ATM transactions
        elif line.startswith('ATM'):
            trans_type = 'ATM'
            description = line[3:].strip()
        # Bank payments
        elif line.startswith('BP'):
            trans_type = 'BP'
            description = line[2:].strip()
        # Credits
        elif line.startswith('CR'):
            trans_type = 'CR'
            description = line[2:].strip()
        # Direct debits
        elif line.startswith('DD'):
            trans_type = 'DD'
            description = line[2:].strip()
        
        if trans_type:
            # Try to find amount on this line or next line
            amount = None
            
            # First try current line
            amount_match = re.search(r'([\d,]+\.\d{2})', line)
            if amount_match:
                amount = self._parse_amount(amount_match.group(1))
                # Remove amount from description
                description = re.sub(r'\s*[\d,]+\.\d{2}.*$', '', description).strip()
            else:
                # Try next line
                if line_idx + 1 < len(all_lines):
                    next_line = all_lines[line_idx + 1].strip()
                    amount_match = re.search(r'([\d,]+\.\d{2})', next_line)
                    if amount_match:
                        amount = self._parse_amount(amount_match.group(1))
                        # Add description from next line if it doesn't look like an amount-only line
                        description_part = re.sub(r'\s*[\d,]+\.\d{2}.*$', '', next_line).strip()
                        if description_part and len(description_part) > 2:
                            description = f"{description} {description_part}".strip()
            
            # Validate amount is reasonable (not a balance)
            if amount and 0.50 <= amount <= 10000:
                try:
                    transaction_date = datetime.strptime(date_str, '%d %b %y').date()
                    transaction_direction = self._hsbc_transaction_type(trans_type, description)
                    
                    return {
                        'date': transaction_date,
                        'description': description,
                        'amount': amount,
                        'type': transaction_direction,
                        'hsbc_type': trans_type,
                        'raw_text': line
                    }
                except Exception as e:
                    print(f"DEBUG: Error creating undated transaction: {str(e)}")
        
        return None
    
    def _parse_generic(self, text: str) -> List[Dict]:
        """Generic transaction parsing"""
        transactions = []
        lines = text.split('\n')
        
        print(f"DEBUG: Parsing {len(lines)} lines of text")
        
        # More flexible patterns
        date_patterns = [
            r'(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',  # DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY
            r'(\d{1,2}\s+\w{3}\s+\d{2,4})',            # DD MMM YYYY
            r'(\d{2}\s+\w+\s+\d{4})',                   # DD Month YYYY
        ]
        
        amount_patterns = [
            r'(?:£|\$|EUR|GBP)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # Currency amounts
            r'(\d{1,3}(?:,\d{3})*\.\d{2})',                           # Decimal amounts
        ]
        
        transaction_count = 0
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line or len(line) < 10:  # Skip very short lines
                continue
                
            # Try to find date patterns
            date_match = None
            for pattern in date_patterns:
                date_match = re.search(pattern, line)
                if date_match:
                    break
                    
            if not date_match:
                continue
                
            # Try to find amount patterns
            amount_matches = []
            for pattern in amount_patterns:
                amount_matches.extend(re.findall(pattern, line))
                
            if not amount_matches:
                continue
                
            try:
                # Parse date
                date_str = date_match.group(1)
                transaction_date = self._parse_date(date_str)
                
                if not transaction_date:
                    print(f"DEBUG: Could not parse date: {date_str}")
                    continue
                
                # Extract description (text between date and amounts)
                description_start = date_match.end()
                description = line[description_start:].strip()
                
                # Find the transaction amount (usually the first significant amount)
                amounts = []
                for amt_str in amount_matches:
                    amount = self._parse_amount(amt_str)
                    if amount > 0:
                        amounts.append(amount)
                
                if not amounts:
                    continue
                    
                # Use the first amount as transaction amount
                transaction_amount = amounts[0]
                
                # Clean description by removing amounts and extra text
                clean_desc = description
                for amt_match in amount_matches:
                    clean_desc = clean_desc.replace(amt_match, '').replace('£', '').replace('$', '').replace(',', '')
                clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()
                
                # Skip if description is too short or looks like header/footer
                if len(clean_desc) < 3 or clean_desc.lower() in ['balance', 'total', 'page', 'statement']:
                    continue
                
                # Determine transaction type
                transaction_type = self._determine_transaction_type(clean_desc, transaction_amount)
                
                transaction = {
                    'date': transaction_date,
                    'description': clean_desc,
                    'amount': transaction_amount,
                    'balance': amounts[1] if len(amounts) > 1 else None,
                    'type': transaction_type,
                    'raw_text': line
                }
                
                transactions.append(transaction)
                transaction_count += 1
                print(f"DEBUG: Found transaction {transaction_count}: {clean_desc} - £{transaction_amount}")
                
            except Exception as e:
                print(f"DEBUG: Error processing line {line_num}: {str(e)}")
                continue
        
        print(f"DEBUG: Successfully parsed {len(transactions)} transactions")
        return transactions
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string with multiple formats"""
        date_formats = [
            '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y',
            '%d/%m/%y', '%d-%m-%y', '%d.%m.%y',
            '%d %b %Y', '%d %B %Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        return None
    
    def _parse_amount(self, amount_str: str) -> float:
        """Parse amount string to float"""
        if not amount_str:
            return 0.0
            
        # Remove currency symbols and whitespace
        clean_amount = re.sub(r'[£$\s,]', '', str(amount_str))
        
        try:
            return float(clean_amount)
        except ValueError:
            return 0.0
    
    def _lloyds_transaction_type(self, trans_code: str, description: str) -> str:
        """Determine transaction type based on Lloyds transaction codes"""
        # Lloyds transaction type codes:
        # DEB = Debit (outgoing payment)
        # FPI = Faster Payment In (incoming)
        # FPO = Faster Payment Out (outgoing)
        # TFR = Transfer
        # CPT = Card Payment
        
        if trans_code in ['FPI', 'TFR'] and 'in' in description.lower():
            return 'credit'
        elif trans_code in ['DEB', 'FPO', 'CPT']:
            return 'debit'
        else:
            # Fall back to description analysis
            return self._determine_transaction_type(description, 0)
    
    def _hsbc_transaction_type(self, trans_code: str, description: str) -> str:
        """Determine transaction type based on HSBC transaction codes"""
        # HSBC transaction type codes:
        # CR = Credit (incoming payment/deposit)
        # TFR = Transfer (outgoing transfer)
        # ATM = ATM withdrawal
        # VIS = Visa card payment
        # BP = Bank Payment (outgoing payment)
        # DD = Direct Debit
        # OBP = Online Banking Payment
        # CARD = Card transaction (starts with )))
        
        if trans_code in ['CR']:
            return 'credit'
        elif trans_code in ['TFR', 'ATM', 'VIS', 'BP', 'DD', 'OBP', 'CARD']:
            return 'debit'
        else:
            # Fall back to description analysis for unknown codes
            return self._determine_transaction_type(description, 0)
    
    def _determine_transaction_type(self, description: str, amount: float) -> str:
        """Determine if transaction is debit or credit based on description and amount"""
        description_lower = description.lower()
        
        # Common credit indicators
        credit_keywords = [
            'salary', 'wage', 'pay', 'deposit', 'transfer in', 'credit',
            'refund', 'cashback', 'interest', 'dividend', 'payment received'
        ]
        
        # Common debit indicators  
        debit_keywords = [
            'withdrawal', 'purchase', 'payment', 'fee', 'charge', 'debit',
            'atm', 'card payment', 'direct debit', 'standing order'
        ]
        
        # Check for credit indicators
        if any(keyword in description_lower for keyword in credit_keywords):
            return 'credit'
        
        # Check for debit indicators
        if any(keyword in description_lower for keyword in debit_keywords):
            return 'debit'
        
        # Default to debit for most transactions
        return 'debit'
    
    def categorize_transaction(self, description: str) -> Tuple[str, float]:
        """Auto-categorize transaction based on description"""
        description_lower = description.lower()
        
        # HSBC-specific merchant recognition first
        if self.bank_name == 'hsbc':
            hsbc_category, hsbc_confidence = self._categorize_hsbc_transaction(description_lower)
            if hsbc_confidence > 0.7:
                return hsbc_category, hsbc_confidence
        
        # Category mapping with confidence scores
        categories = {
            'food': {
                'keywords': ['tesco', 'asda', 'sainsbury', 'morrisons', 'aldi', 'lidl', 
                           'restaurant', 'cafe', 'takeaway', 'pizza', 'mcdonald', 'kfc',
                           'food', 'grocery', 'supermarket'],
                'confidence': 0.9
            },
            'transportation': {
                'keywords': ['fuel', 'petrol', 'diesel', 'train', 'bus', 'taxi', 'uber',
                           'parking', 'mot', 'insurance', 'car', 'vehicle'],
                'confidence': 0.8
            },
            'utilities': {
                'keywords': ['electric', 'gas', 'water', 'phone', 'internet', 'broadband',
                           'mobile', 'energy', 'utility'],
                'confidence': 0.9
            },
            'entertainment': {
                'keywords': ['netflix', 'spotify', 'amazon prime', 'cinema', 'theatre',
                           'gym', 'fitness', 'sport', 'game'],
                'confidence': 0.8
            },
            'shopping': {
                'keywords': ['amazon', 'ebay', 'argos', 'currys', 'john lewis', 'marks spencer',
                           'next', 'zara', 'h&m', 'clothes', 'clothing'],
                'confidence': 0.7
            },
            'healthcare': {
                'keywords': ['pharmacy', 'chemist', 'doctor', 'dentist', 'hospital',
                           'medical', 'health', 'prescription'],
                'confidence': 0.9
            },
            'housing': {
                'keywords': ['rent', 'mortgage', 'council tax', 'home insurance',
                           'maintenance', 'repair', 'diy'],
                'confidence': 0.9
            }
        }
        
        # Check each category
        for category, data in categories.items():
            if any(keyword in description_lower for keyword in data['keywords']):
                return category, data['confidence']
        
        # Default category
        return 'other', 0.3
    
    def _categorize_hsbc_transaction(self, description_lower: str) -> Tuple[str, float]:
        """Enhanced categorization for HSBC Bank transactions"""
        
        # HSBC-specific merchant recognition based on the sample statement
        hsbc_categories = {
            'transportation': {
                'keywords': ['tfl travel ch', 'tfl.gov.uk/cp', 'fuel', 'petrol', 'parking'],
                'confidence': 0.95
            },
            'food': {
                'keywords': ['circolo popolare', 'ristorante venezia', 'restaurant', 'food'],
                'confidence': 0.9
            },
            'transfers': {
                'keywords': ['ritika sneh', 'shivam dubey', 'internet transfer', 'sent from revolut'],
                'confidence': 0.95
            },
            'income': {
                'keywords': ['cognizant', 'salary', 'payroll'],
                'confidence': 0.95
            },
            'cash': {
                'keywords': ['atm cash', 'cash withdrawal'],
                'confidence': 0.9
            },
            'shopping': {
                'keywords': ['amazon prime', 'apple.com/bill', 'revolut'],
                'confidence': 0.85
            },
            'utilities': {
                'keywords': ['american express', 'hsbc card pymt'],
                'confidence': 0.9
            },
            'rent': {
                'keywords': ['rent28-31aug', 'rent'],
                'confidence': 0.95
            },
            'entertainment': {
                'keywords': ['fca stratford', 'london', 'cinema', 'theatre', 'entertainment'],
                'confidence': 0.8
            }
        }
        
        # Check HSBC-specific patterns
        for category, data in hsbc_categories.items():
            if any(keyword in description_lower for keyword in data['keywords']):
                return category, data['confidence']
        
        return 'other', 0.3
    
    def generate_batch_id(self) -> str:
        """Generate unique batch ID for import"""
        return str(uuid.uuid4())
        
    def _clean_description(self, description: str) -> str:
        """Clean and standardize transaction description"""
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', description).strip()
        
        # Remove reference numbers and codes
        cleaned = re.sub(r'[A-Z0-9]{6,}', '', cleaned)
        
        # Capitalize first letter of each word
        cleaned = ' '.join(word.capitalize() for word in cleaned.split())
        
        return cleaned


def process_pdf_statement(pdf_content: bytes, bank_name: str, 
                         statement_month: int, statement_year: int) -> Dict:
    """
    Main function to process a bank statement PDF
    
    Args:
        pdf_content: PDF file content as bytes
        bank_name: Name of the bank
        statement_month: Statement month (1-12)  
        statement_year: Statement year
        
    Returns:
        Dictionary containing processed transactions and metadata
    """
    try:
        print(f"DEBUG: Processing PDF for {bank_name}, {statement_month}/{statement_year}")
        print(f"DEBUG: PDF size: {len(pdf_content)} bytes")
        
        processor = BankStatementProcessor(bank_name)
        
        # Extract text from PDF
        text = processor.extract_text_from_pdf(pdf_content)
        
        if not text or len(text.strip()) < 50:
            return {
                'success': False,
                'error': 'PDF appears to be empty or contains very little text',
                'transactions': [],
                'total_transactions': 0
            }
        
        # Parse transactions
        transactions = processor.parse_transactions(text)
        print(f"DEBUG: Found {len(transactions)} total transactions")
        
        # Filter transactions by statement period if specified
        if statement_month and statement_year:
            filtered_transactions = []
            for trans in transactions:
                if (trans['date'].month == int(statement_month) and 
                    trans['date'].year == int(statement_year)):
                    filtered_transactions.append(trans)
            print(f"DEBUG: After filtering by {statement_month}/{statement_year}: {len(filtered_transactions)} transactions")
            transactions = filtered_transactions
        
        # Auto-categorize transactions
        categorized_count = 0
        for transaction in transactions:
            category, confidence = processor.categorize_transaction(transaction['description'])
            transaction['suggested_category'] = category
            transaction['confidence_score'] = confidence
            transaction['suggested_description'] = processor._clean_description(transaction['description'])
            
            if category != 'other':
                categorized_count += 1
        
        print(f"DEBUG: Auto-categorized {categorized_count} out of {len(transactions)} transactions")
        
        # Generate batch ID
        batch_id = processor.generate_batch_id()
        
        result = {
            'success': True,
            'batch_id': batch_id,
            'transactions': transactions,
            'total_transactions': len(transactions),
            'bank_name': bank_name,
            'statement_period': f"{statement_month}/{statement_year}",
            'processed_at': datetime.utcnow(),
            'debug_info': {
                'text_length': len(text),
                'categorized_count': categorized_count,
                'parsing_method': 'bank_specific' if bank_name in ['hsbc', 'barclays', 'lloyds', 'natwest'] else 'generic'
            }
        }
        
        return result
        
    except Exception as e:
        print(f"DEBUG: Error processing PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e),
            'transactions': [],
            'total_transactions': 0
        }
