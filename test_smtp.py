"""
测试SMTP连接 - 诊断Zoho邮件服务问题
"""
import asyncio
import aiosmtplib
from email.mime.text import MIMEText

async def test_smtp_connection(host, port, user, password, use_ssl=False):
    """测试SMTP连接"""
    print(f"\n{'='*60}")
    print(f"测试配置: {host}:{port}")
    print(f"用户名: {user}")
    print(f"连接方式: {'SSL' if use_ssl else 'STARTTLS'}")
    print(f"{'='*60}\n")
    
    try:
        # 创建简单测试邮件
        message = MIMEText("测试邮件", "plain", "utf-8")
        message["Subject"] = "测试"
        message["From"] = user
        message["To"] = user  # 发送给自己
        
        if use_ssl:
            # SSL方式 (465端口)
            await aiosmtplib.send(
                message,
                hostname=host,
                port=port,
                username=user,
                password=password,
                use_tls=True,
                timeout=10
            )
        else:
            # STARTTLS方式 (587端口)
            await aiosmtplib.send(
                message,
                hostname=host,
                port=port,
                username=user,
                password=password,
                start_tls=True,
                timeout=10
            )
        
        print("✅ 连接成功！邮件已发送")
        return True
        
    except Exception as e:
        print(f"❌ 连接失败: {type(e).__name__}")
        print(f"   错误详情: {str(e)}")
        return False

async def main():
    # Zoho配置
    user = "offferupup@offerupup.cn"
    password = "5CwMBFRMnbtn"
    
    # 测试不同的配置组合
    tests = [
        ("smtp.zoho.com", 587, False),      # STARTTLS
        ("smtp.zoho.com", 465, True),       # SSL
        ("smtp.zoho.com.cn", 587, False),   # 中国区 STARTTLS
        ("smtp.zoho.com.cn", 465, True),    # 中国区 SSL
        ("smtppro.zoho.com", 587, False),   # Pro版本 STARTTLS
    ]
    
    print("\n开始测试Zoho SMTP连接...\n")
    
    for host, port, use_ssl in tests:
        result = await test_smtp_connection(host, port, user, password, use_ssl)
        if result:
            print(f"\n✅ 找到可用配置: {host}:{port} ({'SSL' if use_ssl else 'STARTTLS'})")
            break
        await asyncio.sleep(1)  # 避免频繁尝试

if __name__ == "__main__":
    asyncio.run(main())
