from rest_framework.decorators import api_view, authentication_classes, permission_classes
from django.http import JsonResponse
from .models import Inquiry
from useraccounts.models import User
from .serializers import CreateInquirySerializer, GetInquirySerializer


@api_view(['POST'])
def create_inquiry(request):
    try:
        serializer = CreateInquirySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        else:
            return JsonResponse(serializer.errors, status=400)
    except Exception as e:
        return JsonResponse(e, status=500)
    

@api_view(['GET'])
def inquiries_view(request):
    if request.user.role == User.RoleChoises.CUSTOMER_SERVICE:
        inquiries = Inquiry.objects.all()
    else:
        inquiries = Inquiry.objects.filter(user=request.user)

    inquiries_serializer = GetInquirySerializer(inquiries, many=True)
    return JsonResponse(inquiries_serializer.data, safe=False)


from django.http import Http404

@api_view(['GET'])
def inquiry_detail_api(request, pk):
    try:
        inquiry = Inquiry.objects.get(pk=pk)
        serializer = GetInquirySerializer(inquiry)
        return JsonResponse(serializer.data, status=200)
    except Inquiry.DoesNotExist:
        raise Http404("Inquiry not found")
    except Exception as e:
        return JsonResponse({'error': 'An unexpected error occurred.'}, status=500)
