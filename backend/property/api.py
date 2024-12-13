from django.http import JsonResponse
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from .models import Property, Reservation
from .serializers import PropertyListSerializer, PropertyDetailSerializer, ResirvationListSerializer, BookingSerializer
from .forms import PropertyForm
from django.shortcuts import get_object_or_404
from useraccounts.models import User
from rest_framework.exceptions import AuthenticationFailed
from .tasks import send_property_creation_message
from django.forms.models import model_to_dict
import stripe
from my_stripe.views import product_checkout_view
from django.conf import settings
from rest_framework_simplejwt.tokens import AccessToken


stripe.api_key = settings.STRIPE_SECRET_KEY
@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def properties_list(request):
    user = None
    try:
        # Extract token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            raise AuthenticationFailed('Authorization token not provided')

        token = auth_header.split('Bearer ')[1]
        token = AccessToken(token)

        # Debugging the payload
        print("Token Payload:", token.payload)

        # Extract user ID from token payload
        user_id = token.payload.get('user', {}).get('pk')  # Correct way to extract pk
        if user_id is None:
            raise AuthenticationFailed('User ID not found in token')
        
        user = User.objects.get(pk=user_id)
    except KeyError:
        raise AuthenticationFailed('Authorization token not provided')
    except (AuthenticationFailed, User.DoesNotExist):
        user = None

    favorites = []
    country = request.GET.get('country', '')
    category = request.GET.get('category', '')
    checkin_date = request.GET.get('checkIn', '')
    checkout_date = request.GET.get('checkOut', '')
    bedrooms = request.GET.get('numBedrooms', '')
    bathrooms = request.GET.get('numBathrooms', '')
    guests = request.GET.get('numGuests', '')
    is_favorites = request.GET.get('is_favorites', '')

    # Filter properties based on query parameters
    qs = Property.objects.all()
    landlord_id = request.GET.get('landlord_id')
    if landlord_id:
        qs = qs.filter(landlord_id=landlord_id)
    if is_favorites:
        if user and user.is_authenticated:
            # Filter properties that are favorited by the authenticated user
            qs = qs.filter(favorited=user)
        else:
            # If the user is not authenticated, return an empty queryset
            qs = qs.none()
    if checkin_date and checkout_date:
        exact_matches = Reservation.objects.filter(start_date=checkin_date) | Reservation.objects.filter(end_date=checkout_date)
        overlap_matches = Reservation.objects.filter(start_date__lte=checkout_date, end_date__gte=checkin_date)
        all_matches = []
        for reservation in exact_matches | overlap_matches:
            all_matches.append(reservation.property_id)
        qs = qs.exclude(id__in=all_matches)

    # Collect IDs of favorite properties
    if user and user.is_authenticated:
        print(f"Authenticated User: {user.pk}")
        favorites = Property.objects.filter(favorited=user).values_list('id', flat=True)
        print(f"Favorite Properties IDs: {list(favorites)}")
    else:
        print("User is not authenticated or does not exist")
        favorites = []
    if guests:
        qs = qs.filter(guests__gte=guests)
    if bedrooms:
        qs = qs.filter(bedrooms__gte=bedrooms)
    if bathrooms:
        qs = qs.filter(bathrooms__gte=bathrooms)
    if country:
        qs = qs.filter(country=country)
    if category and category != 'undefined':
        qs = qs.filter(category=category)
    
    print(f"Favorites: {favorites}")

    serializer = PropertyListSerializer(qs, many=True)
    return JsonResponse({
        'data': serializer.data,  # List of properties
        'favorites': list(favorites),  # List of favorite property IDs
    })

@api_view(['POST', 'FILES'])
def create_property(request):
    try:
        print("Received new property creation request")
        print(request.user)
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            property = form.save(commit=False)
            property.landlord = request.user

            # Save the property instance first
            property.save()

            # Serialize the property data
            property_data = model_to_dict(property)
            # Handle the image field manually
            if property.image:
                property_data['image'] = property.image.url
            else:
                property_data['image'] = None

            # Pass serialized data to the message sender
            property_data['landlord_email'] = request.user.email
            property_data['landlord_name'] = request.user.name
            send_property_creation_message.delay(property_data)

            return JsonResponse({'success': True, 'property': property_data})
        else:
            print('Error', form.errors, form.non_field_errors)
            return JsonResponse({'errors': form.errors.as_json()}, status=400)
    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


    

@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def properties_detail(request, pk):
    object = Property.objects.get(id=pk)
    serializer = PropertyDetailSerializer(object, many=False)
    return JsonResponse(
        serializer.data
    )

@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def properties_reservations(request, pk):
    property = Property.objects.get(pk=pk)
    reservations = property.reservations.all()
    serializer = ResirvationListSerializer(reservations, many=True)
    return JsonResponse(
        serializer.data,
        safe=False
    )

# @api_view(['POST'])
# def book_property(request, pk):
#     try:
#         # Accessing data from the request in DRF
#         start_date = request.data.get('start_date', '')
#         end_date = request.data.get('end_date', '')
#         total_price = request.data.get('total_price', '')
#         number_of_nights = request.data.get('number_of_nights', '')
#         guests = request.data.get('guests', '')
        
#         # Retrieve the property and create a reservation
#         property = Property.objects.get(pk=pk)

#         Reservation.objects.create(
#             property=property,
#             start_date=start_date,
#             end_date=end_date,
#             number_of_nights=number_of_nights,
#             total_price=total_price,
#             guests=guests,
#             created_by=request.user
#         )
#         return JsonResponse({'success': True})

#     except Exception as e:
#         print('Error', e)
#         return JsonResponse({'success': False}, status=400)


@api_view(['POST'])
def book_property(request, pk):
    try:
        # Accessing data from the request
        start_date = request.data.get('start_date', '')
        end_date = request.data.get('end_date', '')
        total_price = request.data.get('total_price', '')
        number_of_nights = request.data.get('number_of_nights', '')
        guests = request.data.get('guests', '')
        has_paid = request.data.get('has_paid', False)

        # Retrieve the property
        property = Property.objects.get(pk=pk)

        # Create Stripe Checkout session
        
        checkout_session = product_checkout_view(request, property, pk, total_price, start_date, end_date, number_of_nights, guests, has_paid)
        # Return the checkout session URL to redirect the user
        return JsonResponse({'url': checkout_session.url})

    except Exception as e:
        print('Error:', e)
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@api_view(['POST'])
def toggle_favorite(request, pk):

    if not request.user.is_authenticated:
        return JsonResponse({'detail': 'Authentication required.'}, status=401)
    
    property = get_object_or_404(Property, pk=pk)

    if request.user in property.favorited.all():
        property.favorited.remove(request.user)
        return JsonResponse({'is_favorited': False})
    else:
        property.favorited.add(request.user)
        return JsonResponse({'is_favorited': True})
    