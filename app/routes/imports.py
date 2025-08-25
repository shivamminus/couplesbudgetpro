"""Routes for PDF import functionality"""

import os
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import ImportedTransaction
from app.forms import PDFImportForm, CSVImportForm, TransactionReviewForm, BulkTransactionReviewForm
from app.pdf_processor import process_pdf_statement

imports = Blueprint('imports', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'csv'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@imports.route('/import', methods=['GET', 'POST'])
@login_required
def upload_statement():
    """Upload and process bank statement PDF"""
    form = PDFImportForm()
    
    if form.validate_on_submit():
        print("DEBUG: Form validated successfully")
        file = form.pdf_file.data
        
        if file and allowed_file(file.filename):
            print(f"DEBUG: Processing file: {file.filename}")
            try:
                # Read file content
                pdf_content = file.read()
                print(f"DEBUG: Read {len(pdf_content)} bytes from file")
                
                # Check file size
                if len(pdf_content) > MAX_FILE_SIZE:
                    flash('File size too large. Maximum size is 16MB.', 'error')
                    return render_template('imports/upload.html', form=form)
                
                # Process PDF
                print(f"DEBUG: Processing PDF with bank={form.bank_name.data}, month={form.statement_month.data}, year={form.statement_year.data}")
                result = process_pdf_statement(
                    pdf_content=pdf_content,
                    bank_name=form.bank_name.data,
                    statement_month=int(form.statement_month.data),
                    statement_year=int(form.statement_year.data)
                )
                
                print(f"DEBUG: Processing result: success={result['success']}, transactions={result['total_transactions']}")
                
                if result['success']:
                    # Save transactions to database
                    saved_count = 0
                    for transaction_data in result['transactions']:
                        transaction = ImportedTransaction(
                            user_id=current_user.id,
                            raw_description=transaction_data['description'],
                            amount=transaction_data['amount'],
                            transaction_date=transaction_data['date'],
                            balance=transaction_data.get('balance'),
                            transaction_type=transaction_data['type'],
                            import_batch_id=result['batch_id'],
                            source_file=secure_filename(file.filename),
                            suggested_category=transaction_data.get('suggested_category'),
                            suggested_description=transaction_data.get('suggested_description'),
                            confidence_score=transaction_data.get('confidence_score'),
                            is_expense=(transaction_data['type'] == 'debit')
                        )
                        
                        db.session.add(transaction)
                        saved_count += 1
                    
                    db.session.commit()
                    print(f"DEBUG: Saved {saved_count} transactions to database")
                    
                    flash(f'Successfully imported {saved_count} transactions from {form.bank_name.data.upper()} statement.', 'success')
                    return redirect(url_for('imports.review_batch', batch_id=result['batch_id']))
                    
                else:
                    print(f"DEBUG: Processing failed with error: {result.get('error')}")
                    flash(f'Error processing PDF: {result.get("error", "Unknown error")}', 'error')
                    
            except Exception as e:
                print(f"DEBUG: Exception during processing: {str(e)}")
                flash(f'Error processing file: {str(e)}', 'error')
        else:
            print("DEBUG: File validation failed")
            flash('Please upload a valid PDF file.', 'error')
    else:
        if form.errors:
            print(f"DEBUG: Form validation errors: {form.errors}")
    
    return render_template('imports/upload.html', form=form)

@imports.route('/import_csv', methods=['GET', 'POST'])
@login_required
def upload_csv():
    """Upload and process CSV bank statement"""
    form = CSVImportForm()
    
    if form.validate_on_submit():
        file = form.csv_file.data
        
        if file and file.filename.lower().endswith('.csv'):
            try:
                # Read CSV content
                csv_content = file.read().decode('utf-8')
                
                # Process CSV
                result = process_csv_statement(
                    csv_content=csv_content,
                    date_column=form.date_column.data,
                    description_column=form.description_column.data,
                    amount_column=form.amount_column.data,
                    has_header=form.has_header.data,
                    filename=secure_filename(file.filename)
                )
                
                if result['success']:
                    # Save transactions to database
                    saved_count = 0
                    for transaction_data in result['transactions']:
                        transaction = ImportedTransaction(
                            user_id=current_user.id,
                            raw_description=transaction_data['description'],
                            amount=transaction_data['amount'],
                            transaction_date=transaction_data['date'],
                            balance=transaction_data.get('balance'),
                            transaction_type=transaction_data['type'],
                            import_batch_id=result['batch_id'],
                            source_file=secure_filename(file.filename),
                            suggested_category=transaction_data.get('suggested_category'),
                            suggested_description=transaction_data.get('suggested_description'),
                            confidence_score=transaction_data.get('confidence_score'),
                            is_expense=(transaction_data['type'] == 'debit')
                        )
                        
                        db.session.add(transaction)
                        saved_count += 1
                    
                    db.session.commit()
                    
                    flash(f'Successfully imported {saved_count} transactions from CSV file.', 'success')
                    return redirect(url_for('imports.review_batch', batch_id=result['batch_id']))
                    
                else:
                    flash(f'Error processing CSV: {result.get("error", "Unknown error")}', 'error')
                    
            except Exception as e:
                flash(f'Error processing CSV file: {str(e)}', 'error')
        else:
            flash('Please upload a valid CSV file.', 'error')
    
    return render_template('imports/upload_csv.html', form=form)

def process_csv_statement(csv_content: str, date_column: str, description_column: str, 
                         amount_column: str, has_header: bool, filename: str) -> dict:
    """Process CSV bank statement"""
    import csv
    import io
    from datetime import datetime
    import uuid
    from app.pdf_processor import BankStatementProcessor
    
    try:
        # Detect if this is a Lloyds Bank CSV based on headers
        is_lloyds = False
        first_line = csv_content.split('\n')[0] if csv_content else ''
        if 'Transaction Date,Transaction Type,Sort Code,Account Number' in first_line:
            is_lloyds = True
            print("DEBUG: Detected Lloyds Bank CSV format")
        
        transactions = []
        
        if is_lloyds:
            return process_lloyds_csv(csv_content, filename)
        
        csv_reader = csv.DictReader(io.StringIO(csv_content)) if has_header else csv.reader(io.StringIO(csv_content))
        
        processor = BankStatementProcessor('generic')
        
        for row_num, row in enumerate(csv_reader, 1):
            try:
                if has_header:
                    date_str = row.get(date_column, '')
                    description = row.get(description_column, '')
                    amount_str = row.get(amount_column, '')
                else:
                    # Assume first 3 columns are date, description, amount
                    if len(row) >= 3:
                        date_str = row[0]
                        description = row[1]  
                        amount_str = row[2]
                    else:
                        continue
                
                if not date_str or not description or not amount_str:
                    continue
                
                # Parse date
                transaction_date = processor._parse_date(date_str)
                if not transaction_date:
                    continue
                
                # Parse amount
                amount = processor._parse_amount(amount_str)
                if amount <= 0:
                    continue
                
                # Determine transaction type
                transaction_type = processor._determine_transaction_type(description, amount)
                
                # Auto-categorize
                category, confidence = processor.categorize_transaction(description)
                cleaned_desc = processor._clean_description(description)
                
                transaction = {
                    'date': transaction_date,
                    'description': description.strip(),
                    'amount': amount,
                    'type': transaction_type,
                    'suggested_category': category,
                    'suggested_description': cleaned_desc,
                    'confidence_score': confidence
                }
                
                transactions.append(transaction)
                
            except Exception as e:
                print(f"Error processing row {row_num}: {e}")
                continue
        
        batch_id = str(uuid.uuid4())
        
        return {
            'success': True,
            'batch_id': batch_id,
            'transactions': transactions,
            'total_transactions': len(transactions)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'transactions': [],
            'total_transactions': 0
        }


def categorize_lloyds_transaction(description: str, trans_type: str) -> tuple:
    """Enhanced categorization for Lloyds Bank transactions"""
    description_lower = description.lower()
    
    # Lloyds-specific merchant recognition
    lloyds_categories = {
        'food': {
            'keywords': ['tesco', 'asda', 'sainsbury', 'morrisons', 'aldi', 'lidl', 'waitrose',
                        'chopstix', 'amazon* rj', 'great indian', 'subway', 'ppoint'],
            'confidence': 0.9
        },
        'transportation': {
            'keywords': ['flix', 'fuel', 'petrol', 'parking', 'train', 'bus'],
            'confidence': 0.9
        },
        'utilities': {
            'keywords': ['lebara mobile', 'phone', 'mobile', 'internet', 'gas', 'electric'],
            'confidence': 0.9
        },
        'transfers': {
            'keywords': ['sneh r', 'shivam dubey', 's dubey', 'sakshi sharma', 'ritika sneh'],
            'confidence': 0.95
        },
        'rent': {
            'keywords': ['velour homes', 'alliance east lond', 'rent', 'housing'],
            'confidence': 0.95
        },
        'cash': {
            'keywords': ['lloyds bank cashba', 'atm', 'cash'],
            'confidence': 0.9
        },
        'shopping': {
            'keywords': ['amazon', 'selecta', 'maryland s', 'mary ley'],
            'confidence': 0.8
        }
    }
    
    # Enhanced categorization based on transaction type
    if trans_type == 'FPI' and any(keyword in description_lower for keyword in ['sneh', 'dubey', 'sharma']):
        return 'transfers', 0.95
    elif trans_type == 'FPO' and 'alliance' in description_lower:
        return 'rent', 0.95
    elif trans_type == 'CPT':  # Card payments
        # Check specific merchants
        for category, data in lloyds_categories.items():
            if any(keyword in description_lower for keyword in data['keywords']):
                return category, data['confidence']
        return 'shopping', 0.7
    
    # Standard categorization
    for category, data in lloyds_categories.items():
        if any(keyword in description_lower for keyword in data['keywords']):
            return category, data['confidence']
    
    return 'other', 0.3


def process_lloyds_csv(csv_content: str, filename: str) -> dict:
    """Process Lloyds Bank CSV format specifically"""
    import csv
    import io
    from datetime import datetime
    import uuid
    from app.pdf_processor import BankStatementProcessor
    
    try:
        transactions = []
        processor = BankStatementProcessor('lloyds')
        
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        for row_num, row in enumerate(csv_reader, 1):
            try:
                # Lloyds CSV columns:
                # Transaction Date,Transaction Type,Sort Code,Account Number,Transaction Description,Debit Amount,Credit Amount,Balance
                date_str = row.get('Transaction Date', '').strip()
                trans_type = row.get('Transaction Type', '').strip()
                description = row.get('Transaction Description', '').strip()
                debit_amount = row.get('Debit Amount', '').strip()
                credit_amount = row.get('Credit Amount', '').strip()
                balance_str = row.get('Balance', '').strip()
                
                if not date_str or not description:
                    continue
                
                # Parse date (DD/MM/YYYY format)
                try:
                    transaction_date = datetime.strptime(date_str, '%d/%m/%Y').date()
                except ValueError:
                    print(f"DEBUG: Could not parse date: {date_str}")
                    continue
                
                # Determine amount and transaction type
                amount = 0.0
                transaction_direction = 'debit'  # Default
                
                if credit_amount and credit_amount.replace('.', '').replace(',', '').isdigit():
                    amount = processor._parse_amount(credit_amount)
                    transaction_direction = 'credit'
                elif debit_amount and debit_amount.replace('.', '').replace(',', '').isdigit():
                    amount = processor._parse_amount(debit_amount)
                    transaction_direction = 'debit'
                
                if amount <= 0:
                    continue
                
                # Parse balance
                balance = processor._parse_amount(balance_str) if balance_str else None
                
                # Use Lloyds-specific transaction type mapping
                if trans_type in ['FPI', 'TFR']:
                    # Faster Payment In or Transfer - typically credit
                    if transaction_direction == 'debit':
                        # But if it's in debit column, it's actually outgoing
                        pass
                    else:
                        transaction_direction = 'credit'
                elif trans_type in ['DEB', 'FPO', 'CPT']:
                    # Debit, Faster Payment Out, Card Payment - typically debit
                    transaction_direction = 'debit'
                
                # Auto-categorize using enhanced Lloyds-specific logic
                category, confidence = categorize_lloyds_transaction(description, trans_type)
                cleaned_desc = processor._clean_description(description)
                
                transaction = {
                    'date': transaction_date,
                    'description': description,
                    'amount': amount,
                    'balance': balance,
                    'type': transaction_direction,
                    'lloyds_type': trans_type,
                    'suggested_category': category,
                    'suggested_description': cleaned_desc,
                    'confidence_score': confidence
                }
                
                transactions.append(transaction)
                print(f"DEBUG: Parsed Lloyds CSV transaction: {date_str} - {description} - {trans_type} - £{amount}")
                
            except Exception as e:
                print(f"Error processing Lloyds CSV row {row_num}: {e}")
                continue
        
        batch_id = str(uuid.uuid4())
        
        print(f"DEBUG: Successfully processed {len(transactions)} Lloyds CSV transactions")
        
        return {
            'success': True,
            'batch_id': batch_id,
            'transactions': transactions,
            'total_transactions': len(transactions),
            'bank_name': 'Lloyds Bank',
            'format': 'CSV'
        }
        
    except Exception as e:
        print(f"DEBUG: Error processing Lloyds CSV: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'transactions': [],
            'total_transactions': 0
        }

@imports.route('/review/<batch_id>')
@login_required
def review_batch(batch_id):
    """Review imported transactions batch"""
    transactions = ImportedTransaction.query.filter_by(
        user_id=current_user.id,
        import_batch_id=batch_id,
        is_processed=False
    ).order_by(ImportedTransaction.transaction_date.desc()).all()
    
    if not transactions:
        flash('No transactions found for review.', 'info')
        return redirect(url_for('imports.import_history'))
    
    bulk_form = BulkTransactionReviewForm()
    
    # Calculate summary statistics
    total_transactions = len(transactions)
    total_amount = sum(t.amount for t in transactions if t.is_expense)
    high_confidence = sum(1 for t in transactions if t.confidence_score and t.confidence_score > 0.8)
    
    summary = {
        'total_transactions': total_transactions,
        'total_amount': total_amount,
        'high_confidence': high_confidence,
        'confidence_percentage': (high_confidence / total_transactions * 100) if total_transactions > 0 else 0
    }
    
    return render_template('imports/review_batch.html', 
                         transactions=transactions, 
                         batch_id=batch_id,
                         bulk_form=bulk_form,
                         summary=summary)

@imports.route('/review_transaction/<int:transaction_id>', methods=['GET', 'POST'])
@login_required
def review_transaction(transaction_id):
    """Review and categorize individual transaction"""
    transaction = ImportedTransaction.query.filter_by(
        id=transaction_id,
        user_id=current_user.id
    ).first_or_404()
    
    form = TransactionReviewForm()
    
    if form.validate_on_submit():
        # Update transaction with user review
        transaction.is_expense = form.is_expense.data
        transaction.suggested_category = form.category.data
        transaction.suggested_description = form.description.data or transaction.raw_description
        transaction.user_notes = form.user_notes.data
        transaction.is_reviewed = True
        
        # Add tags if provided
        if form.tags.data:
            # Store tags as comma-separated string for now
            transaction.user_notes = f"Tags: {form.tags.data}\n{transaction.user_notes or ''}".strip()
        
        db.session.commit()
        
        flash('Transaction updated successfully.', 'success')
        return redirect(url_for('imports.review_batch', batch_id=transaction.import_batch_id))
    
    # Pre-populate form with suggestions
    form.is_expense.data = transaction.is_expense
    form.category.data = transaction.suggested_category
    form.description.data = transaction.suggested_description or transaction.raw_description
    
    return render_template('imports/review_transaction.html', 
                         transaction=transaction, 
                         form=form)

@imports.route('/bulk_action/<batch_id>', methods=['POST'])
@login_required
def bulk_action(batch_id):
    """Handle bulk actions on transaction batch"""
    form = BulkTransactionReviewForm()
    
    if form.validate_on_submit():
        transactions = ImportedTransaction.query.filter_by(
            user_id=current_user.id,
            import_batch_id=batch_id,
            is_processed=False
        ).all()
        
        if form.approve_all.data:
            # Approve all transactions with suggestions
            approved_count = 0
            for transaction in transactions:
                if transaction.suggested_category and transaction.suggested_category != 'ignore':
                    transaction.is_approved = True
                    transaction.is_reviewed = True
                    approved_count += 1
            
            db.session.commit()
            flash(f'Approved {approved_count} transactions for import.', 'success')
            return redirect(url_for('imports.create_expenses', batch_id=batch_id))
            
        elif form.delete_batch.data:
            # Delete entire batch
            for transaction in transactions:
                db.session.delete(transaction)
            
            db.session.commit()
            flash('Import batch deleted successfully.', 'info')
            return redirect(url_for('imports.import_history'))
            
        elif form.export_csv.data:
            # Export to CSV (implement later)
            flash('CSV export functionality coming soon!', 'info')
            
    return redirect(url_for('imports.review_batch', batch_id=batch_id))

@imports.route('/create_expenses/<batch_id>')
@login_required
def create_expenses(batch_id):
    """Create expenses from approved imported transactions"""
    from app.models import Expense
    
    approved_transactions = ImportedTransaction.query.filter_by(
        user_id=current_user.id,
        import_batch_id=batch_id,
        is_approved=True,
        is_processed=False
    ).all()
    
    created_count = 0
    for transaction in approved_transactions:
        if transaction.suggested_category != 'ignore' and transaction.is_expense:
            # Create expense from transaction
            expense = Expense(
                user_id=current_user.id,
                amount=transaction.amount,
                description=transaction.suggested_description or transaction.raw_description,
                category=transaction.suggested_category,
                date=transaction.transaction_date,
                tags=f"imported,{batch_id[:8]}"  # Add import tags
            )
            
            db.session.add(expense)
            
            # Link transaction to created expense
            transaction.expense_id = expense.id
            transaction.is_processed = True
            
            created_count += 1
    
    db.session.commit()
    
    flash(f'Successfully created {created_count} expenses from imported transactions.', 'success')
    return redirect(url_for('expenses.list_expenses'))

@imports.route('/history')
@login_required
def import_history():
    """View import history"""
    # Get unique batches with summary info
    batch_query = db.session.query(
        ImportedTransaction.import_batch_id,
        ImportedTransaction.source_file,
        ImportedTransaction.import_date,
        db.func.count(ImportedTransaction.id).label('total_count'),
        db.func.sum(db.case((ImportedTransaction.is_processed == True, 1), else_=0)).label('processed_count'),
        db.func.sum(ImportedTransaction.amount).label('total_amount')
    ).filter_by(
        user_id=current_user.id
    ).group_by(
        ImportedTransaction.import_batch_id,
        ImportedTransaction.source_file,
        ImportedTransaction.import_date
    ).order_by(ImportedTransaction.import_date.desc()).all()
    
    batches = []
    for batch in batch_query:
        batches.append({
            'batch_id': batch.import_batch_id,
            'source_file': batch.source_file,
            'import_date': batch.import_date,
            'total_count': batch.total_count,
            'processed_count': batch.processed_count or 0,
            'pending_count': batch.total_count - (batch.processed_count or 0),
            'total_amount': batch.total_amount or 0,
            'status': 'Completed' if batch.processed_count == batch.total_count else 'Pending'
        })
    
    return render_template('imports/history.html', batches=batches)

@imports.route('/delete_batch/<batch_id>', methods=['POST'])
@login_required
def delete_batch(batch_id):
    """Delete an import batch"""
    transactions = ImportedTransaction.query.filter_by(
        user_id=current_user.id,
        import_batch_id=batch_id
    ).all()
    
    for transaction in transactions:
        db.session.delete(transaction)
    
    db.session.commit()
    flash('Import batch deleted successfully.', 'info')
    return redirect(url_for('imports.import_history'))

@imports.route('/test_processing')
@login_required 
def test_processing():
    """Test route for PDF processing functionality"""
    from app.pdf_processor import BankStatementProcessor
    
    # Sample bank statement text
    sample_text = """
Date        Description                     Amount      Balance
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
    
    try:
        processor = BankStatementProcessor('generic')
        transactions = processor.parse_transactions(sample_text)
        
        # Auto-categorize
        for trans in transactions:
            category, confidence = processor.categorize_transaction(trans['description'])
            trans['suggested_category'] = category
            trans['confidence_score'] = confidence
            trans['suggested_description'] = processor._clean_description(trans['description'])
        
        return f"""
        <h2>PDF Processing Test Results</h2>
        <p>Found {len(transactions)} transactions:</p>
        <ul>
        {''.join([f"<li><strong>{t['date']}</strong> - {t['description']} - £{t['amount']:.2f} ({t['suggested_category']}, {t['confidence_score']:.1f})</li>" for t in transactions])}
        </ul>
        <a href="/imports/import">Back to Import</a>
        """
    except Exception as e:
        return f"<h2>Error Testing PDF Processing</h2><p>{str(e)}</p><a href='/imports/import'>Back to Import</a>"

@imports.route('/api/transaction_suggestions/<int:transaction_id>')
@login_required
def transaction_suggestions(transaction_id):
    """API endpoint for transaction categorization suggestions"""
    transaction = ImportedTransaction.query.filter_by(
        id=transaction_id,
        user_id=current_user.id
    ).first_or_404()
    
    # Get similar transactions from user's expense history
    from app.models import Expense
    
    similar_expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.description.ilike(f'%{transaction.raw_description[:20]}%')
    ).limit(5).all()
    
    suggestions = {
        'suggested_category': transaction.suggested_category,
        'suggested_description': transaction.suggested_description,
        'confidence_score': transaction.confidence_score,
        'similar_transactions': [
            {
                'description': exp.description,
                'category': exp.category,
                'amount': exp.amount
            } for exp in similar_expenses
        ]
    }
    
    return jsonify(suggestions)
