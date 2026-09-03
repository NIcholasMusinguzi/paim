from django.http import JsonResponse


def health(request):
    return JsonResponse({"app": "consent", "status": "ok"})
