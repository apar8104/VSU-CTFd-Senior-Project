from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os 
from PIL import Image, ImageDraw, ImageFont
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

def generate_winner_certificate(username, rank):
    """
    Draws the rank ordinal and username onto the winner certificate template.
    Returns the file path of the generated PNG.
    """
    ordinals = {1: "1st", 2: "2nd", 3: "3rd"}
    rank_label = ordinals.get(rank, f"{rank}th")

    template_path = os.path.join(
        os.path.dirname(__file__),
        "static/VSUCTF-WinnerCertificate.png"
    )

    img = Image.open(template_path).convert("RGBA")
    draw = ImageDraw.Draw(img)

    img_width, img_height = img.size

    try:
        rank_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size=int(img_height * 0.10))
    except IOError:
        rank_font = ImageFont.load_default()

    rank_color = (26, 14, 179, 255)  # dark blue matching template

    rank_bbox = draw.textbbox((0, 0), rank_label, font=rank_font)
    rank_w = rank_bbox[2] - rank_bbox[0]
    rank_x = (img_width - rank_w) / 2          # horizontally centered
    rank_y = img_height * 0.32                  # sits on the "YOU PLACED ... OVERALL" line

    draw.text((rank_x, rank_y), rank_label, font=rank_font, fill=rank_color)

    draw.text((rank_x, rank_y), rank_label, font=rank_font, fill=rank_color)

    # --- Username (drawn on the dotted signature line, center of certificate) ---
    try:
        name_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size=int(img_height * 0.045))
    except IOError:
        name_font = ImageFont.load_default()

    name_color = (26, 14, 179, 255)

    name_bbox = draw.textbbox((0, 0), username, font=name_font)
    name_w = name_bbox[2] - name_bbox[0]
    name_x = (img_width - name_w) / 2          # horizontally centered
    name_y = img_height * 0.60
    draw.text((name_x, name_y), username, font=name_font, fill=name_color)

    # Save to a flat RGB PNG (no alpha issues for email clients)
    out = Image.new("RGB", img.size, (255, 255, 255))
    out.paste(img, mask=img.split()[3])

    file_path = f"/tmp/{username}_winner_certificate.png"
    out.save(file_path, "PNG")

    return file_path