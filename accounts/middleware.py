from django.utils import translation
from django.conf import settings


class UserLanguageMiddleware:
    """
    Middleware to activate user's preferred language from their profile
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if user is authenticated and has a language preference
        if request.user.is_authenticated and hasattr(request.user, 'language'):
            language = request.user.language
            if language in [lang[0] for lang in settings.LANGUAGES]:
                translation.activate(language)
                request.LANGUAGE_CODE = language
        else:
            # Check session for language preference
            language = request.session.get('django_language')
            if language and language in [lang[0] for lang in settings.LANGUAGES]:
                translation.activate(language)
                request.LANGUAGE_CODE = language

        response = self.get_response(request)
        translation.deactivate()
        return response
