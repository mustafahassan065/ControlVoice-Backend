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
    authority_score: int,
    label_top: str = "Clarity",
    label_bottom: str = "Resonance",
    center_label: str = "AUTHORITY",
    score_left_label: str = "Pause Control",
    score_left_val: str = "72/100",
    score_right_label: str = "Strong Endings",
    score_right_val: str = "54/100",
    coaching_title: str = "Real-time Coaching",
    coaching_sub: str = "★ Optimal steady flow",
    pace_label: str = "Pace",
    email_type: str = "afternoon",  # morning, afternoon, evening
    prev_score: int = None,         # for evening — before arc
) -> bytes:
    """
    Generate exactly same graphic as the image — C-shape arc, inner circle, pace waveform.
    Returns PNG bytes.
    """

    fig, ax = plt.subplots(1, 1, figsize=(7.2, 3.4))
    fig.patch.set_facecolor('#FDFCF8')
    ax.set_facecolor('#FDFCF8')
    ax.set_xlim(0, 7.2)
    ax.set_ylim(0, 3.4)
    ax.axis('off')

    # ── LEFT SIDE: C-shape arc ──────────────────────────────

    cx, cy, r = 1.9, 1.7, 1.45  # center x, y, radius

    # C-arc = 270 degrees (open on right side, -225 to 45 degrees)
    # Score fills the arc proportionally
    start_angle = -225
    full_sweep = 270

    # If evening — draw previous arc faint first
    if email_type == "evening" and prev_score is not None:
        prev_sweep = (prev_score / 100) * full_sweep
        prev_arc = patches.Arc(
            (cx, cy), 2 * r, 2 * r,
            angle=0,
            theta1=start_angle,
            theta2=start_angle + prev_sweep,
            color='#DEDAD2', linewidth=3.5, solid_capstyle='round'
        )
        ax.add_patch(prev_arc)

    # Main score arc
    score_sweep = (authority_score / 100) * full_sweep
    main_arc = patches.Arc(
        (cx, cy), 2 * r, 2 * r,
        angle=0,
        theta1=start_angle,
        theta2=start_angle + score_sweep,
        color='#1A1A1B', linewidth=4.5, solid_capstyle='round'
    )
    ax.add_patch(main_arc)

    # Inner circle
    inner_circle = plt.Circle((cx, cy), 0.48, color='#F5F3EF', zorder=3)
    ax.add_patch(inner_circle)
    inner_border = plt.Circle((cx, cy), 0.48, fill=False, edgecolor='#DEDAD2', linewidth=1, zorder=4)
    ax.add_patch(inner_border)

    # Score number center
    ax.text(cx, cy + 0.06, str(authority_score),
            ha='center', va='center', fontsize=26, fontweight='normal',
            color='#1A1A1B', zorder=5)

    # Center label above number
    ax.text(cx, cy + 0.26, center_label,
            ha='center', va='center', fontsize=6.5, color='#9A9890',
            fontweight='normal', zorder=5, letter_spacing=None)

    # Top label (Clarity)
    ax.text(cx, cy + r + 0.18, label_top,
            ha='center', va='bottom', fontsize=8, color='#4A4840')

    # Bottom label (Resonance)
    ax.text(cx, cy - r - 0.18, label_bottom,
            ha='center', va='top', fontsize=8, color='#4A4840')

    # ── RIGHT SIDE: Coaching box + waveform ─────────────────

    box_x, box_y = 3.55, 2.55
    box_w, box_h = 3.4, 0.62

    # Coaching box background
    box = patches.FancyBboxPatch(
        (box_x, box_y), box_w, box_h,
        boxstyle="round,pad=0.06",
        facecolor='#F0EDE6', edgecolor='none'
    )
    ax.add_patch(box)

    ax.text(box_x + 0.18, box_y + 0.42, coaching_title,
            fontsize=7.5, color='#4A4840', fontweight='semibold', va='center')
    ax.text(box_x + 0.18, box_y + 0.18, coaching_sub,
            fontsize=7.5, color='#8A7A60', va='center')

    # Pace label
    ax.text(3.55, 2.15, pace_label,
            fontsize=8, color='#4A4840', va='center')

    # Pace waveform — two lines
    wave_x = np.linspace(3.55, 6.9, 60)

    # Back line (faint)
    wave_y_back = 1.78 + 0.13 * np.sin(wave_x * 3.8) + 0.06 * np.sin(wave_x * 7.2)
    ax.plot(wave_x, wave_y_back, color='#DEDAD2', linewidth=1.5, solid_capstyle='round')

    # Front line (bold) — slightly different phase
    wave_y_front = 1.72 + 0.15 * np.sin(wave_x * 3.8 + 0.4) + 0.07 * np.sin(wave_x * 7.2 + 0.3)
    ax.plot(wave_x, wave_y_front, color='#1A1A1B', linewidth=2.2, solid_capstyle='round')

    # Dot on waveform
    mid_idx = 35
    ax.plot(wave_x[mid_idx], wave_y_front[mid_idx], 'o',
            color='#1A1A1B', markersize=5, zorder=5)

    # Score labels below waveform
    ax.text(3.55, 1.28, score_left_label,
            fontsize=7.5, color='#9A9890', va='center')
    ax.text(3.55, 1.06, score_left_val,
            fontsize=8, color='#1A1A1B', fontweight='semibold', va='center')

    ax.text(5.42, 1.28, score_right_label,
            fontsize=7.5, color='#9A9890', va='center')
    ax.text(5.42, 1.06, score_right_val,
            fontsize=8, color='#1A1A1B', fontweight='semibold', va='center')

    # Save to bytes
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor='#FDFCF8', edgecolor='none')
    buf.seek(0)
    plt.close(fig)
    return buf.read()


def upload_image_to_s3(image_bytes: bytes, filename: str = None) -> str:
    """Upload PNG to S3 and return public URL"""
    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION", "us-east-1")
    )
    bucket = os.getenv("AWS_BUCKET_NAME")
    if not filename:
        filename = f"email_graphics/{uuid.uuid4()}.png"

    s3_client.put_object(
        Bucket=bucket,
        Key=filename,
        Body=image_bytes,
        ContentType='image/png',
        CacheControl='max-age=86400',
    )
    url = f"https://{bucket}.s3.{os.getenv('AWS_REGION', 'us-east-1')}.amazonaws.com/{filename}"
    return url


def generate_and_upload(
    authority_score: int,
    label_top: str = "Clarity",
    label_bottom: str = "Resonance",
    center_label: str = "AUTHORITY",
    score_left_label: str = "Pause Control",
    score_left_val: str = "72/100",
    score_right_label: str = "Strong Endings",
    score_right_val: str = "54/100",
    coaching_title: str = "Real-time Coaching",
    coaching_sub: str = "★ Optimal steady flow",
    pace_label: str = "Pace",
    email_type: str = "afternoon",
    prev_score: int = None,
) -> str:
    """Generate image and upload to S3, return URL"""
    img_bytes = generate_score_graphic(
        authority_score=authority_score,
        label_top=label_top,
        label_bottom=label_bottom,
        center_label=center_label,
        score_left_label=score_left_label,
        score_left_val=score_left_val,
        score_right_label=score_right_label,
        score_right_val=score_right_val,
        coaching_title=coaching_title,
        coaching_sub=coaching_sub,
        pace_label=pace_label,
        email_type=email_type,
        prev_score=prev_score,
    )
    return upload_image_to_s3(img_bytes)