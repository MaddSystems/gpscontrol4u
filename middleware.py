from django.utils import translation
from django.utils.deprecation import MiddlewareMixin


class ForceSpanishMiddleware(MiddlewareMixin):
    """
    Middleware to force Spanish language by default
    """
    
    def process_request(self, request):
        # Get language from various sources in order of preference
        language = None
        
        # 1. From session
        if 'django_language' in request.session:
            language = request.session['django_language']
        
        # 2. From cookie
        elif 'django_language' in request.COOKIES:
            language = request.COOKIES['django_language']
        
        # 3. From user profile if authenticated
        elif request.user.is_authenticated and hasattr(request.user, 'language'):
            language = request.user.language
        
        # 4. Default to Spanish
        else:
            language = 'es'
        
        # Ensure it's a valid language
        if language not in ['en', 'es']:
            language = 'es'
        
        # Activate the language
        translation.activate(language)
        
        # Set in session if not already set
        if 'django_language' not in request.session:
            request.session['django_language'] = language
