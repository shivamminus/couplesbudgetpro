# Money Management App

A comprehensive personal finance management application built with Flask, designed to help users track expenses, manage budgets, and gain insights into their financial habits. Features secure user authentication, expense categorization, and analytics dashboard.

## Features

- **User Authentication**: Secure registration, login, and profile management
- **Expense Tracking**: Add, edit, and categorize expenses with detailed descriptions
- **Category Management**: Organize expenses with customizable categories
- **Dashboard Analytics**: Visual insights into spending patterns and trends
- **Admin Panel**: Administrative interface for user and system management
- **Responsive Design**: Mobile-friendly interface for on-the-go expense tracking
- **Secure**: Password hashing, CSRF protection, and secure session management

## Technology Stack

- **Backend**: Python 3.8+, Flask, SQLAlchemy
- **Database**: SQLite (development), MySQL (production)
- **Frontend**: HTML5, CSS3, Bootstrap 4, Chart.js
- **Security**: Flask-WTF (CSRF), Werkzeug (password hashing)
- **Testing**: Python unittest framework

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/moneymanagementapp.git
   cd moneymanagementapp
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # or
   source venv/bin/activate  # macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```
   FLASK_APP=run.py
   FLASK_ENV=development
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=sqlite:///money_management.db
   ```

5. **Initialize the database**
   ```bash
   python run.py
   ```
   The app will create the database and tables automatically on first run.

6. **Run the application**
   ```bash
   python run.py
   ```
   Open your browser to `http://localhost:5000`

### Production Deployment (PythonAnywhere)

For detailed deployment instructions to PythonAnywhere, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Project Structure

```
moneymanagementapp/
├── app/
│   ├── __init__.py          # Application factory
│   ├── models.py            # Database models
│   ├── auth/                # Authentication blueprint
│   │   ├── __init__.py
│   │   ├── routes.py        # Auth routes
│   │   └── forms.py         # Auth forms
│   ├── main/                # Main application routes
│   │   ├── __init__.py
│   │   ├── routes.py        # Main routes
│   │   └── forms.py         # Main forms
│   ├── static/              # CSS, JS, images
│   │   ├── css/
│   │   ├── js/
│   │   └── img/
│   └── templates/           # HTML templates
│       ├── base.html
│       ├── auth/
│       └── main/
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_expenses.py
│   └── test_models.py
├── config.py               # Configuration settings
├── run.py                  # Application entry point
├── wsgi.py                 # WSGI entry point for production
├── requirements.txt        # Python dependencies
├── requirements_pythonanywhere.txt  # PythonAnywhere specific
├── DEPLOYMENT.md          # Deployment guide
└── README.md              # This file
```
- Visit the analytics page for detailed insights
- View spending trends, category breakdowns, and comparisons
- Export data for external analysis
- Get AI-powered insights and recommendations

## File Structure

```
moneymanagementapp/
├── app.py                 # Main application file
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── venv/                # Virtual environment
├── static/              # Static files (CSS, JS, images)
│   └── css/
│       └── custom.css   # Custom styling
└── templates/           # HTML templates
    ├── base.html        # Base template
    ├── index.html       # Landing page
    ├── login.html       # Login page
    ├── register.html    # Registration page
    ├── dashboard.html   # Main dashboard
    ├── expenses.html    # Expense list
    ├── add_expense.html # Add expense form
    ├── budgets.html     # Budget overview
    ├── set_budget.html  # Set budget form
    ├── goals.html       # Goals overview
    ├── add_goal.html    # Add goal form
    ├── analytics.html   # Analytics dashboard
    ├── suggestions.html # AI suggestions
    └── profile.html     # User profile
```

## Database Schema

### Users
- User authentication and profile information
- Partner linking for shared financial management

### Expenses
- Detailed expense tracking with categories, amounts, dates
- Recurring expense support
## Usage

### Creating Your First Account

1. Visit the application homepage
2. Click "Register" to create a new account
3. Fill in your details and submit the form
4. Log in with your new credentials

### Adding Expenses

1. Navigate to "Add Expense" from the main menu
2. Fill in the expense details:
   - Amount
   - Category
   - Description
   - Date
3. Submit the form to save your expense

### Managing Categories

1. Go to "Categories" in the main menu
2. Add new categories or edit existing ones
3. Categories help organize and analyze your spending

### Viewing Analytics

1. Visit the Dashboard to see:
   - Total expenses by category
   - Monthly spending trends
   - Recent transactions
   - Budget insights

## API Endpoints

The application provides a RESTful interface:

- `GET /` - Homepage and dashboard
- `POST /auth/register` - User registration
- `POST /auth/login` - User authentication
- `GET /expenses` - View all expenses
- `POST /expenses/add` - Add new expense
- `PUT /expenses/<id>` - Update expense
- `DELETE /expenses/<id>` - Delete expense
- `GET /categories` - View categories
- `POST /categories/add` - Add new category

## Testing

Run the test suite:

```bash
python -m unittest discover tests
```

Test coverage includes:
- User authentication flows
- Expense CRUD operations
- Category management
- Database models
- Form validation
- Security features

## Database Schema

### Users Table
- id (Primary Key)
- username (Unique)
- email (Unique)
- password_hash
- is_admin (Boolean)
- created_at

### Expenses Table
- id (Primary Key)
- user_id (Foreign Key)
- amount (Decimal)
- category
- description
- date
- created_at

## Security Features

- Password hashing using Werkzeug
- CSRF protection on all forms
- Secure session management
- SQL injection prevention through SQLAlchemy ORM
- Input validation and sanitization
- Admin role-based access control

## Configuration

The application supports multiple environments:

- **Development**: SQLite database, debug mode enabled
- **Testing**: In-memory database, testing configurations
- **Production**: MySQL database, optimized for PythonAnywhere

Environment-specific settings are managed in `config.py`.

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Ensure DATABASE_URL is correctly set
   - Check database credentials and connectivity

2. **Import Errors**
   - Verify virtual environment is activated
   - Ensure all dependencies are installed

3. **Static Files Not Loading**
   - Check Flask configuration for static files
   - Verify file paths in templates

### Getting Help

- Check the [Issues](https://github.com/yourusername/moneymanagementapp/issues) page
- Review the deployment guide in `DEPLOYMENT.md`
- Ensure all environment variables are properly set

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Flask community for the excellent web framework
- Bootstrap team for the responsive CSS framework
- Chart.js for beautiful data visualizations
- PythonAnywhere for reliable hosting platform

## Version History

- **v1.0.0** - Initial release with core expense tracking features
- **v1.1.0** - Added category management and basic analytics
- **v1.2.0** - Enhanced security features and admin panel
- **v2.0.0** - Production-ready with comprehensive testing and deployment guides

## Contact

For questions or support, please open an issue on GitHub or contact the maintainer.

---

**Happy Budget Tracking!** 💰📊
