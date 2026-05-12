"""
RESQ - Disaster Response Coordination Platform
Main Flask Application
"""
from flask import Flask, request, jsonify, session, render_template
from sqlalchemy import inspect, text
import os

from .config import config
from .db import db
from .models.user import User
from .models.incident import Incident
from .models.notification import Notification
from .models.volunteer_skill import VolunteerSkill
from .routes.auth import auth_bp
from .routes.incidents import incidents_bp
from .routes.admin import admin_bp


def create_app(config_name='development'):
    """
    Application factory - creates and configures Flask app
    """
    app = Flask(__name__,
               template_folder='templates',
               static_folder='static')
    
    # Load configuration
    app.config.from_object(config.get(config_name, config['development']))
    
    # Initialize database
    db.init_app(app)
    
    # Create tables if they don't exist (for development)
    # In production, use migrations instead
    with app.app_context():
        db.create_all()

        inspector = inspect(db.engine)
        if inspector.has_table('incidents'):
            incident_columns = [column['name'] for column in inspector.get_columns('incidents')]
            if 'verified_by' not in incident_columns:
                with db.engine.begin() as conn:
                    conn.execute(text('ALTER TABLE incidents ADD COLUMN verified_by INTEGER'))

        # Initialize sample data if database is empty
        if User.query.count() == 0:
            from database.init_db import init_database
            init_database()
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(incidents_bp)
    app.register_blueprint(admin_bp)
    
    # Register before/after request handlers
    @app.before_request
    def before_request():
        """Initialize database connection before each request"""
        # No longer needed with SQLAlchemy, but keeping for compatibility
        pass
    
    @app.teardown_appcontext
    def close_db(error):
        """Close database connection after each request"""
        # SQLAlchemy handles this automatically
        pass
    
    # ==================== HTML Routes ====================
    
    @app.route('/')
    def index():
        """Home page"""
        return render_template('index.html')
    
    @app.route('/login')
    def login_page():
        """Login page"""
        return render_template('login.html')
    
    @app.route('/register')
    def register_page():
        """Registration page"""
        return render_template('register.html')
    
    @app.route('/dashboard')
    def dashboard_page():
        """Dashboard page"""
        return render_template('dashboard.html')
    
    @app.route('/report')
    def report_incident_page():
        """Report incident page"""
        return render_template('report_incident.html')
    
    @app.route('/reports')
    def view_reports_page():
        """View reports page"""
        return render_template('view_reports.html')
    
    @app.route('/admin')
    def admin_page():
        """Admin panel page"""
        return render_template('admin_panel.html')
    
    @app.route('/broadcast')
    def broadcast_page():
        """Broadcast notification page for admins"""
        if 'user_id' not in session or session.get('role') != 'admin':
            return render_template('dashboard.html')
        return render_template('broadcast.html')
    
    @app.route('/notifications')
    def notifications_page():
        """Notifications page"""
        return render_template('notifications.html')
    
    # ==================== API Routes ====================
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'service': 'RESQ API',
            'version': '1.0.0'
        }), 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        return jsonify({'error': 'Internal server error'}), 500
    
    return app


# Create the application
app = create_app(os.environ.get('FLASK_ENV', 'production'))


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║       RESQ - Disaster Response Coordination Platform      ║
║                                                            ║
║       Server running on http://localhost:{port}            ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝

Test Accounts:
--------------
Admin:     username: admin,     password: admin123
Volunteer: username: john_volunteer, password: volunteer123
Citizen:   username: mike_citizen,   password: citizen123
    """)
    
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)
