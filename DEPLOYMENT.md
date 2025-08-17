# CouplesBudget Pro - PythonAnywhere Deployment Guide

## Overview
CouplesBudget Pro is a Flask-based financial management application for couples, optimized for PythonAnywhere hosting.

## Features
- 🔐 Secure user authentication and authorization
- 💰 Expense tracking with categories and priorities
- 📊 Budget management with alerts
- 🎯 Financial goal setting and tracking
- 💼 Investment portfolio tracking
- 👥 Partner linking for shared finances
- 📈 Analytics and reporting
- 📱 Responsive design for mobile and desktop

## PythonAnywhere Deployment Instructions

### 1. Prerequisites
- PythonAnywhere account (free or paid)
- Git repository on GitHub
- MySQL database (included with paid accounts)

### 2. Clone Repository on PythonAnywhere
```bash
# In PythonAnywhere Bash console
cd /home/yourusername
git clone https://github.com/yourusername/couplesbudgetpro.git
cd couplesbudgetpro
```

### 3. Set Up Virtual Environment
```bash
# Create virtual environment
python3.10 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Database Configuration
For MySQL on PythonAnywhere:
```python
# In your PythonAnywhere files, create .env file:
SECRET_KEY=your-secret-key-here
DATABASE_URL=mysql://yourusername:yourpassword@yourusername.mysql.pythonanywhere-services.com/yourusername$dbname
FLASK_CONFIG=production
```

### 5. Web App Configuration
1. Go to PythonAnywhere Dashboard → Web
2. Create new web app
3. Choose Manual configuration → Python 3.10
4. Set source code directory: `/home/yourusername/couplesbudgetpro`
5. Set working directory: `/home/yourusername/couplesbudgetpro`
6. Edit WSGI file (see wsgi.py in repository)

### 6. Static Files Configuration
In PythonAnywhere Web tab:
- URL: `/static/`
- Directory: `/home/yourusername/couplesbudgetpro/static/`

### 7. Initialize Database
```bash
# In PythonAnywhere console
cd /home/yourusername/couplesbudgetpro
source venv/bin/activate
python
>>> from run import app
>>> from app import db
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

### 8. Environment Variables
Create `.env` file in project root:
```
SECRET_KEY=your-super-secret-key-change-this-in-production
DATABASE_URL=mysql://username:password@yourusername.mysql.pythonanywhere-services.com/yourusername$couplesbudget
FLASK_CONFIG=production
ADMIN_EMAIL=your-email@example.com
```

### 9. File Permissions
```bash
# Ensure proper permissions
chmod -R 755 /home/yourusername/couplesbudgetpro
```

## GitHub Repository Structure
```
couplesbudgetpro/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── forms.py
│   ├── utils.py
│   ├── errors.py
│   ├── security.py
│   └── routes/
├── templates/
├── static/
├── tests/
├── requirements.txt
├── wsgi.py
├── run.py
├── config.py
├── .env.example
├── .gitignore
├── README.md
└── DEPLOYMENT.md
```

## Troubleshooting

### Common Issues:
1. **Import errors**: Check Python version and virtual environment
2. **Database connection**: Verify DATABASE_URL format for PythonAnywhere MySQL
3. **Static files not loading**: Check static files configuration in Web tab
4. **Module not found**: Ensure all dependencies are in requirements.txt

### PythonAnywhere Specific:
- Free accounts have limited CPU seconds
- File uploads are limited to 100MB total
- MySQL databases only on paid accounts (SQLite for free accounts)

## Support
- PythonAnywhere Help: https://help.pythonanywhere.com/
- Flask Documentation: https://flask.palletsprojects.com/
