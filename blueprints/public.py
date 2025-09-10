# Public pages blueprint
from flask import Blueprint, render_template, request
from models import Subscription

public_bp = Blueprint('public', __name__)

@public_bp.route('/')
def index():
    """Homepage with VPN service landing"""
    return render_template('public/index.html')

@public_bp.route('/pricing')
def pricing():
    """Pricing page"""
    plans = Subscription.get_plan_details()
    return render_template('public/pricing.html', plans=plans)

@public_bp.route('/docs')
def docs():
    """Documentation and support page"""
    return render_template('public/docs.html')