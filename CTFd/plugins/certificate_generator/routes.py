from flask import Blueprint, send_file, abort
from CTFd.utils.decorators import authed_only
from CTFd.models import Users
from CTFd.utils.user import get_current_user
from .utils import can_get_certificate, generate_certificate

certificate_bp = Blueprint(
    "certificate",
    __name__, 
    url_prefix="/certificate"
)

@certificate_bp.route("/download")
@authed_only
def download_certificate():
    user = get_current_user()

    if not can_get_certificate(user):
        abort(403)
        
    pdf_path = generate_certificate(user.name)
    
    return send_file(pdf_path, as_attachment=True)
