from flask import Blueprint
from CTFd.utils.user import get_current_user

def load(app):
    from .routes import certificate_bp
    from .utils import can_get_certificate

    app.register_blueprint(certificate_bp)

    @app.context_processor
    def inject_certificate_flag():
        user = get_current_user()
        return dict(can_get_certificate=can_get_certificate(user) if user else False)