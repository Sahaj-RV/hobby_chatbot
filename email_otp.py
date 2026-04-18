# email_otp.py
# Handles everything related to OTP:
#   - Generating a secure 6-digit OTP
#   - Sending it via Gmail SMTP
#   - Storing OTPs with expiry (10 minutes)
#   - Verifying submitted OTPs

import smtplib
import random
import time
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load Gmail credentials from .env file
load_dotenv()

GMAIL_ADDRESS      = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

# OTP expiry time in seconds (10 minutes)
OTP_EXPIRY_SECONDS = 600

# ─────────────────────────────────────────────
# IN-MEMORY OTP STORE
# Format: { "user@email.com": {"otp": "123456", "expires_at": 1234567890} }
# In Phase 2 we'll move this to a database.
# ─────────────────────────────────────────────
otp_store = {}


def generate_otp() -> str:
    """Generate a secure random 6-digit OTP string."""
    return str(random.randint(100000, 999999))


def store_otp(email: str, otp: str):
    """Save OTP with expiry timestamp for a given email."""
    otp_store[email] = {
        "otp":        otp,
        "expires_at": time.time() + OTP_EXPIRY_SECONDS
    }


def verify_otp(email: str, submitted_otp: str) -> dict:
    """
    Check if the submitted OTP is correct and not expired.
    Returns: {"valid": True} or {"valid": False, "reason": "..."}
    """
    record = otp_store.get(email)

    if not record:
        return {"valid": False, "reason": "No OTP found for this email. Please request a new one."}

    if time.time() > record["expires_at"]:
        del otp_store[email]   # clean up expired OTP
        return {"valid": False, "reason": "OTP has expired. Please request a new one."}

    if record["otp"] != submitted_otp.strip():
        return {"valid": False, "reason": "Incorrect OTP. Please try again."}

    # Valid — clean up so OTP can't be reused
    del otp_store[email]
    return {"valid": True}


def build_otp_email_html(otp: str, purpose: str) -> str:
    """
    Build a clean HTML email body.
    purpose: "verify" (start) or "save" (save results)
    """
    purpose_text = (
        "complete your sign-in to Hobby Discovery Bot"
        if purpose == "verify"
        else "save your personalized hobby recommendations"
    )

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8"/>
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: #f5f4f0; margin: 0; padding: 0; }}
        .container {{ max-width: 480px; margin: 40px auto; background: #fff;
                      border-radius: 16px; overflow: hidden;
                      border: 1px solid #e8e6df; }}
        .header {{ background: #1a1a18; padding: 28px 32px; }}
        .header h1 {{ color: #fff; font-size: 18px; font-weight: 500; margin: 0; }}
        .header p  {{ color: #b4b2a9; font-size: 13px; margin: 4px 0 0; }}
        .body {{ padding: 32px; }}
        .otp-box {{ background: #f5f4f0; border-radius: 12px;
                    text-align: center; padding: 24px; margin: 20px 0; }}
        .otp-code {{ font-size: 40px; font-weight: 700; letter-spacing: 10px;
                     color: #1a1a18; font-family: monospace; }}
        .otp-note {{ font-size: 12px; color: #73726c; margin-top: 8px; }}
        .body p {{ font-size: 14px; color: #3d3d3a; line-height: 1.6; }}
        .footer {{ padding: 20px 32px; border-top: 1px solid #e8e6df;
                   font-size: 12px; color: #73726c; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>✦ Hobby Discovery Bot</h1>
          <p>Your verification code</p>
        </div>
        <div class="body">
          <p>Hi there! Use the code below to {purpose_text}:</p>
          <div class="otp-box">
            <div class="otp-code">{otp}</div>
            <div class="otp-note">Valid for 10 minutes · Do not share this code</div>
          </div>
          <p>If you didn't request this, you can safely ignore this email.</p>
        </div>
        <div class="footer">
          Sent by Hobby Discovery Bot &nbsp;·&nbsp; This is an automated message
        </div>
      </div>
    </body>
    </html>
    """


def send_otp_email(to_email: str, purpose: str = "verify") -> dict:
    """
    Generate an OTP, store it, and send it to the user's email via Gmail.

    Args:
        to_email: recipient email address
        purpose:  "verify" (login) or "save" (save results)

    Returns:
        {"success": True} or {"success": False, "error": "..."}
    """
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        return {
            "success": False,
            "error": "Email credentials not configured. Check your .env file."
        }

    otp = generate_otp()
    store_otp(to_email, otp)

    subject = (
        "Your Hobby Bot verification code"
        if purpose == "verify"
        else "Save your hobby results — verification code"
    )

    # Build the email
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"Hobby Discovery Bot <{GMAIL_ADDRESS}>"
    msg["To"]      = to_email

    # Plain text fallback (for email clients that block HTML)
    text_body = f"Your OTP is: {otp}\n\nIt expires in 10 minutes."
    msg.attach(MIMEText(text_body, "plain"))

    # HTML version
    html_body = build_otp_email_html(otp, purpose)
    msg.attach(MIMEText(html_body, "html"))

    # Send via Gmail SMTP (port 587 with STARTTLS)
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()                              # encrypt connection
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())
        print(f"[OTP] Sent to {to_email} (purpose={purpose})")
        return {"success": True}

    except smtplib.SMTPAuthenticationError:
        return {
            "success": False,
            "error": "Gmail authentication failed. Check your App Password in .env."
        }
    except smtplib.SMTPException as e:
        return {"success": False, "error": f"Email sending failed: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}
