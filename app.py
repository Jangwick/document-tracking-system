import os
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta, time
from flask_mail import Mail, Message
import uuid

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///document_tracking.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'  # Replace with actual email
app.config['MAIL_PASSWORD'] = 'your-password'  # Replace with actual password

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
mail = Mail(app)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Define models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='student')
    profile_picture = db.Column(db.String(200), default='default.jpg')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    applications = db.relationship('Application', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password, password)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    payment_status = db.Column(db.String(20), default='Unpaid')
    documents = db.relationship('Document', backref='application', lazy=True)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False)
    document_type = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), default='Pending')
    feedback = db.Column(db.Text, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text, nullable=True)
    user = db.relationship('User', backref='logs', lazy=True)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Add context processor for notifications
@app.context_processor
def inject_notifications():
    def get_notifications():
        if current_user.is_authenticated:
            return Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
        return []
    
    return dict(get_notifications=get_notifications)

# Add context processor for current datetime
@app.context_processor
def inject_now():
    def now():
        return datetime.utcnow()
    return dict(now=now)

# Add context processor for user logs
@app.context_processor
def inject_user_logs():
    def get_user_logs(user_id, limit=5):
        return AuditLog.query.filter_by(user_id=user_id).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    
    return dict(get_user_logs=get_user_logs)

# Add this before the route that uses @admin_required (before line 339)
from functools import wraps
from flask import flash, redirect, url_for

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if current_user.role != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            log = AuditLog(user_id=user.id, action='User logged in')
            db.session.add(log)
            db.session.commit()
            
            next_page = request.args.get('next')
            if user.role == 'admin':
                return redirect(next_page or url_for('admin_dashboard'))
            return redirect(next_page or url_for('dashboard'))
        flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))
            
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
            
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return redirect(url_for('register'))
            
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    log = AuditLog(user_id=current_user.id, action='User logged out')
    db.session.add(log)
    db.session.commit()
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
        
    applications = Application.query.filter_by(user_id=current_user.id).order_by(Application.created_at.desc()).all()
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    
    return render_template('dashboard.html', applications=applications, notifications=notifications)

@app.route('/application/new', methods=['GET', 'POST'])
@login_required
def new_application():
    if request.method == 'POST':
        application = Application(user_id=current_user.id)
        db.session.add(application)
        db.session.commit()
        
        flash('Application created successfully. Please upload required documents.', 'success')
        return redirect(url_for('upload_documents', application_id=application.id))
    
    return render_template('new_application.html')

