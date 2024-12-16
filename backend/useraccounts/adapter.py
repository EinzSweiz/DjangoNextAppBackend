from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.models import EmailAddress
from allauth.account.utils import setup_user_email
from .models import User

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # Check if the user already exists with the social email
        existing_user = User.objects.filter(email=sociallogin.user.email).first()
        if existing_user:
            sociallogin.user = existing_user
        else:
            print("No existing user found with the given email.")
        
        # Ensure the email is correctly set
        if not sociallogin.user.email:
            sociallogin.user.email = sociallogin.account.extra_data.get('email')

        if not sociallogin.user.email:
            raise AssertionError("Email not set properly for the user during social login.")
        
        # Handle the email in the EmailAddress model
        email_address = EmailAddress.objects.filter(email=sociallogin.user.email).first()
        if email_address:
            # Email exists, mark it as verified if needed
            email_address.verified = True
            email_address.save()
        else:
            # If the email does not exist in the EmailAddress model, create it
            email_address = EmailAddress.objects.create(user=sociallogin.user, email=sociallogin.user.email, verified=True)
        
        # Call the parent method to continue with the social login
        return super().pre_social_login(request, sociallogin)