"""Analytics and reporting routes"""

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from collections import defaultdict
import json

import plotly
import plotly.graph_objs as go
import plotly.express as px

from app.models import Expense
from app.utils import get_couple_user_ids
from app import db

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/')
@login_required
def analytics():
    """Analytics dashboard with charts and insights"""
    user_ids = get_couple_user_ids(current_user.id)
    
    # Get all expenses for analysis
    expenses = Expense.query.filter(Expense.user_id.in_(user_ids)).all()
    
    if not expenses:
        return render_template('analytics.html', 
                             spending_chart=None, 
                             trend_chart=None, 
                             category_chart=None)
    
    # Create spending by category chart
    category_data = defaultdict(float)
    for expense in expenses:
        category_data[expense.category.title()] += expense.amount
    
    fig1 = go.Figure(data=[go.Pie(
        labels=list(category_data.keys()),
        values=list(category_data.values()),
        title='Combined Spending by Category'
    )])
    spending_chart = json.dumps(fig1, cls=plotly.utils.PlotlyJSONEncoder)
    
    # Create monthly spending trend
    monthly_data = defaultdict(float)
    for expense in expenses:
        month_key = expense.date.strftime('%Y-%m')
        monthly_data[month_key] += expense.amount
    
    sorted_months = sorted(monthly_data.keys())
    amounts = [monthly_data[month] for month in sorted_months]
    
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=sorted_months, 
        y=amounts, 
        mode='lines+markers', 
        name='Combined Monthly Spending'
    ))
    fig2.update_layout(
        title='Combined Monthly Spending Trend', 
        xaxis_title='Month', 
        yaxis_title='Amount (£)'
    )
    trend_chart = json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder)
    
    # Create category comparison chart
    fig3 = px.bar(
        x=list(category_data.keys()), 
        y=list(category_data.values()), 
        title='Combined Category Spending Comparison'
    )
    fig3.update_layout(xaxis_title='Category', yaxis_title='Amount (£)')
    category_chart = json.dumps(fig3, cls=plotly.utils.PlotlyJSONEncoder)
    
    return render_template('analytics.html', 
                         spending_chart=spending_chart,
                         trend_chart=trend_chart,
                         category_chart=category_chart)

@analytics_bp.route('/suggestions')
@login_required
def suggestions():
    """AI-powered savings suggestions"""
    from app.utils import generate_savings_suggestions, generate_investment_recommendations
    
    suggestions = generate_savings_suggestions(current_user.id)
    
    # Calculate potential monthly savings
    monthly_savings = sum(s.get('potential_savings', 0) for s in suggestions)
    investments = generate_investment_recommendations(current_user.id, monthly_savings)
    
    return render_template('suggestions.html', 
                         suggestions=suggestions, 
                         investments=investments,
                         monthly_savings=monthly_savings)
