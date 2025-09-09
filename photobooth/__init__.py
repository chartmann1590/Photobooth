"""
Photobooth Flask Application Package
"""
import os
import logging
from flask import Flask
from config import config

def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize configuration
    config[config_name].init_app(app)
    
    # Initialize database
    from .models import init_db
    init_db(app.config['DATABASE_PATH'])
    
    # Register blueprints
    from .routes_booth import booth_bp
    from .routes_settings import settings_bp
    
    app.register_blueprint(booth_bp, url_prefix='/booth')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    
    # Health check endpoint
    @app.route('/healthz')
    def health_check():
        """Health check endpoint"""
        return {'status': 'healthy', 'app': 'photobooth'}, 200
    
    # Root redirect to booth
    @app.route('/')
    def index():
        """Root redirect to booth"""
        from flask import redirect, url_for
        return redirect(url_for('booth.booth'))
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """404 error handler"""
        from flask import render_template
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """500 error handler"""
        from flask import render_template
        logging.error(f"Internal server error: {error}")
        return render_template('500.html'), 500
    
    return app