import threading
from django.core.cache import cache

class UploadProgressMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'POST' and request.META.get('CONTENT_LENGTH'):
            request.upload_id = str(threading.current_thread().ident)
            cache.set(f'upload_progress_{request.upload_id}', {
                'total': int(request.META.get('CONTENT_LENGTH', 0)),
                'uploaded': 0
            })

            def callback(chunks):
                for chunk in chunks:
                    progress = cache.get(f'upload_progress_{request.upload_id}')
                    if progress:
                        progress['uploaded'] += len(chunk)
                        cache.set(f'upload_progress_{request.upload_id}', progress)
                    yield chunk

            request._body_file = callback(request._body_file)

        response = self.get_response(request)

        if hasattr(request, 'upload_id'):
            cache.delete(f'upload_progress_{request.upload_id}')

        return response 