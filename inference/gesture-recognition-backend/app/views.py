from django.http import JsonResponse

def get_gesture_data(request):
    """Returns sample gesture data for testing."""
    return JsonResponse({"gesture": "wave", "confidence": 0.95})
