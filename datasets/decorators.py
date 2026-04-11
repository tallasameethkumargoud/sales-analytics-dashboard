from functools import wraps
from django.shortcuts import redirect
from django.http import JsonResponse
from .models import UserProfile


def get_user_role(user):
    try:
        return user.profile.role
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=user, role="analyst")
        return "analyst"
    except Exception:
        return "analyst"


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("/login/")
            role = get_user_role(request.user)
            if role not in roles:
                return redirect("/analytics/?error=access_denied")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def api_role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({"error": "Not authenticated."}, status=401)
            role = get_user_role(request.user)
            if role not in roles:
                return JsonResponse({"error": f"Access denied. Your role: {role}"}, status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
