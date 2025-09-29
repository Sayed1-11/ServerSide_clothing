import threading
import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)

def send_checkout_email(email, subject, template, context):
    def send_sync():
        try:
            logger.info(f"Starting email send to: {email}")
            
            # Render template
            message = render_to_string(template, context)
            logger.info("Template rendered successfully")
            
            # Create email
            email_obj = EmailMultiAlternatives(
                subject=subject,
                body='Order Confirmation',  # Plain text fallback
                from_email=settings.EMAIL_HOST_USER,
                to=[email]
            )
            email_obj.attach_alternative(message, "text/html")
            
            # Send email
            email_obj.send(fail_silently=False)
            logger.info(f"Email sent successfully to {email}")
            
        except Exception as e:
            logger.error(f"Email failed for {email}: {str(e)}")
    
    # Start background thread
    thread = threading.Thread(target=send_sync)
    thread.daemon = True  # This allows the main process to exit without waiting for thread
    thread.start()
    logger.info(f"Email thread started for {email}")
    
    return True