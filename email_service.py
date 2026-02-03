"""
邮件服务模块 - 发送验证码邮件
"""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import random
import string
from datetime import datetime, timedelta
from typing import Dict

load_dotenv()

# 验证码存储 {email: {"code": "123456", "expires": datetime}}
verification_codes: Dict[str, dict] = {}

def generate_code(length: int = 6) -> str:
    """生成随机验证码"""
    return ''.join(random.choices(string.digits, k=length))

def store_code(email: str, code: str, expires_minutes: int = 10):
    """存储验证码"""
    verification_codes[email] = {
        "code": code,
        "expires": datetime.utcnow() + timedelta(minutes=expires_minutes)
    }

def verify_code(email: str, code: str) -> bool:
    """验证验证码"""
    if email not in verification_codes:
        return False
    
    stored = verification_codes[email]
    
    # 检查是否过期
    if datetime.utcnow() > stored["expires"]:
        del verification_codes[email]
        return False
    
    # 验证码是否匹配
    if stored["code"] != code:
        return False
    
    # 验证成功后删除
    del verification_codes[email]
    return True

async def send_verification_email(to_email: str, code: str) -> bool:
    """发送验证码邮件"""
    
    # 获取邮件配置
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    from_email = os.getenv("FROM_EMAIL", smtp_user)
    app_name = os.getenv("APP_NAME", "心理医生助手")
    
    if not smtp_user or not smtp_password:
        # 测试模式：不发送真实邮件，使用固定验证码
        print(f"[TEST MODE] 验证码邮件 -> {to_email}: {code}")
        return True
    
    try:
        # 创建邮件
        message = MIMEMultipart("alternative")
        message["Subject"] = f"{app_name} - 验证码"
        message["From"] = from_email
        message["To"] = to_email
        
        # 邮件内容
        text_content = f"""
        您好！
        
        您的验证码是：{code}
        
        验证码有效期为10分钟，请及时使用。
        如果这不是您的操作，请忽略此邮件。
        
        {app_name}
        """
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #409eff;">验证码通知</h2>
                <p>您好！</p>
                <p>您的验证码是：</p>
                <div style="background-color: #f0f0f0; padding: 15px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 5px; margin: 20px 0;">
                    {code}
                </div>
                <p style="color: #666; font-size: 14px;">验证码有效期为10分钟，请及时使用。</p>
                <p style="color: #666; font-size: 14px;">如果这不是您的操作，请忽略此邮件。</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="color: #999; font-size: 12px;">{app_name}</p>
            </div>
        </body>
        </html>
        """
        
        part1 = MIMEText(text_content, "plain", "utf-8")
        part2 = MIMEText(html_content, "html", "utf-8")
        
        message.attach(part1)
        message.attach(part2)
        
        # 发送邮件
        # 根据端口选择连接方式：465用SSL，587用TLS
        if smtp_port == 465:
            # SSL连接
            await aiosmtplib.send(
                message,
                hostname=smtp_host,
                port=smtp_port,
                username=smtp_user,
                password=smtp_password,
                use_tls=True,
            )
        else:
            # STARTTLS连接（587端口）
            await aiosmtplib.send(
                message,
                hostname=smtp_host,
                port=smtp_port,
                username=smtp_user,
                password=smtp_password,
                start_tls=True,
            )
        
        print(f"验证码邮件已发送至: {to_email}")
        return True
        
    except Exception as e:
        print(f"发送邮件失败: {str(e)}")
        return False
