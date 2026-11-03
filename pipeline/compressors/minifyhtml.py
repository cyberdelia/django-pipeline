from pipeline.compressors import CompressorBase
from pipeline.conf import settings


class MinifyHtmlCompressor(CompressorBase):
    """
    HTML compressor based on the Python library minify-html
    (https://pypi.org/project/minify-html).
    """

    def compress_html(self, html):
        import minify_html

        return minify_html.minify(html, **settings.MINIFYHTML_PARAMS)
