from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os 
from CTFd.models import Challenges, Solves, Configs
from CTFd.utils import get_config
import time

def user_completed_ctf(user):
    total = Challenges.query.count()
    solved = Solves.query.filter_by(user_id=user.id).count()
    return total > 0 and solved >= total


def can_get_certificate(user):
    return user_completed_ctf(user) or ctf_has_ended()

def ctf_has_ended():
    end = Configs.query.filter_by(key="ctf_end").first()

    if not end:
        return False
    try:
        return float(end.value) < time.time()
    except Exception:
        return False

def generate_certificate(username):
    file_path = f"/tmp/{username}_certificate.pdf"

    c = canvas.Canvas(file_path, pagesize=letter)

    template_path = os.path.join(
        os.path.dirname(__file__),
        "static/VSUCTF-Certificate.png"
    )

    c.drawImage(template_path, 0, 0, width=612, height=792)

    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(306, 400, username)

    c.save()

    return file_path