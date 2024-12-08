from celery import shared_task
from helpers.messaging import send_message
from useraccounts.models import User
from .models import Property
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone

@shared_task
def send_property_creation_message(property_data):
    try:
        landlord_email = property_data.get('landlord_email', 'noreply@example.com')
        landlord_name = property_data.get('landlord_name', 'User')
    
        subject = 'New Property Created'
        from_email = 'riad.sultanov.1999@gmail.com'
        to_email = landlord_email
    
        html_message = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    h1 {{ color: #1f2937; }}
                    h2 {{ color: #1f2937; }}
                    p {{ color: #4b5563; }}
                    .property-info {{ margin-bottom: 10px; }}
                </style>
            </head>
            <body>
                <h1>Dear {landlord_name},</h1><br>
                <h2>New Property Created</h2>
                <p>A new property has been added:</p>
                <div class="property-info">
                    <strong>Name:</strong> {property_data['title']}<br>
                    <strong>Location:</strong> {property_data['country']}<br>
                    <strong>Price per Night:</strong> ${property_data['price_per_night']}<br>
                    <strong>Bedrooms:</strong> {property_data['bedrooms']}<br>
                    <strong>Bathrooms:</strong> {property_data['bathrooms']}
                </div>
                <p>Thank you for using our service!</p>
            </body>
        </html>
        """
    
        send_message(
            subject=subject,
            message=html_message,
            from_email=from_email,
            to_email=to_email,
        )
    except Exception as e:
        print(f"Error sending confirmation email: {e}")



@shared_task
def send_property_report():
    today = datetime.today()
    properties = Property.objects.filter(created_at__date=today.date())
    
    # Build the HTML report
    html_message = f"""
    <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    color: #333;
                    padding: 20px;
                }}
                h1 {{
                    color: #1f2937;
                    font-size: 24px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }}
                table, th, td {{
                    border: 1px solid #ddd;
                    text-align: left;
                }}
                th {{
                    background-color: #4CAF50;
                    color: white;
                    padding: 10px;
                }}
                td {{
                    padding: 8px;
                }}
                tr:nth-child(even) {{
                    background-color: #f2f2f2;
                }}
            </style>
        </head>
        <body>
            <h1>Property Report - {today.date()}</h1>
            <p>Below is the list of properties created today:</p>
            <table>
                <tr>
                    <th>Name</th>
                    <th>Location</th>
                    <th>Price per Night</th>
                    <th>Bedrooms</th>
                    <th>Bathrooms</th>
                </tr>
    """
    
    for property in properties:
        html_message += f"""
        <tr>
            <td>{property.name}</td>
            <td>{property.location}</td>
            <td>${property.price_per_night}</td>
            <td>{property.bedrooms}</td>
            <td>{property.bathrooms}</td>
        </tr>
        """
    
    html_message += """
            </table>
            <p>Thank you for using our service!</p>
        </body>
    </html>
    """
    
    # Send the email to the admins
    from_email = 'riad.sultanov.1999@gmail.com'  # Replace with a proper email address
    to_email = settings.ADMIN_USER_EMAIL  # Assuming you have a list of admin emails in settings.py
    
    send_message(
        subject=f"Property Report - {today.date()}",
        message=html_message,
        from_email=from_email,
        to_email=to_email,
    )


@shared_task
def archive_old_properties():
    threshold_date = timezone.now() - timedelta(days=365)  # Properties older than 1 year
    old_properties = Property.objects.filter(created_at__lte=threshold_date)

    # Archive properties (e.g., save to a CSV file)
    with open('old_properties.csv', 'w') as f:
        for property in old_properties:
            f.write(f"{property.name}, {property.location}, {property.created_at}\n")
    
    # Optionally, delete old properties
    old_properties.delete()