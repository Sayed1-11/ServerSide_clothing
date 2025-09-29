from background_task import background
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

@background(schedule=5)  # Run 5 seconds later
def send_checkout_email_background(email, subject, template, context):
    try:
        message = render_to_string(template, context)
        send_email = EmailMultiAlternatives(
            subject, 
            '', 
            from_email=settings.EMAIL_HOST_USER, 
            to=[email]
        )
        send_email.attach_alternative(message, "text/html")
        send_email.send()
        print(f"Email sent successfully to {email}")
        return True
    except Exception as e:
        print(f"Email sending failed: {str(e)}")
        return False