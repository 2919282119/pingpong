import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

logger = logging.getLogger(__name__)

EMAIL_CONFIG = {
    "host": os.environ.get("EMAIL_HOST", "smtp.qq.com"),
    "port": int(os.environ.get("EMAIL_PORT", "465")),
    "user": os.environ.get("EMAIL_USER", "2919282119@qq.com"),
    "pass": os.environ.get("EMAIL_PASS", "gbwiixfruxdgdfda"),
}


def send_verify_code_email(to_email: str, code: str, type_: str = "register") -> bool:
    type_map = {"register": "注册", "login": "登录", "forgot": "找回密码"}
    type_label = type_map.get(type_, "验证")

    subject = f"乒小Yo - {type_label}验证码"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width:600px; margin:0 auto; padding:20px;">
      <h2 style="color:#1485ee; text-align:center;">乒小Yo</h2>
      <div style="background:#f5f5f5; padding:30px; border-radius:10px; margin:20px 0;">
        <p style="font-size:16px; color:#333; margin-bottom:20px;">您好！</p>
        <p style="font-size:16px; color:#333; margin-bottom:20px;">您的{type_label}验证码为：</p>
        <div style="text-align:center; margin:30px 0;">
          <span style="font-size:32px; font-weight:bold; color:#1485ee; letter-spacing:5px;
               padding:15px 30px; background:#fff; border-radius:5px; display:inline-block;">
            {code}
          </span>
        </div>
        <p style="font-size:14px; color:#999;">验证码有效期为 5 分钟，请勿泄露给他人。</p>
      </div>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = EMAIL_CONFIG["user"]
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL(EMAIL_CONFIG["host"], EMAIL_CONFIG["port"]) as server:
            server.login(EMAIL_CONFIG["user"], EMAIL_CONFIG["pass"])
            server.sendmail(EMAIL_CONFIG["user"], [to_email], msg.as_string())
        logger.info("Verification email sent to %s", to_email)
        return True
    except Exception as e:
        logger.warning("Failed to send email to %s: %s", to_email, e)
        return False
