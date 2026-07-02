from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .auth_service import register_user, login_user

@csrf_exempt
def register_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        user, msg = register_user(username, password, email)
        if user:
            return JsonResponse({'message': msg, 'user_id': user.id}, status=201)
        return JsonResponse({'error': msg}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        tokens, msg = login_user(username, password)
        if tokens:
            return JsonResponse({'message': msg, 'tokens': tokens}, status=200)
        return JsonResponse({'error': msg}, status=401)
    return JsonResponse({'error': 'Method not allowed'}, status=405)