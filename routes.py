from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app import app, db
from models import User, ChatSession, Feedback
from ai_service import ai_service
import logging

logger = logging.getLogger(__name__)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    """Landing page"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/home')
@login_required
def home():
    """User home page (separate from dashboard)"""
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Please provide both email and password.', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        # Validation
        if not all([full_name, email, password]):
            flash('All fields are required.', 'error')
            return render_template('signup.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('signup.html')
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please use a different email.', 'error')
            return render_template('signup.html')
        
        # Create new user
        try:
            user = User(full_name=full_name, email=email)
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating user: {e}")
            flash('An error occurred while creating your account. Please try again.', 'error')
    
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard with analytics"""
    # Get user's feedback statistics
    feedback_stats = db.session.query(
        Feedback.sentiment, 
        db.func.count(Feedback.id)
    ).filter_by(user_id=current_user.id).group_by(Feedback.sentiment).all()
    
    stats = {'positive': 0, 'negative': 0, 'neutral': 0}
    for sentiment, count in feedback_stats:
        stats[sentiment] = count
    
    # Get recent feedback
    recent_feedback = db.session.query(Feedback, ChatSession).join(
        ChatSession, Feedback.chat_session_id == ChatSession.id
    ).filter(Feedback.user_id == current_user.id).order_by(
        Feedback.created_at.desc()
    ).limit(5).all()
    
    return render_template('dashboard.html', 
                         feedback_stats=stats, 
                         recent_feedback=recent_feedback)

@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    """AI chat interface"""
    if request.method == 'POST':
        question = request.form.get('question', '').strip()
        feedback_text = request.form.get('feedback', '').strip()
        chat_session_id = request.form.get('chat_session_id')
        
        if question:
            # Get AI response
            try:
                ai_response = ai_service.get_ai_response(question)
                
                # Save chat session
                chat_session = ChatSession(
                    user_id=current_user.id,
                    question=question,
                    response=ai_response
                )
                db.session.add(chat_session)
                db.session.commit()
                
                session['last_chat_id'] = chat_session.id
                session['last_response'] = ai_response
                
                flash('Response generated successfully!', 'success')
                
            except Exception as e:
                logger.error(f"Error processing chat: {e}")
                flash('Sorry, there was an error processing your question. Please try again.', 'error')
        
        elif feedback_text and chat_session_id:
            # Process feedback
            try:
                chat_session = ChatSession.query.get(int(chat_session_id))
                if chat_session and chat_session.user_id == current_user.id:
                    sentiment = ai_service.analyze_sentiment(feedback_text)
                    
                    feedback = Feedback(
                        user_id=current_user.id,
                        chat_session_id=chat_session.id,
                        feedback_text=feedback_text,
                        sentiment=sentiment
                    )
                    db.session.add(feedback)
                    db.session.commit()
                    
                    flash(f'Feedback submitted! Sentiment: {sentiment.title()}', 'success')
                    session.pop('last_chat_id', None)
                    session.pop('last_response', None)
                else:
                    flash('Invalid chat session.', 'error')
                    
            except Exception as e:
                logger.error(f"Error processing feedback: {e}")
                flash('Error submitting feedback. Please try again.', 'error')
    
    return render_template('chat.html', 
                         last_chat_id=session.get('last_chat_id'),
                         last_response=session.get('last_response'))

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
