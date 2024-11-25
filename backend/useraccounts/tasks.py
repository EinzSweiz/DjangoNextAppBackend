from celery import shared_task
from helpers.messaging import send_message
from .models import User
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.utils.http import urlsafe_base64_encode

@shared_task
def send_confirmation_message(user_id):
    try:
        user = User.objects.get(pk=user_id)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(str(user.id).encode())
        confirmation_url = f"{settings.WEBSITE_URL}/confirm/{uid}/{token}/"
        
        subject = 'Please confirm your email address'
        message = (
            f"Hi {user.username},\n\n"
            f"Please confirm your email address by clicking the link below:\n"
            f"{confirmation_url}\n\n"
            f"Thank you!"
        )
        
        send_message(subject, message, 'riad.sultanov.1999@gmail.com', [user.email])
    except Exception as e:
        print(f"Error sending confirmation email: {e}")
