from flask import Blueprint

def load(app):
    from .routes import certificate_bp
    app.register_blueprint(certificate_bp)