# Database models for VPN service - python_database integration
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import DeclarativeBase
import secrets
import string

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class User(UserMixin, db.Model):
    """User model for authentication and account management"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Relations
    subscriptions = db.relationship('Subscription', backref='user', lazy=True, cascade='all, delete-orphan')
    vpn_keys = db.relationship('VPNKey', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_active_subscription(self):
        """Get current active subscription"""
        return Subscription.query.filter_by(
            user_id=self.id,
            is_active=True
        ).filter(
            Subscription.expires_at > datetime.utcnow()
        ).first()
    
    def __repr__(self):
        return f'<User {self.email}>'

class Subscription(db.Model):
    """User subscription model"""
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan = db.Column(db.String(50), nullable=False)  # free, 1m, 3m
    amount_usd = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    payment_id = db.Column(db.String(255), nullable=True)  # Stripe payment ID
    
    def is_expired(self):
        """Check if subscription is expired"""
        if not self.expires_at:
            return False  # Free plan never expires
        return datetime.utcnow() > self.expires_at
    
    def days_remaining(self):
        """Get days remaining until expiration"""
        if not self.expires_at:
            return None  # Free plan
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)
    
    @staticmethod
    def get_plan_details():
        """Get available subscription plans"""
        return {
            'free': {'amount': 0, 'duration_days': None, 'name': 'Бесплатно'},
            '1m': {'amount': 15, 'duration_days': 30, 'name': '1 месяц'},
            '3m': {'amount': 29, 'duration_days': 90, 'name': '3 месяца'}
        }
    
    def __repr__(self):
        return f'<Subscription {self.plan} for user {self.user_id}>'

class VPNKey(db.Model):
    """VPN access keys model"""
    __tablename__ = 'vpn_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id'), nullable=False)
    token = db.Column(db.Text, nullable=False)  # VPN access key/config
    server_id = db.Column(db.Integer, db.ForeignKey('vpn_servers.id'), nullable=True)
    outline_key_id = db.Column(db.String(100), nullable=True)  # Outline server key ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relations
    subscription = db.relationship('Subscription', backref='vpn_keys')
    server = db.relationship('VPNServer', backref='active_keys')
    
    def is_expired(self):
        """Check if key is expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @staticmethod
    def generate_key_token():
        """Generate random access token"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(32))
    
    def __repr__(self):
        return f'<VPNKey {self.id} for user {self.user_id}>'

class VPNServer(db.Model):
    """VPN servers management model"""
    __tablename__ = 'vpn_servers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    host = db.Column(db.String(255), nullable=False)
    port = db.Column(db.Integer, default=22)
    outline_api_url = db.Column(db.String(500), nullable=True)  # Outline management URL
    ssh_private_key = db.Column(db.Text, nullable=True)  # SSH private key for server access
    max_clients = db.Column(db.Integer, default=5)
    active_clients = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_health_check = db.Column(db.DateTime, nullable=True)
    
    def is_available(self):
        """Check if server has available slots"""
        return self.active_clients < self.max_clients and self.is_active
    
    def get_load_percentage(self):
        """Get server load percentage"""
        if self.max_clients == 0:
            return 100
        return (self.active_clients / self.max_clients) * 100
    
    @staticmethod
    def get_available_server():
        """Get the best available server"""
        return VPNServer.query.filter_by(is_active=True).filter(
            VPNServer.active_clients < VPNServer.max_clients
        ).order_by(VPNServer.active_clients.asc()).first()
    
    def __repr__(self):
        return f'<VPNServer {self.name} ({self.host})>'

class EmailNotification(db.Model):
    """Email notifications log"""
    __tablename__ = 'email_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    template = db.Column(db.String(100), nullable=False)  # welcome, payment_success, expiring_soon, expired
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    success = db.Column(db.Boolean, default=False)
    error_message = db.Column(db.Text, nullable=True)
    
    # Relations
    user = db.relationship('User', backref='email_notifications')
    
    def __repr__(self):
        return f'<EmailNotification {self.template} to {self.email}>'