@app.route('/application/<int:application_id>/upload', methods=['GET', 'POST'])
@login_required
def upload_documents(application_id):
    application = Application.query.get_or_404(application_id)
    
    if application.user_id != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))
        
    document_types = ['Birth Certificate', 'Form 138', 'Good Moral Certificate', 'TOR', 'Honorable Dismissal', '2x2 Photo']
    
    if request.method == 'POST':
        for doc_type in document_types:
            file = request.files.get(doc_type)
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_ext = filename.rsplit('.', 1)[1].lower()
                
                if file_ext not in ['pdf', 'jpg', 'jpeg', 'png']:
                    flash(f'Invalid file format for {doc_type}. Only PDF, JPG, and PNG are allowed.', 'danger')
                    continue
                    
                # Create unique filename
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                
                document = Document(
                    application_id=application.id,
                    document_type=doc_type,
                    file_path=unique_filename
                )
                
                db.session.add(document)
        
        db.session.commit()
        
        # Create notification for admin
        admin_users = User.query.filter_by(role='admin').all()
        for admin in admin_users:
            notification = Notification(
                user_id=admin.id,
                message=f'New application submitted by {current_user.username}'
            )
            db.session.add(notification)
        
        db.session.commit()
        
        flash('Documents uploaded successfully', 'success')
        return redirect(url_for('dashboard'))
    
    # Get already uploaded documents
    uploaded_docs = Document.query.filter_by(application_id=application_id).all()
    uploaded_types = {doc.document_type for doc in uploaded_docs}
    
    return render_template('upload_documents.html', 
                          application=application, 
                          document_types=document_types,
                          uploaded_types=uploaded_types)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        
        # Check if new username or email already exists
        user_check = User.query.filter_by(username=username).first()
        if user_check and user_check.id != current_user.id:
            flash('Username already taken', 'danger')
            return redirect(url_for('profile'))
            
        email_check = User.query.filter_by(email=email).first()
        if email_check and email_check.id != current_user.id:
            flash('Email already registered', 'danger')
            return redirect(url_for('profile'))
        
        current_user.username = username
        current_user.email = email
        
        # Handle profile picture upload
        if 'profile_pic' in request.files:
            profile_pic = request.files['profile_pic']
            if profile_pic.filename:
                filename = secure_filename(profile_pic.filename)
                file_ext = filename.rsplit('.', 1)[1].lower()
                
                if file_ext not in ['jpg', 'jpeg', 'png']:
                    flash('Invalid image format. Use JPG or PNG.', 'danger')
                else:
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    profile_pic.save(file_path)
                    current_user.profile_picture = unique_filename
        
        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile.html')

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_user.check_password(current_password):
            flash('Current password is incorrect', 'danger')
            return redirect(url_for('change_password'))
            
        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return redirect(url_for('change_password'))
            
        current_user.set_password(new_password)
        db.session.commit()
        
        flash('Password changed successfully', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('change_password.html')

# Admin routes
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    # Get application counts by status
    pending = Application.query.filter_by(status='Pending').count()
    under_review = Application.query.filter_by(status='Under Review').count()
    approved = Application.query.filter_by(status='Approved').count()
    rejected = Application.query.filter_by(status='Rejected').count()
    
    # Get recent applications (limited to 10)
    recent_applications = Application.query.order_by(Application.created_at.desc()).limit(10).all()
    
    # Get recent audit logs
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()
    
    # Get submission count data for the last 7 days
    submission_dates = []
    submission_counts = []
    
    for i in range(6, -1, -1):  # Last 7 days (6 days ago to today)
        date = datetime.now() - timedelta(days=i)
        start_of_day = datetime.combine(date.date(), time.min)
        end_of_day = datetime.combine(date.date(), time.max)
        
        # Count applications created on this day
        count = Application.query.filter(
            Application.created_at >= start_of_day,
            Application.created_at <= end_of_day
        ).count()
        
        # Format date as "MMM DD" (e.g., "Jun 15")
        formatted_date = date.strftime('%b %d')
        
        submission_dates.append(formatted_date)
        submission_counts.append(count)
    
    # Get daily statistics for application statuses over time (last 30 days)
    status_timeline_data = {
        'dates': [],
        'pending': [],
        'under_review': [],
        'approved': [],
        'rejected': []
    }
    
    # Calculate daily application status totals for the past 30 days
    for i in range(29, -1, -1):  # 29 days ago to today
        date = datetime.now() - timedelta(days=i)
        date_str = date.strftime('%b %d')
        status_timeline_data['dates'].append(date_str)
        
        # Count applications by status up to this day
        pending_count = Application.query.filter(
            Application.status == 'Pending',
            Application.created_at <= datetime.combine(date.date(), time.max)
        ).count()
        
        review_count = Application.query.filter(
            Application.status == 'Under Review',
            Application.created_at <= datetime.combine(date.date(), time.max)
        ).count()
        
        approved_count = Application.query.filter(
            Application.status == 'Approved',
            Application.created_at <= datetime.combine(date.date(), time.max)
        ).count()
        
        rejected_count = Application.query.filter(
            Application.status == 'Rejected',
            Application.created_at <= datetime.combine(date.date(), time.max)
        ).count()
        
        status_timeline_data['pending'].append(pending_count)
        status_timeline_data['under_review'].append(review_count)
        status_timeline_data['approved'].append(approved_count)
        status_timeline_data['rejected'].append(rejected_count)
    
    return render_template(
        'admin/dashboard.html',
        pending=pending,
        under_review=under_review,
        approved=approved,
        rejected=rejected,
        recent_applications=recent_applications,
        logs=logs,
        submission_dates=submission_dates,
        submission_counts=submission_counts,
        status_timeline_data=status_timeline_data
    )

@app.route('/admin/recent-activities')
@login_required
@admin_required
def admin_recent_activities():
    # Get fresh audit log data for AJAX refresh
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()
    
    activities = []
    for log in logs:
        user = User.query.get(log.user_id)
        username = user.username if user else f"User #{log.user_id}"
        
        activities.append({
            'username': username,
            'user_id': log.user_id,
            'action': log.action,
            'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M')
        })
        
    return jsonify({'activities': activities})

