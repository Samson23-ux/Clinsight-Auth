import ssl
import smtplib
import secrets
from uuid import UUID
from redis import Redis
from email.mime.text import MIMEText
from sqlalchemy import Engine, create_engine
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session, sessionmaker
from datetime import datetime, timezone, timedelta


from app.core.config import settings
from app.api.models.auth import AuthOtp
from app.tasks.celery_app import celery_app


db_engine: Engine = create_engine(
    url=settings.SYNC_DB_URL,
    pool_size=10,
    pool_timeout=10.0,
    pool_pre_ping=True,
    max_overflow=5,
    connect_args={"options": "-c timezone=utc"},
)


db_session: Session = sessionmaker(bind=db_engine, autocommit=False, autoflush=False)


class BaseTaskWithFailure(celery_app.Task):
    # errors to retry for
    autoretry_for = (
        smtplib.SMTPConnectError,
        smtplib.SMTPServerDisconnected,
        ConnectionError,
        TimeoutError,
    )

    # maximum retry value
    max_retries = 5

    """
    retry jitter set to True to ensure randomness in retry_backoff value
    this prevents overwhelming when multiple tasks fails simultaneously,
    retrying each task at different time
    """
    retry_jitter = True

    """
    increment retry delay value exponentially
    """
    retry_backoff = 2

    """
    maximum retry backoff - one minute
    """
    retry_backoff_max = 600

@celery_app.task(base=BaseTaskWithFailure)
def send_email(email_id: str, user_email: str, user_id: UUID):
    from app.api.services.auth_service import auth_service_v1
    try:
        session: Session = db_session()
        redis_client: Redis = Redis.from_url(settings.REDIS_URL)

        code_db: dict | None = auth_service_v1._get_verification_code(
            email_id, redis_client
        )

        if not code_db:
            # create email code
            otp: str = str(secrets.randbelow(900000) + 100000)

            message: MIMEMultipart = MIMEMultipart()

            message["From"] = settings.API_EMAIL
            message["To"] = user_email
            message["Subject"] = "Email Verification Code"

            # HTML Text
            body: str = f"""
            <!DOCTYPE html>
            <html>
                <head>
                    <meta charset="UTF-8" />
                    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                </head>
                <body style="margin:0;padding:0;background-color:#f4f4f4;font-family:Arial,sans-serif;">
                    <table width="100%" cellpadding="0" cellspacing="0" style="padding:40px 0;">
                    <tr>
                        <td align="center">
                        <table width="480" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;padding:40px;box-shadow:0 2px 8px rgba(0,0,0,0.05);">
                            <tr>
                            <td align="center" style="padding-bottom:24px;">
                                <h2 style="margin:0;color:#1a1a1a;font-size:22px;">Verify your email</h2>
                            </td>
                            </tr>
                            <tr>
                            <td align="center" style="padding-bottom:16px;">
                                <p style="margin:0;color:#555555;font-size:15px;line-height:1.6;">
                                Use the code below to complete your verification. It expires in <strong>5 minutes</strong>.
                                </p>
                            </td>
                            </tr>
                            <tr>
                            <td align="center" style="padding:24px 0;">
                                <div style="display:inline-block;background:#f0f4ff;border-radius:8px;padding:16px 40px;">
                                <span style="font-size:36px;font-weight:bold;letter-spacing:10px;color:#3b5bdb;">{otp}</span>
                                </div>
                            </td>
                            </tr>
                            <tr>
                            <td align="center" style="padding-top:16px;">
                                <p style="margin:0;color:#999999;font-size:13px;">
                                If you did not request this, please ignore this email.
                                </p>
                            </td>
                            </tr>
                        </table>
                        </td>
                    </tr>
                    </table>
                </body>
            </html>
            """

            mime_text: MIMEText = MIMEText(body, "html")

            message.attach(mime_text)
            context = ssl.create_default_context()

            with smtplib.SMTP_SSL(
                "smtp.gmail.com", settings.SMTP_PORT, context=context
            ) as server:
                text = message.as_string()
                server.login(settings.API_EMAIL, settings.API_EMAIL_PASSWORD)
                server.sendmail(settings.API_EMAIL, user_email, text)

            payload: dict = {"otp": otp, "email": user_email}

            expires_at: datetime = datetime.now(timezone.utc) + timedelta(minutes=5)
            auth_otp: AuthOtp = AuthOtp(user_id=user_id, otp=otp, expires_at=expires_at)

            auth_service_v1._create_auth_otp(auth_otp, session)
            auth_service_v1._create_email_code(email_id, payload, 300, redis_client)
    finally:
        session.close()
        redis_client.close()
