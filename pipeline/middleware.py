from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.exceptions import MiddlewareNotUsed
from django.utils.deprecation import MiddlewareMixin
from django.utils.encoding import DjangoUnicodeDecodeError

from pipeline.compressors import Compressor
from pipeline.conf import settings


class MinifyHTMLMiddleware(MiddlewareMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not settings.PIPELINE_ENABLED:
            raise MiddlewareNotUsed

    def process_response(self, request, response):
        if (
            response.has_header("Content-Type")
            and "text/html" in response["Content-Type"]
        ):
            compressor = Compressor(storage=staticfiles_storage, verbose=False)
            try:
                response.content = compressor.compress_html(
                    response.content.decode("utf-8")
                )
                response["Content-Length"] = str(len(response.content))
            except DjangoUnicodeDecodeError:
                pass
        return response
