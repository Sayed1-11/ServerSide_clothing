import threading
import logging
import os
from django.template.loader import render_to_string
import resend

logger = logging.getLogger(__name__)

def send_checkout_email(email, subject, template, context):
    """Send email using Resend API"""
    
    def send_sync():
        try:
            # Check if API key is set
            api_key = os.environ.get('EMAIL_API_KEY')
            if not api_key:
                logger.error("❌ EMAIL_API_KEY not set in environment variables")
                return False
                
            resend.api_key = api_key
            
            logger.info(f"🟡 Starting Resend email to: {email}")
            
            # Render template
            html_content = render_to_string(template, context)
            
            # Send email via Resend
            r = resend.Emails.send({
                "from": os.environ.get('EMAIL'),
                "to": email,
                "subject": subject,
                "html": html_content,
            })
            
            logger.info(f"✅ Resend email sent successfully to {email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Resend email failed for {email}: {str(e)}")
            return False
    
    thread = threading.Thread(target=send_sync, daemon=True)
    thread.start()
    return True