import threading
import logging
import os
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)

def send_checkout_email(email, subject, template, context):
    """Send email in background thread with production logging"""
    
    def send_sync():
        try:
            logger.info(f"🟡 Starting email send to: {email}")
            logger.info(f"🟡 Environment: {'Production' if os.environ.get('RENDER') else 'Development'}")
            
            # Check environment
            if os.environ.get('RENDER'):
                logger.info("🟡 Running on Render - using production email settings")
            
            # Render template
            message = render_to_string(template, context)
            
            # Create email - USE DEFAULT_FROM_EMAIL instead of EMAIL_HOST_USER
            email_obj = EmailMultiAlternatives(
                subject=subject,
                body='Thank you for your order!',
                from_email=settings.DEFAULT_FROM_EMAIL,  # ← FIXED: Use DEFAULT_FROM_EMAIL
                to=[email]
            )
            email_obj.attach_alternative(message, "text/html")
            
            # Send email
            email_obj.send()
            logger.info(f"✅ Email sent successfully to {email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Email failed for {email}: {str(e)}")
            logger.error(f"❌ Email backend: {getattr(settings, 'EMAIL_BACKEND', 'Not set')}")
            logger.error(f"❌ Email host: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
            logger.error(f"❌ From email: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}")
            return False
    
    thread = threading.Thread(target=send_sync, daemon=True)
    thread.start()
    return True