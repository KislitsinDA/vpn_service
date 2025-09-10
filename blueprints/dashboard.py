# User dashboard blueprint
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Subscription, VPNKey
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    """User dashboard"""
    # Get user's active subscription
    subscription = current_user.get_active_subscription()
    
    # Get user's VPN keys
    vpn_keys = VPNKey.query.filter_by(user_id=current_user.id, is_active=True)\
                          .order_by(VPNKey.created_at.desc()).all()
    
    # Get subscription history
    subscription_history = Subscription.query.filter_by(user_id=current_user.id)\
                                            .order_by(Subscription.created_at.desc()).all()
    
    return render_template('dashboard/index.html', 
                         subscription=subscription,
                         vpn_keys=vpn_keys,
                         subscription_history=subscription_history)

@dashboard_bp.route('/subscription')
@login_required
def subscription():
    """Subscription management"""
    subscription = current_user.get_active_subscription()
    plans = Subscription.get_plan_details()
    
    return render_template('dashboard/subscription.html', 
                         subscription=subscription,
                         plans=plans)

@dashboard_bp.route('/keys')
@login_required
def keys():
    """VPN keys management"""
    vpn_keys = VPNKey.query.filter_by(user_id=current_user.id)\
                          .order_by(VPNKey.created_at.desc()).all()
    
    return render_template('dashboard/keys.html', vpn_keys=vpn_keys)