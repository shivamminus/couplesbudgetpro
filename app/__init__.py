# Application package
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
import os
import logging
from logging.handlers import RotatingFileHandler

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()

def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG') or 'default'
    
    # Set template and static folders relative to the parent directory
    template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
    static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static')
    
    app = Flask(__name__, 
                template_folder=template_folder,
                static_folder=static_folder)
    
    # Import and apply configuration
    from config import config
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    login_manager.login_view = 'auth.login'
    
    # Import models to register them with SQLAlchemy
    from app.models import User, Expense, Budget, Goal, Investment, PartnerRequest
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.expenses import expenses_bp
    from app.routes.budgets import budgets_bp
    from app.routes.goals import goals_bp
    from app.routes.analytics import analytics_bp
    from app.routes.profile import profile_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(expenses_bp, url_prefix='/expenses')
    app.register_blueprint(budgets_bp, url_prefix='/budgets')
    app.register_blueprint(goals_bp, url_prefix='/goals')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(profile_bp, url_prefix='/profile')
    
    # Error handlers
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)
    
    # Set up logging for production
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/moneymanagement.log', 
                                         maxBytes=10240000, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Money Management App startup')
    
    return app
