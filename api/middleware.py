import random
import string
from datetime import timedelta
from django.core.cache import cache
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.utils.deprecation import MiddlewareMixin
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse


def generate_random_username():
    return 'anonymous#' + ''.join(random.choices(string.digits, k=8))


class AnonymousSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, 'user') and not request.user.is_authenticated:
            if 'anon_username' not in request.session:
                request.session['anon_username'] = generate_random_username()
                request.session.set_expiry(timedelta(days=4))

        response = self.get_response(request)
        return response


class TokenBlacklistMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth = JWTAuthentication()
        try:
            user_auth_tuple = auth.authenticate(request)
            if user_auth_tuple is not None:
                user, token = user_auth_tuple
                if user.is_banned:
                    return JsonResponse({'detail': 'Token blacklisted'}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            pass

        response = self.get_response(request)
        return response
