import resend
import random
from datetime import datetime, timedelta, timezone
from src.config import settings

# Resend client setup
resend.api_key = settings.RESEND_API_KEY


def generate_otp() -> str:
    """
    Generates a 6-digit OTP code.
    Random number between 100000 and 999999.
    """
    return str(random.randint(100000, 999999))


def get_otp_expiry() -> datetime:
    """
    Returns OTP expiry time — 10 minutes from now (UTC).
    """
    return datetime.now(timezone.utc) + timedelta(minutes=10)


def send_otp_email(email: str, otp: str) -> bool:
    """
    Sends OTP verification email via Resend.
    Returns True if sent successfully, False otherwise.
    """
    try:
        print(f"OTP for {email}: {otp}")
        resend.Emails.send({
            "from": "JobRadar <onboarding@resend.dev>",
            "to": email,
            "subject": "Your JobRadar verification code",
            "html": f"""
            <div style="font-family: sans-serif; max-width: 400px; margin: 0 auto; padding: 32px;">
                <h2 style="color: #6366f1;">📡 JobRadar</h2>
                <p>Your verification code is:</p>
                <div style="
                    background: #1e1b4b;
                    color: #ffffff;
                    font-size: 36px;
                    font-weight: bold;
                    letter-spacing: 8px;
                    text-align: center;
                    padding: 24px;
                    border-radius: 8px;
                    margin: 24px 0;
                ">
                    {otp}
                </div>
                <p style="color: #64748b; font-size: 13px;">
                    This code expires in 10 minutes.<br>
                    If you didn't request this, ignore this email.
                </p>
            </div>
            """
        })
        return True
    except Exception as e:
        print(f"Email send error: {e}")
        return False