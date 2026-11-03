from pipeline.compressors import CompressorBase


class DjangoHtmlCompressor(CompressorBase):
    """
    Simple Django HTML minifier using 'django.utils.html.strip_spaces_between_tags()'
    """

    def compress_html(self, html):
        from django.utils.html import strip_spaces_between_tags as minify_html

        return minify_html(html.strip())
