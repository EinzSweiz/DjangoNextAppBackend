from .serializers import UserDetailSerializer, UserProfileUpdateSerializer, UserProfileSerializer
from django.http import JsonResponse
from .models import User
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from property.serializers import ResirvationListSerializer
import logging

logger = logging.getLogger(__name__)
@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def landlord_detail(request, pk):
    user = User.objects.get(pk=pk)
    serializer = UserDetailSerializer(user, many=False)
    return JsonResponse(serializer.data, safe=False)


@api_view(['GET'])
def reservations_list(request):
    qs = request.user.reservations.all()
    serializer = ResirvationListSerializer(qs, many=True)
    return JsonResponse(serializer.data, safe=False)


def profile_detail(request, pk):
    try:
        user = User.objects.get(pk=pk)
        logger.debug(f"User details: {vars(user)}")
        for user in User.objects.all():
            try:
                str(user.name)
                str(user.email)
            except UnicodeDecodeError:
                logger.error(f"Problematic user: {user.id}")
        serializer = UserProfileSerializer(user)
        return JsonResponse(serializer.data)
    except UnicodeDecodeError as e:
        logger.error(f"Encoding error: {e}")
        return JsonResponse({"error": f"Encoding error: {e}"}, status=400)


@api_view(['PUT'])
@authentication_classes([])
@permission_classes([])
def update_profile(request, pk):
    user = User.objects.get(pk=pk)
    serializer = UserProfileUpdateSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return JsonResponse(serializer.data)
    else:
    # Log the serializer errors to check the exact issue
        print(serializer.errors)
        return JsonResponse(serializer.errors, status=400)
