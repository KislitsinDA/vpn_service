# Billing and payments blueprint - flask_stripe integration
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from models import db, Subscription, VPNKey
from datetime import datetime, timedelta
import stripe
import os

# Initialize Stripe - flask_stripe integration 
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

billing_bp = Blueprint('billing', __name__)

@billing_bp.route('/checkout/<plan>')
@login_required
def checkout(plan):
    """Checkout page for subscription plan"""
    plans = Subscription.get_plan_details()
    
    if plan not in plans:
        flash('Недопустимый тарифный план', 'error')
        return redirect(url_for('public.pricing'))
    
    plan_info = plans[plan]
    
    # Create order in session
    order = {
        'plan': plan,
        'amount_usd': plan_info['amount'],
        'user_id': current_user.id
    }
    session['order'] = order
    
    # Default gateway
    gateway = request.args.get('gateway', 'stripe')
    
    return render_template('billing/pay.html', order=order, gateway=gateway)

@billing_bp.route('/process-payment', methods=['POST'])
@login_required
def process_payment():
    """Process payment for subscription"""
    order = session.get('order')
    if not order:
        flash('Сессия истекла. Попробуйте еще раз.', 'error')
        return redirect(url_for('public.pricing'))
    
    try:
        # Create subscription record
        plan_info = Subscription.get_plan_details()[order['plan']]
        
        expires_at = None
        if plan_info['duration_days']:
            expires_at = datetime.utcnow() + timedelta(days=plan_info['duration_days'])
        
        subscription = Subscription(
            user_id=current_user.id,
            plan=order['plan'],
            amount_usd=order['amount_usd'],
            expires_at=expires_at
        )
        
        # For free plan or demo, create immediately
        if order['amount_usd'] == 0:
            subscription.payment_id = 'FREE_PLAN'
        else:
            # TODO: Implement real Stripe payment processing
            subscription.payment_id = f'DEMO_PAYMENT_{datetime.utcnow().timestamp()}'
        
        db.session.add(subscription)
        db.session.flush()  # Get subscription ID
        
        # Create VPN key
        vpn_key = VPNKey(
            user_id=current_user.id,
            subscription_id=subscription.id,
            token=VPNKey.generate_key_token(),
            expires_at=expires_at
        )
        
        db.session.add(vpn_key)
        db.session.commit()
        
        # Clear order from session
        session.pop('order', None)
        
        flash('Оплата успешна! Ваш ключ доступа готов.', 'success')
        return redirect(url_for('billing.success'))
        
    except Exception as e:
        db.session.rollback()
        flash('Ошибка при обработке платежа. Попробуйте еще раз.', 'error')
        return redirect(url_for('billing.checkout', plan=order['plan']))

@billing_bp.route('/success')
@login_required
def success():
    """Payment success page"""
    # Get user's latest VPN key
    key = VPNKey.query.filter_by(user_id=current_user.id, is_active=True)\
                     .order_by(VPNKey.created_at.desc()).first()
    
    return render_template('billing/success.html', key=key)