from django.shortcuts import render
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

def product_checkout_view(request, property, pk, total_price, start_date, end_date, number_of_nights, guests, has_paid, payment_method):
    # Determine currency based on the selected payment method
    if payment_method == "blik":
        currency = "pln"  # BLIK only supports PLN
    else:
        currency = "usd"  # Default currency is USD for other methods like PayPal or cards

    checkout_session = stripe.checkout.Session.create(
        line_items=[
            {
                'price_data': {
                    'currency': currency,  # Dynamically set currency
                    'product_data': {
                        'name': property.title,
                    },
                    'unit_amount': int(float(total_price) * 100),  # Stripe expects amount in cents
                },
                'quantity': 1,
            },
        ],
        mode='payment',
        payment_method=[i for i in ['card', 'blik', 'paypal']],
        payment_method_types=[
            'card',  # Credit/Debit cards
            'blik',  # BLIK payments
            'paypal',  # PayPal payments
        ],
        customer_creation='always',
        success_url='http://165.22.76.137/payment/success?session_id={CHECKOUT_SESSION_ID}',  # Redirect to success URL after payment
        cancel_url=request.build_absolute_uri(f'/payment/cancel/{pk}/'),  # Redirect to cancel URL if payment fails
        customer_email=request.user.email,  # Optional: Prefill user email in checkout
        metadata={
            'property_id': pk,
            'start_date': start_date,
            'end_date': end_date,
            'number_of_nights': number_of_nights,
            'guests': guests,
            'total_price': total_price,
            'has_paid': has_paid,
        }
    )
    return checkout_session
