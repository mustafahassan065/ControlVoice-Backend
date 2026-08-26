import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import io
import boto3
import os
import uuid
from dotenv import load_dotenv

load_dotenv()


def generate_score_graphic(
    authority_score: int = 87,
    center_label: str = "AUTHORITY",
    label_top: str = "Clarity",
    label_bottom: str = "Resonance",
    coaching_title: str = "Real-time Coaching",
    coaching_sub: str = "★ Optimal steady flow",
    pace_label: str = "Pace",
    score_left_label: str = "Pause Control",
    score_left_val: str = "72/100",
    score_right_label: str = "Strong Endings",
    score_right_val: str = "54/100",
    prev_score: int = None,
    email_type: str = "afternoon",
) -> bytes:

    fig = plt.figure(figsize=(7.5, 3.5), facecolor='#FDFCF8')
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor('#FDFCF8')
    ax.set_xlim(0, 7.5)
    ax.set_ylim(0, 3.5)
    ax.axis('off')

    cx, cy, r = 1.9, 1.75, 1.38

    # Evening: faint before arc
    if email_type == "evening" and prev_score is not None:
        theta_prev = np.linspace(
            np.radians(-225 + 270 * (prev_score / 100)),
            np.radians(-225), 300)
        ax.plot(cx + r * np.cos(theta_prev), cy + r * np.sin(theta_prev),
                color='#DEDAD2', linewidth=4, solid_capstyle='round')

    # Main arc using plot (not patches.Arc) — avoids solid_capstyle issue
    theta = np.linspace(
        np.radians(-225 + 270 * (authority_score / 100)),
        np.radians(-225), 300)
    ax.plot(cx + r * np.cos(theta), cy + r * np.sin(theta),
            color='#1A1A1B', linewidth=5, solid_capstyle='round')

    # Inner circle
    ax.add_patch(plt.Circle((cx, cy), 0.46, color='#F5F3EF', zorder=3))
    ax.add_patch(plt.Circle((cx, cy), 0.46, fill=False,
                             edgecolor='#DEDAD2', linewidth=1.2, zorder=4))

    ax.text(cx, cy + 0.22, center_label, ha='center', va='center',
            fontsize=6, color='#9A9890', zorder=5)
    ax.text(cx, cy - 0.08, str(authority_score), ha='center', va='center',
            fontsize=28, color='#1A1A1B', zorder=5)
    ax.text(cx, cy + r + 0.18, label_top, ha='center', fontsize=9, color='#4A4840')
    ax.text(cx, cy - r - 0.18, label_bottom, ha='center', fontsize=9, color='#4A4840')

    # Coaching box
    ax.add_patch(patches.FancyBboxPatch(
        (3.4, 2.62), 3.8, 0.62,
        boxstyle="round,pad=0.08", facecolor='#F0EDE6', edgecolor='none'))
    ax.text(3.58, 2.98, coaching_title, fontsize=8, color='#4A4840', fontweight='semibold')
    ax.text(3.58, 2.74, coaching_sub, fontsize=8, color='#8A7A60')

    ax.text(3.4, 2.28, pace_label, fontsize=9, color='#4A4840')

    # Waveform
    wx = np.linspace(3.4, 7.2, 80)
    wy1 = 1.82 + 0.12 * np.sin(wx * 3.8) + 0.05 * np.sin(wx * 7.5)
    wy2 = 1.75 + 0.14 * np.sin(wx * 3.8 + 0.5) + 0.06 * np.sin(wx * 7.5 + 0.4)
    ax.plot(wx, wy1, color='#DEDAD2', linewidth=1.8, solid_capstyle='round')
    ax.plot(wx, wy2, color='#1A1A1B', linewidth=2.5, solid_capstyle='round')
    ax.plot(wx[45], wy2[45], 'o', color='#1A1A1B', markersize=6, zorder=5)

    ax.text(3.4, 1.28, score_left_label, fontsize=8, color='#9A9890')
    ax.text(3.4, 1.06, score_left_val, fontsize=9, color='#1A1A1B', fontweight='semibold')
    ax.text(5.4, 1.28, score_right_label, fontsize=8, color='#9A9890')
    ax.text(5.4, 1.06, score_right_val, fontsize=9, color='#1A1A1B', fontweight='semibold')

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='#FDFCF8')
    buf.seek(0)
    img_bytes = buf.read()
    plt.close()
    return img_bytes


def upload_image_to_s3(image_bytes: bytes, filename: str = None) -> str:
    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name='eu-north-1'
    )
    bucket = os.getenv("AWS_BUCKET_NAME")
    if not filename:
        filename = f"email-graphics/{uuid.uuid4()}.png"

    s3_client.put_object(
        Bucket=bucket,
        Key=filename,
        Body=image_bytes,
        ContentType='image/png',
    )
    region = os.getenv("AWS_REGION", "eu-north-1")
    url = f"https://{bucket}.s3.{region}.amazonaws.com/{filename}"
    return url


def generate_and_upload(
    authority_score: int = 87,
    center_label: str = "AUTHORITY",
    label_top: str = "Clarity",
    label_bottom: str = "Resonance",
    coaching_title: str = "Real-time Coaching",
    coaching_sub: str = "★ Optimal steady flow",
    pace_label: str = "Pace",
    score_left_label: str = "Pause Control",
    score_left_val: str = "72/100",
    score_right_label: str = "Strong Endings",
    score_right_val: str = "54/100",
    prev_score: int = None,
    email_type: str = "afternoon",
) -> str:
    img_bytes = generate_score_graphic(
        authority_score=authority_score,
        center_label=center_label,
        label_top=label_top,
        label_bottom=label_bottom,
        coaching_title=coaching_title,
        coaching_sub=coaching_sub,
        pace_label=pace_label,
        score_left_label=score_left_label,
        score_left_val=score_left_val,
        score_right_label=score_right_label,
        score_right_val=score_right_val,
        prev_score=prev_score,
        email_type=email_type,
    )
    return upload_image_to_s3(img_bytes)