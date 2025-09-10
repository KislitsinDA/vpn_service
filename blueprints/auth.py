# Authentication blueprint
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Пожалуйста, заполните все поля', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(email=email.lower()).first()
        
        if user and user.check_password(password):
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user, remember=True)  # Remember user for convenience
            flash('Добро пожаловать!', 'success')
            
            # Redirect to next page if specified and safe, otherwise to dashboard
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/') and not next_page.startswith('//'):
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))
        else:
            flash('Неверный email или пароль', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        agree_terms = request.form.get('agree_terms')
        agree_privacy = request.form.get('agree_privacy')
        
        if not all([email, password, agree_terms, agree_privacy]):
            flash('Пожалуйста, заполните все поля и согласитесь с условиями', 'error')
            return render_template('auth/register.html')
        
        # Password validation
        if len(password) < 6:
            flash('Пароль должен содержать минимум 6 символов', 'error')
            return render_template('auth/register.html')
        
        # Email validation
        if '@' not in email or '.' not in email.split('@')[-1]:
            flash('Пожалуйста, введите корректный email адрес', 'error')
            return render_template('auth/register.html')
        
        # Check if user already exists
        if User.query.filter_by(email=email.lower()).first():
            flash('Пользователь с таким email уже существует', 'error')
            return render_template('auth/register.html')
        
        # Create new user
        user = User(email=email.lower())
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            
            login_user(user)
            flash('Регистрация успешна! Добро пожаловать!', 'success')
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            db.session.rollback()
            flash('Ошибка при регистрации. Попробуйте еще раз.', 'error')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('Вы успешно вышли из системы', 'info')
    return redirect(url_for('public.index'))

@auth_bp.route('/request-password-reset', methods=['GET', 'POST'])
def request_password_reset():
    """Request password reset"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            flash('Пожалуйста, введите email', 'error')
            return render_template('auth/request_reset.html')
        
        user = User.query.filter_by(email=email.lower()).first()
        
        if user:
            # TODO: Implement password reset email sending
            flash('Если аккаунт с таким email существует, на него будет отправлена ссылка для восстановления пароля', 'info')
        else:
            flash('Если аккаунт с таким email существует, на него будет отправлена ссылка для восстановления пароля', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/request_reset.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    # TODO: Implement token verification
    
    if request.method == 'POST':
        password = request.form.get('password')
        
        if not password:
            flash('Пожалуйста, введите новый пароль', 'error')
            return render_template('auth/reset.html', token=token)
        
        # TODO: Implement password reset logic
        flash('Пароль успешно изменен', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset.html', token=token)
