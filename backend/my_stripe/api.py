import stripe
from rest_framework.decorators import api_view
from property.serializers import BookingSerializer
from django.http import JsonResponse
from .models import UserPayment
from property.models import Property, Reservation


@api_view(['GET'])
def payment_success(request):
    try:
        # Retrieve session ID from query parameters
        checkout_session_id = request.GET.get('session_id', None)
        if not checkout_session_id:
            return JsonResponse({'success': False, 'error': 'Missing session_id'}, status=400)

        # Retrieve the Stripe session
        session = stripe.checkout.Session.retrieve(checkout_session_id)
        customer_id = session.customer
        customer = stripe.Customer.retrieve(customer_id)

        # Use metadata to get booking details
        metadata = {
            'pk': session.metadata['property_id'],
            'start_date': session.metadata['start_date'],
            'end_date': session.metadata['end_date'],
            'total_price': session.metadata['total_price'],
            'number_of_nights': session.metadata['number_of_nights'],
            'guests': session.metadata['guests'],
        }

        # Validate metadata using BookingSerializer
        serializer = BookingSerializer(data=metadata)
        if not serializer.is_valid():
            return JsonResponse({'success': False, 'errors': serializer.errors}, status=400)

        # Retrieve the property
        property = Property.objects.get(pk=metadata['pk'])

        # Create the reservation
        reservation = Reservation.objects.create(
            property=property,
            start_date=serializer.validated_data['start_date'],
            end_date=serializer.validated_data['end_date'],
            number_of_nights=serializer.validated_data['number_of_nights'],
            total_price=serializer.validated_data['total_price'],
            guests=serializer.validated_data['guests'],
            created_by=request.user
        )

        # Prepare response
        response_data = {
            "success": True,
            "reservation": {
                "id": reservation.id,
                "start_date": reservation.start_date,
                "end_date": reservation.end_date,
                "total_price": float(reservation.total_price),
                "number_of_nights": reservation.number_of_nights,
                "guests": reservation.guests,
                "created_by": request.user.username,
                "property": {
                    "id": property.id,
                    "name": property.name,
                    "address": property.address,
                    "image_url": property.image_url,
                },
            },
            "customer": {
                "id": customer.id,
                "email": customer.email,
                "name": customer.name,
            },
        }

        return JsonResponse(response_data, status=200)

    except Property.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Property not found'}, status=404)

    except Exception as e:
        print('Error:', e)
        return JsonResponse({'success': False, 'error': str(e)}, status=400)



@api_view(['GET'])
def payment_cancel(request, pk):
    return JsonResponse({'success': False, 'message': 'Payment was canceled'})