# CouplesBudget Pro

A comprehensive Flask web application designed for couples to manage their monthly expenses, budgets, and financial goals together. Features AI-powered insights, detailed analytics, and personalized recommendations for saving and investing.

## Features

### 💰 Expense Tracking
- Track all expenses with detailed categories and subcategories
- Set recurring expenses (monthly, weekly, yearly)
- Priority levels for better expense management
- Custom tags for advanced filtering
- Import/export functionality

### 📊 Budget Management
- Set monthly budgets for different categories
- Real-time budget monitoring with visual indicators
- Customizable alert thresholds
- Budget vs actual spending analysis
- Historical budget performance

### 🎯 Financial Goals
- Create and track multiple financial goals
- Progress visualization with completion percentages
- Goal categories: Emergency fund, vacation, home purchase, etc.
- Automated savings recommendations
- Goal achievement celebrations

### 📈 Advanced Analytics
- Interactive charts and graphs
- Spending trend analysis
- Category breakdowns and comparisons
- Monthly and yearly financial reports
- Export analytics data

### 🤖 AI-Powered Insights
- Personalized money-saving suggestions
- Investment recommendations based on spending patterns
- Financial health score
- Predictive analytics for future spending
- Custom financial advice

### 👥 Couple-Focused Features
- Shared expense tracking
- Joint budget management
- Combined financial goals
- Partner spending insights
- Collaborative financial planning

## Technology Stack

- **Backend**: Flask, SQLAlchemy, Flask-Login
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Database**: SQLite (development), PostgreSQL (production ready)
- **Charts**: Plotly.js for interactive visualizations
- **AI/ML**: scikit-learn for predictive analytics
- **Forms**: Flask-WTF, WTForms

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd moneymanagementapp
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set environment variables** (optional)
   ```bash
   # For enhanced security in production
   export SECRET_KEY=your-secret-key-here
   export DATABASE_URL=your-database-url-here
   export OPENAI_API_KEY=your-openai-api-key-here
   ```

6. **Initialize the database**
   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

7. **Run the application**
   ```bash
   python app.py
   ```

8. **Access the application**
   Open your browser and go to `http://localhost:5000`

## Usage

### Getting Started
1. Register for a new account or login with existing credentials
2. Add your first expense to start tracking your spending
3. Set up budgets for different expense categories
4. Create financial goals to work towards
5. Explore analytics and AI suggestions for better financial management

### Key Features Usage

#### Adding Expenses
- Click "Add Expense" from the dashboard or sidebar
- Fill in the amount, description, category, and other details
- Set recurring expenses for regular payments
- Use tags for better organization

#### Setting Budgets
- Navigate to "Set Budget" from the sidebar
- Choose a category and set your monthly budget amount
- Set alert thresholds to get notified when approaching limits
- Review budget performance on the budgets page

#### Creating Goals
- Go to "Add Goal" to create new financial goals
- Use quick templates for common goals like emergency funds
- Track progress with visual indicators
- Get recommendations for monthly savings amounts

#### Viewing Analytics
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
- Priority levels and custom tags

### Budgets
- Monthly budget limits by category
- Alert thresholds and performance tracking

### Goals
- Financial goal tracking with target amounts and dates
- Progress monitoring and completion status

### Investments (Future)
- Investment portfolio tracking
- Performance monitoring and recommendations

## Features in Development

- [ ] Partner account linking and shared access
- [ ] Mobile app with offline support
- [ ] Bank account integration for automatic expense import
- [ ] Advanced investment tracking and recommendations
- [ ] Email notifications and alerts
- [ ] Multi-currency support
- [ ] Data export to popular formats (PDF, Excel)
- [ ] Receipt photo upload and OCR processing

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please create an issue on the GitHub repository or contact the development team.

## Acknowledgments

- Bootstrap for the responsive UI framework
- Plotly.js for interactive charts and graphs
- Font Awesome for icons
- Flask community for the excellent web framework
- scikit-learn for machine learning capabilities

---

**CouplesBudget Pro** - Empowering couples to achieve their financial dreams together! 💑💰
