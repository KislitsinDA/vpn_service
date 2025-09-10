# Flask VPN service main application - python_database integration
import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import secrets

from models import db, User, Subscription, VPNKey, VPNServer, EmailNotification

# Import blueprints
from blueprints.auth import auth_bp
from blueprints.public import public_bp
from blueprints.billing import billing_bp
from blueprints.dashboard import dashboard_bp
from blueprints.admin import admin_bp

def create_app():
    """Application factory"""
    app = Flask(__name__)
    
    # Configuration
    app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_urlsafe(32)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["WTF_CSRF_TIME_LIMIT"] = None  # No time limit for CSRF tokens
    
    # Initialize extensions
    db.init_app(app)
    csrf = CSRFProtect(app)
    
    # Login manager setup
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(public_bp)
    app.register_blueprint(billing_bp, url_prefix='/billing')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    with app.app_context():
        # Create all database tables
        db.create_all()
        
        # Create default admin user if not exists (only in development)
        if app.debug and not User.query.filter_by(is_admin=True).first():
            admin_email = os.environ.get('ADMIN_EMAIL', 'admin@gshvpn.com')
            admin_password = os.environ.get('ADMIN_PASSWORD')
            if admin_password:  # Only create if password is provided via env
                admin = User(
                    email=admin_email,
                    is_admin=True
                )
                admin.set_password(admin_password)
                db.session.add(admin)
            
        # Create default VPN server if not exists
        server = VPNServer.query.first()
        if not server:
            server = VPNServer(
                name='Main Server',
                host='5.181.3.114',
                outline_api_url=os.environ.get('OUTLINE_API_URL', 'https://5.181.3.114:33297/YGjdhN4YLC1kXe2pJ5sy0A'),
                max_clients=5
            )
            db.session.add(server)
        
        try:
            db.session.commit()
        except Exception as e:
            print(f"Database setup error: {e}")
            db.session.rollback()
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)