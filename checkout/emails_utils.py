import threading
import logging
import os
from django.template.loader import render_to_string
import requests

logger = logging.getLogger(__name__)

def send_checkout_email(email, subject, template, context):
    """Send email using Brevo API"""
    
    def send_sync():
        try:
            api_key = os.environ.get('BREVO_API_KEY')
            if not api_key:
                logger.error("❌ BREVO_API_KEY not set")
                return False
            
            # Render template
            html_content = render_to_string(template, context)
            
            # Send via Brevo API
            response = requests.post(
                'https://api.brevo.com/v3/smtp/email',
                headers={
                    'api-key': api_key,
                    'Content-Type': 'application/json'
                },
                json={
                    'sender': {
                        'name': 'Aurify Studio',
                        'email': 'aursifystudio@gmail.com'  # Your Gmail works here
                    },
                    'to': [{'email': email}],
                    'subject': subject,
                    'htmlContent': html_content
                }
            )
            
            if response.status_code == 201:
                logger.info(f"✅ Brevo email sent successfully to {email}")
                return True
            else:
                logger.error(f"❌ Brevo API failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Email failed: {str(e)}")
            return False
    
    thread = threading.Thread(target=send_sync, daemon=True)
    thread.start()
    return True