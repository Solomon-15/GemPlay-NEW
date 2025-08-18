"""
Утилиты для отправки email уведомлений
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

logger = logging.getLogger(__name__)

# Email settings from environment variables
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
FROM_EMAIL = os.getenv('FROM_EMAIL', SMTP_USER)
FRONTEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:3000').replace('/api', '')

# Initialize Jinja2 environment
template_dir = Path(__file__).parent / 'email_templates'
template_dir.mkdir(exist_ok=True)
jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))

class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        self.smtp_host = SMTP_HOST
        self.smtp_port = SMTP_PORT
        self.smtp_user = SMTP_USER
        self.smtp_password = SMTP_PASSWORD
        self.from_email = FROM_EMAIL
        
    def _send_email(self, to_email: str, subject: str, html_body: str, text_body: Optional[str] = None):
        """Send email using SMTP"""
        if not self.smtp_user or not self.smtp_password:
            logger.warning(f"Email не отправлен {to_email}: SMTP не настроен")
            return False
            
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text body if provided
            if text_body:
                text_part = MIMEText(text_body, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # Add HTML body
            html_part = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
                
            logger.info(f"Email отправлен на {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки email на {to_email}: {e}")
            return False
    
    def send_email_verification(self, to_email: str, username: str, verification_token: str) -> bool:
        """Send email verification email"""
        verification_url = f"{FRONTEND_URL}/verify-email?token={verification_token}"
        
        subject = "GemPlay - Подтверждение email адреса"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Подтверждение email</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #10B981;">GemPlay</h1>
                <p style="color: #6B7280;">PvP NFT Gem Battle Game</p>
            </div>
            
            <div style="background: #F9FAFB; padding: 30px; border-radius: 10px;">
                <h2 style="color: #1F2937; margin-bottom: 20px;">Добро пожаловать, {username}!</h2>
                
                <p style="color: #4B5563; line-height: 1.6; margin-bottom: 25px;">
                    Спасибо за регистрацию в GemPlay! Для завершения создания аккаунта, 
                    пожалуйста, подтвердите ваш email адрес.
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}" 
                       style="background: #10B981; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 8px; font-weight: bold;
                              display: inline-block;">
                        Подтвердить Email
                    </a>
                </div>
                
                <p style="color: #6B7280; font-size: 14px; line-height: 1.4;">
                    Если кнопка не работает, скопируйте и вставьте эту ссылку в браузер:<br>
                    <a href="{verification_url}" style="color: #10B981; word-break: break-all;">
                        {verification_url}
                    </a>
                </p>
                
                <p style="color: #9CA3AF; font-size: 12px; margin-top: 20px;">
                    Если вы не создавали аккаунт в GemPlay, проигнорируйте это письмо.
                </p>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Добро пожаловать в GemPlay, {username}!
        
        Для подтверждения email адреса перейдите по ссылке:
        {verification_url}
        
        Если вы не создавали аккаунт в GemPlay, проигнорируйте это письмо.
        """
        
        return self._send_email(to_email, subject, html_body, text_body)
    
    def send_password_reset(self, to_email: str, username: str, reset_token: str) -> bool:
        """Send password reset email"""
        reset_url = f"{FRONTEND_URL}/reset-password?token={reset_token}"
        
        subject = "GemPlay - Сброс пароля"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Сброс пароля</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #10B981;">GemPlay</h1>
                <p style="color: #6B7280;">PvP NFT Gem Battle Game</p>
            </div>
            
            <div style="background: #FEF3F2; padding: 30px; border-radius: 10px; border: 1px solid #FCA5A5;">
                <h2 style="color: #DC2626; margin-bottom: 20px;">🔒 Сброс пароля</h2>
                
                <p style="color: #4B5563; line-height: 1.6; margin-bottom: 25px;">
                    Привет, {username}! Мы получили запрос на сброс пароля для вашего аккаунта GemPlay.
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background: #DC2626; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 8px; font-weight: bold;
                              display: inline-block;">
                        Сбросить Пароль
                    </a>
                </div>
                
                <p style="color: #6B7280; font-size: 14px; line-height: 1.4;">
                    Если кнопка не работает, скопируйте и вставьте эту ссылку в браузер:<br>
                    <a href="{reset_url}" style="color: #DC2626; word-break: break-all;">
                        {reset_url}
                    </a>
                </p>
                
                <div style="background: #FEF9C3; padding: 15px; border-radius: 8px; margin: 20px 0; border: 1px solid #FDE047;">
                    <p style="color: #854D0E; font-size: 14px; margin: 0; font-weight: bold;">
                        ⚠️ Важно: Ссылка действительна только 1 час
                    </p>
                </div>
                
                <p style="color: #9CA3AF; font-size: 12px; margin-top: 20px;">
                    Если вы не запрашивали сброс пароля, проигнорируйте это письмо. 
                    Ваш пароль останется неизменным.
                </p>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Сброс пароля - GemPlay
        
        Привет, {username}!
        
        Мы получили запрос на сброс пароля для вашего аккаунта.
        Для сброса пароля перейдите по ссылке (действительна 1 час):
        
        {reset_url}
        
        Если вы не запрашивали сброс пароля, проигнорируйте это письмо.
        """
        
        return self._send_email(to_email, subject, html_body, text_body)

# Global email service instance
email_service = EmailService()

def send_verification_email(to_email: str, username: str, verification_token: str) -> bool:
    """Send email verification"""
    return email_service.send_email_verification(to_email, username, verification_token)

def send_password_reset_email(to_email: str, username: str, reset_token: str) -> bool:
    """Send password reset email"""
    return email_service.send_password_reset(to_email, username, reset_token)