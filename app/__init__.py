import os
from flask import Flask
from config import Config

def create_app():
    Config.validate()
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Ensure SECRET_KEY is set for production
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', app.config.get('SECRET_KEY', 'dev_secret_key_12345'))

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.patient import patient_bp
    from app.routes.doctor import doctor_bp
    from app.routes.appointment import appointment_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(patient_bp, url_prefix='/patient')
    app.register_blueprint(doctor_bp, url_prefix='/doctor')
    app.register_blueprint(appointment_bp, url_prefix='/appointment')
    
    # Global Routes
    @app.route('/')
    def index():
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))

    return app

# Expose app for Gunicorn/Deployment
app = create_app()