@app.route('/admin/applications')
@login_required
def admin_applications():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    status_filter = request.args.get('status', '')
    
    if status_filter:
        applications = Application.query.filter_by(status=status_filter).order_by(Application.updated_at.desc()).all()
    else:
        applications = Application.query.order_by(Application.updated_at.desc()).all()
    
    return render_template('admin/applications.html', applications=applications)

@app.route('/admin/application/<int:application_id>')
@login_required
def admin_application_detail(application_id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    application = Application.query.get_or_404(application_id)
    documents = Document.query.filter_by(application_id=application_id).all()
    
    # Log this view
    log = AuditLog(
        user_id=current_user.id,
        action=f'Viewed application #{application_id}',
        details=f'Admin viewed application details for application #{application_id}'
    )
    db.session.add(log)
    db.session.commit()
    
    return render_template('admin/application_detail.html', application=application, documents=documents)

@app.route('/admin/document/update/<int:document_id>', methods=['POST'])
@login_required
def update_document_status(document_id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    document = Document.query.get_or_404(document_id)
    status = request.form.get('status')
    feedback = request.form.get('feedback', '')
    
    document.status = status
    document.feedback = feedback
    document.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    # Create notification for the student
    application = Application.query.get(document.application_id)
    user_id = application.user_id
    
    notification = Notification(
        user_id=user_id,
        message=f'Your {document.document_type} has been {status}.'
    )
    db.session.add(notification)
    db.session.commit()
    
    # Log this action
    log = AuditLog(
        user_id=current_user.id,
        action=f'Updated document status',
        details=f'Changed status of {document.document_type} to {status} for application #{document.application_id}'
    )
    db.session.add(log)
    db.session.commit()
    
    flash(f'Document status updated to {status}', 'success')
    return redirect(url_for('admin_application_detail', application_id=document.application_id))

@app.route('/admin/application/update/<int:application_id>', methods=['POST'])
@login_required
def update_application_status(application_id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    application = Application.query.get_or_404(application_id)
    status = request.form.get('status')
    payment_status = request.form.get('payment_status', application.payment_status)
    
    application.status = status
    application.payment_status = payment_status
    application.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    # Create notification for the student
    notification = Notification(
        user_id=application.user_id,
        message=f'Your application status has been updated to {status}.'
    )
    db.session.add(notification)
    db.session.commit()
    
    # Log this action
    log = AuditLog(
        user_id=current_user.id,
        action=f'Updated application status',
        details=f'Changed application #{application_id} status to {status}'
    )
    db.session.add(log)
    db.session.commit()
    
    flash(f'Application status updated to {status}', 'success')
    return redirect(url_for('admin_application_detail', application_id=application_id))

@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    search = request.args.get('search', '')
    
    if search:
        users = User.query.filter(
            (User.username.contains(search)) | 
            (User.email.contains(search))
        ).all()
    else:
        users = User.query.all()
    
    return render_template('admin/users.html', users=users)

@app.route('/admin/user/<int:user_id>')
@login_required
def admin_user_detail(user_id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    applications = Application.query.filter_by(user_id=user_id).order_by(Application.created_at.desc()).all()
    
    return render_template('admin/user_detail.html', user=user, applications=applications)

@app.route('/admin/reports')
@login_required
def admin_reports():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    total_users = User.query.filter_by(role='student').count()
    total_applications = Application.query.count()
    pending_apps = Application.query.filter_by(status='Pending').count()
    approved_apps = Application.query.filter_by(status='Approved').count()
    rejected_apps = Application.query.filter_by(status='Rejected').count()
    
    # Fix the case() function syntax for newer SQLAlchemy versions
    doc_stats = db.session.query(
        Document.document_type,
        db.func.count(Document.id).label('total'),
        db.func.sum(
            db.case(
                (Document.status == 'Rejected', 1),
                else_=0
            )
        ).label('rejected')
    ).group_by(Document.document_type).all()
    
    return render_template('admin/reports.html', 
                          total_users=total_users,
                          total_applications=total_applications,
                          pending_apps=pending_apps,
                          approved_apps=approved_apps,
                          rejected_apps=rejected_apps,
                          doc_stats=doc_stats)

@app.route('/admin/logs')
@login_required
def admin_logs():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(100).all()
    
    return render_template('admin/logs.html', logs=logs)

@app.route('/mark_notification_read/<int:notification_id>')
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    
    if notification.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    notification.is_read = True
    db.session.commit()
    
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Update system settings
        # This would involve storing settings in a Settings model
        flash('Settings updated successfully', 'success')
        return redirect(url_for('admin_settings'))
    
    return render_template('admin/settings.html')

@app.route('/view_document/<int:document_id>')
@login_required
def view_document(document_id):
    document = Document.query.get_or_404(document_id)
    application = Application.query.get(document.application_id)
    
    # Check if user has access to this document
    if current_user.role != 'admin' and application.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('view_document.html', document=document)

@app.route('/application/<int:application_id>/payment_page')
@login_required
def payment_page(application_id):
    application = Application.query.get_or_404(application_id)
    
    # Check if user has permission to pay for this application
    if application.user_id != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))
    
    # Check if application is already paid
    if application.payment_status == 'Paid':
        flash('This application is already paid', 'info')
        return redirect(url_for('dashboard'))
    
    return render_template('process_payment.html', application=application)

@app.route('/application/<int:application_id>/complete_payment', methods=['POST'])
@login_required
def complete_payment(application_id):
    try:
        application = Application.query.get_or_404(application_id)
        
        # Check if user has permission to update this application
        if application.user_id != current_user.id:
            flash('Unauthorized access', 'danger')
            return redirect(url_for('dashboard'))
        
        # Check if application is already paid
        if application.payment_status == 'Paid':
            flash('This application is already paid', 'info')
            return redirect(url_for('dashboard'))
            
        payment_method = request.form.get('payment_method')
        reference_number = request.form.get('reference_number', 'N/A')
        
        if not payment_method:
            flash('Please select a payment method', 'warning')
            return redirect(url_for('payment_page', application_id=application_id))
        
        # Update application payment status
        application.payment_status = 'Paid'
        application.updated_at = datetime.utcnow()
        
        # Log the payment action
        log = AuditLog(
            user_id=current_user.id,
            action=f'Payment submitted for application #{application_id}',
            details=f'Method: {payment_method}, Reference: {reference_number}'
        )
        db.session.add(log)
        
        # Create notification for admin
        admin_users = User.query.filter_by(role='admin').all()
        for admin in admin_users:
            notification = Notification(
                user_id=admin.id,
                message=f'Payment received for application #{application_id} by {current_user.username}. Method: {payment_method}'
            )
            db.session.add(notification)
        
        # Create notification for the user
        notification = Notification(
            user_id=current_user.id,
            message=f'Your payment for application #{application_id} has been recorded and is being processed.'
        )
        db.session.add(notification)
        
        # Commit all database changes in a single transaction
        db.session.commit()
        
        flash('Payment processed successfully. Your payment is being verified.', 'success')
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        db.session.rollback()  # Roll back any database changes if there's an exception
        flash(f'There was an error processing your payment: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

def create_tables_and_admin():
    db.create_all()
    
    # Create admin user if none exists
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@example.com',
            role='admin'
        )
        admin.set_password('admin123')  # Change this in production!
        db.session.add(admin)
        db.session.commit()

# Add bulk document processing endpoints
@app.route('/admin/documents/bulk_action', methods=['POST'])
@login_required
def bulk_document_action():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    action = request.form.get('action')
    document_ids = request.form.getlist('document_ids')
    
    if not document_ids:
        flash('No documents selected', 'warning')
        return redirect(request.referrer)
    
    if action == 'approve':
        status = 'Approved'
    elif action == 'reject':
        status = 'Rejected'
    elif action == 'review':
        status = 'Under Review'
    else:
        flash('Invalid action', 'danger')
        return redirect(request.referrer)
    
    for doc_id in document_ids:
        document = Document.query.get(doc_id)
        if document:
            document.status = status
            document.updated_at = datetime.utcnow()
            
            # Create notification for the student
            application = Application.query.get(document.application_id)
            notification = Notification(
                user_id=application.user_id,
                message=f'Your {document.document_type} has been {status}.'
            )
            db.session.add(notification)
            
            # Log this action
            log = AuditLog(
                user_id=current_user.id,
                action=f'Bulk updated document status',
                details=f'Changed status of {document.document_type} to {status} for application #{document.application_id}'
            )
            db.session.add(log)
    
    db.session.commit()
    flash(f'{len(document_ids)} documents have been {status.lower()}', 'success')
    return redirect(request.referrer)

# Add admin capability to reset user passwords
@app.route('/admin/user/<int:user_id>/reset_password', methods=['POST'])
@login_required
def admin_reset_password(user_id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # Generate a random password
    temp_password = ''.join(uuid.uuid4().hex[:8])
    user.set_password(temp_password)
    
    db.session.commit()
    
    # Create notification for the user
    notification = Notification(
        user_id=user.id,
        message=f'Your password has been reset by an administrator. Your temporary password is: {temp_password}'
    )
    db.session.add(notification)
    db.session.commit()
    
    # Log this action
    log = AuditLog(
        user_id=current_user.id,
        action=f'Reset user password',
        details=f'Reset password for user {user.username} (ID: {user.id})'
    )
    db.session.add(log)
    db.session.commit()
    
    flash(f'Password for {user.username} has been reset. A notification with the temporary password has been sent.', 'success')
    return redirect(url_for('admin_user_detail', user_id=user.id))

# Add admin ability to activate/deactivate user accounts
@app.route('/admin/user/<int:user_id>/toggle_active', methods=['POST'])
@login_required
def toggle_user_active(user_id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # Add an active field to the User model if it doesn't exist
    if not hasattr(user, 'active'):
        # We need to add this field to the User model - this is a placeholder
        # In reality, you would need to update the User model and do a database migration
        flash('This feature requires a database schema update', 'danger')
        return redirect(url_for('admin_user_detail', user_id=user.id))
    
    user.active = not user.active
    db.session.commit()
    
    status = "activated" if user.active else "deactivated"
    
    # Create notification for the user
    notification = Notification(
        user_id=user.id,
        message=f'Your account has been {status} by an administrator.'
    )
    db.session.add(notification)
    db.session.commit()
    
    # Log this action
    log = AuditLog(
        user_id=current_user.id,
        action=f'Toggle user active status',
        details=f'{status.capitalize()} account for user {user.username} (ID: {user.id})'
    )
    db.session.add(log)
    db.session.commit()
    
    flash(f'Account for {user.username} has been {status}.', 'success')
    return redirect(url_for('admin_user_detail', user_id=user.id))

# Add enhanced admin statistical endpoint
@app.route('/admin/dashboard/stats')
@login_required
def admin_dashboard_stats():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get counts for various statistics
    stats = {
        'total_users': User.query.filter_by(role='student').count(),
        'total_applications': Application.query.count(),
        'pending_docs': Document.query.filter_by(status='Pending').count(),
        'approved_docs': Document.query.filter_by(status='Approved').count(),
        'rejected_docs': Document.query.filter_by(status='Rejected').count(),
        'under_review_docs': Document.query.filter_by(status='Under Review').count()
    }
    
    # Get document type distribution
    doc_types = db.session.query(Document.document_type, db.func.count(Document.id)).group_by(Document.document_type).all()
    stats['doc_type_distribution'] = {doc_type: count for doc_type, count in doc_types}
    
    # Get daily application submission counts for the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    daily_submissions = db.session.query(
        db.func.date(Application.created_at),
        db.func.count(Application.id)
    ).filter(Application.created_at >= thirty_days_ago).group_by(db.func.date(Application.created_at)).all()
    stats['daily_submissions'] = {str(date): count for date, count in daily_submissions}
    
    return jsonify(stats)

# Add bulk application processing endpoint
@app.route('/admin/applications/bulk_action', methods=['POST'])
@login_required
def bulk_application_action():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    action = request.form.get('action')
    application_ids = request.form.getlist('application_ids')
    
    if not application_ids:
        flash('No applications selected', 'warning')
        return redirect(request.referrer)
    
    if action == 'approve':
        status = 'Approved'
    elif action == 'reject':
        status = 'Rejected'
    elif action == 'review':
        status = 'Under Review'
    else:
        flash('Invalid action', 'danger')
        return redirect(request.referrer)
    
    for app_id in application_ids:
        application = Application.query.get(app_id)
        if application:
            application.status = status
            application.updated_at = datetime.utcnow()
            
            # Create notification for the student
            notification = Notification(
                user_id=application.user_id,
                message=f'Your application #{application.id} status has been updated to {status}.'
            )
            db.session.add(notification)
            
            # Log this action
            log = AuditLog(
                user_id=current_user.id,
                action=f'Bulk updated application status',
                details=f'Changed application #{app_id} status to {status}'
            )
            db.session.add(log)
    
    db.session.commit()
    flash(f'{len(application_ids)} applications have been {status.lower()}', 'success')
    return redirect(request.referrer)

if __name__ == '__main__':
    # Initialize database and admin user before running the app
    with app.app_context():
        create_tables_and_admin()
    app.run(debug=True)
