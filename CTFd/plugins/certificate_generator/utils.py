from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os 

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