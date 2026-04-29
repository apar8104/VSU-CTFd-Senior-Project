from flask import Blueprint

def load(app):
    from .routes import certificate_bp
    from .utils import can_get_certificate

    app.register_blueprint(certificate_bp)

    @app.context_processor
    def inject_certificate_flag():
        return dict(can_get_certificate=can_get_certificate)