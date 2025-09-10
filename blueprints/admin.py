# Admin panel blueprint
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from models import db, User, Subscription, VPNKey, VPNServer, EmailNotification
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Доступ запрещен. Требуются права администратора.', 'error')
            return redirect(url_for('public.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def index():
    """Admin dashboard"""
    # Statistics
    total_users = User.query.count()
    active_subscriptions = Subscription.query.filter_by(is_active=True).count()
    total_revenue = db.session.query(db.func.sum(Subscription.amount_usd))\
                             .filter(Subscription.amount_usd > 0).scalar() or 0
    active_keys = VPNKey.query.filter_by(is_active=True).count()
    
    # Recent activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_subscriptions = Subscription.query.order_by(Subscription.created_at.desc())\
                                            .limit(5).all()
    
    # Server status
    servers = VPNServer.query.all()
    
    return render_template('admin/index.html',
                         total_users=total_users,
                         active_subscriptions=active_subscriptions,
                         total_revenue=total_revenue,
                         active_keys=active_keys,
                         recent_users=recent_users,
                         recent_subscriptions=recent_subscriptions,
                         servers=servers)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """Users management"""
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc())\
                     .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('admin/users.html', users=users)

@admin_bp.route('/subscriptions')
@login_required
@admin_required
def subscriptions():
    """Subscriptions management"""
    page = request.args.get('page', 1, type=int)
    subscriptions = Subscription.query.order_by(Subscription.created_at.desc())\
                                     .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('admin/subscriptions.html', subscriptions=subscriptions)

@admin_bp.route('/servers')
@login_required
@admin_required
def servers():
    """VPN servers management"""
    servers = VPNServer.query.all()
    return render_template('admin/servers.html', servers=servers)

@admin_bp.route('/emails')
@login_required
@admin_required
def emails():
    """Email notifications log"""
    page = request.args.get('page', 1, type=int)
    emails = EmailNotification.query.order_by(EmailNotification.sent_at.desc())\
                                   .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('admin/emails.html', emails=emails)