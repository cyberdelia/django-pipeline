from __future__ import annotations

import base64
import os
import posixpath
import re
import subprocess
import warnings
from collections.abc import Iterator, Sequence
from itertools import takewhile

from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils.encoding import force_str, smart_bytes

from pipeline.conf import settings
from pipeline.exceptions import CompressorError
from pipeline.utils import relpath, set_std_streams_blocking, to_class

# Regex matching url(...), url('...'), and url("...") patterns.
#
# Replacements will preserve the quotes and any whitespace contained within
# the pattern, transforming only the filename.
#
# Verbose and documented, to ease future maintenance.
_CSS_URL_REWRITE_PATH_RE_STR = r"""
    (?P<url_prefix>
      url\(                 # The opening `url(`.
      (?P<url_quote>['"]?)  # Optional quote (' or ").
      \s*
    )
    (?P<url_path>.*?)       # The path to capture.
    (?P<url_suffix>
      (?P=url_quote)        # The quote found earlier, if any.
      \s*
      \)                    # The end `)`, completing `url(...)`.
    )
"""


# Regex matching `//@ sourceMappingURL=...` and variants.
#
# This will capture sourceMappingURL and sourceURL keywords, both
# `//@` and `//#` variants, and both `//` and `/* ... */` comment types.
#
# Verbose and documented, to ease future maintenance.
_SOURCEMAP_REWRITE_PATH_RE_STR = r"""
    (?P<sourcemap_prefix>
      /(?:/|(?P<sourcemap_mlcomment>\*))  # Opening comment (`//#`, `//@`,
      [#@]\s+                             # `/*@`, `/*#`).
      source(?:Mapping)?URL=              # The sourcemap indicator.
      \s*
    )
    (?P<sourcemap_path>.*?)               # The path to capture.
    (?P<sourcemap_suffix>
      \s*
      (?(sourcemap_mlcomment)\*/\s*)      # End comment (`*/`)
    )
    $                                     # The line should now end.
"""


# Implementation of the above regexes, for CSS and JavaScript.
CSS_REWRITE_PATH_RE = re.compile(
    f"{_CSS_URL_REWRITE_PATH_RE_STR}|{_SOURCEMAP_REWRITE_PATH_RE_STR}", re.X | re.M
)
JS_REWRITE_PATH_RE = re.compile(_SOURCEMAP_REWRITE_PATH_RE_STR, re.X | re.M)


URL_REPLACER = re.compile(r"""url\(__EMBED__(.+?)(\?\d+)?\)""")
NON_REWRITABLE_URL = re.compile(r"^(#|http:|https:|data:|//)")

DEFAULT_TEMPLATE_FUNC = "template"
TEMPLATE_FUNC = r"""var template = function(str){var fn = new Function('obj', 'var __p=[],print=function(){__p.push.apply(__p,arguments);};with(obj||{}){__p.push(\''+str.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/<%=([\s\S]+?)%>/g,function(match,code){return "',"+code.replace(/\\'/g, "'")+",'";}).replace(/<%([\s\S]+?)%>/g,function(match,code){return "');"+code.replace(/\\'/g, "'").replace(/[\r\n\t]/g,' ')+"__p.push('";}).replace(/\r/g,'\\r').replace(/\n/g,'\\n').replace(/\t/g,'\\t')+"');}return __p.join('');");return fn;};"""  # noqa

MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
    ".ttf": "font/truetype",
    ".otf": "font/opentype",
    ".woff": "font/woff",
}
EMBED_EXTS = MIME_TYPES.keys()
FONT_EXTS = [".ttf", ".otf", ".woff"]


class Compressor:
    asset_contents = {}

    def __init__(self, storage=None, verbose=False):
        if storage is None:
            storage = staticfiles_storage
        self.storage = storage
        self.verbose = verbose

    @property
    def js_compressor(self):
        return to_class(settings.JS_COMPRESSOR)

    @property
    def css_compressor(self):
        return to_class(settings.CSS_COMPRESSOR)

    @property
    def html_compressor(self):
        return to_class(settings.HTML_COMPRESSOR)

    def compress_js(
        self,
        paths: Sequence[str],
        templates: Sequence[str] | None = None,
        *,
        output_filename: str | None = None,
        **kwargs,
    ) -> str:
        """Concatenate and compress JS files"""
        # Note how a semicolon is added between the two files to make sure that
        # their behavior is not changed. '(expression1)\n(expression2)' calls
        # `expression1` with `expression2` as an argument! Superfluous
        # semicolons are valid in JavaScript and will be removed by the
        # minifier.
        js = self.concatenate(
            paths,
            file_sep=";",
            output_filename=output_filename,
            rewrite_path_re=JS_REWRITE_PATH_RE,
        )

        if templates:
            js = js + self.compile_templates(templates)

        if not settings.DISABLE_WRAPPER:
            js = settings.JS_WRAPPER % js

        compressor = self.js_compressor
        if compressor:
            js = getattr(compressor(verbose=self.verbose), "compress_js")(js)

        return js

    def compress_css(self, paths, output_filename, variant=None, **kwargs):
        """Concatenate and compress CSS files"""
        css = self.concatenate(
            paths,
            file_sep="",
            rewrite_path_re=CSS_REWRITE_PATH_RE,
            output_filename=output_filename,
            variant=variant,
        )
        compressor = self.css_compressor
        if compressor:
            css = getattr(compressor(verbose=self.verbose), "compress_css")(css)
        if not variant:
            return css
        elif variant == "datauri":
            return self.with_data_uri(css)
        else:
            raise CompressorError(f'"{variant}" is not a valid variant')

    def compress_html(self, html, **kwargs):
        """Minify HTML response"""
        compressor = self.html_compressor
        if compressor:
            html = getattr(compressor(verbose=self.verbose), "compress_html")(html)
        return html

    def compile_templates(self, paths):
        compiled = []
        if not paths:
            return ""
        namespace = settings.TEMPLATE_NAMESPACE
        base_path = self.base_path(paths)
        for path in paths:
            contents = self.read_text(path)
            contents = re.sub("\r?\n", "\\\\n", contents)
            contents = re.sub("'", "\\'", contents)
            name = self.template_name(path, base_path)
            compiled.append(
                "{}['{}'] = {}('{}');\n".format(
                    namespace, name, settings.TEMPLATE_FUNC, contents
                )
            )
        if settings.TEMPLATE_FUNC == DEFAULT_TEMPLATE_FUNC:
            compiler = TEMPLATE_FUNC
        else:
            compiler = ""
        return "\n".join(
            [
                "{namespace} = {namespace} || {{}};".format(namespace=namespace),
                compiler,
                "".join(compiled),
            ]
        )

    def base_path(self, paths):
        def names_equal(name):
            return all(n == name[0] for n in name[1:])

        directory_levels = zip(*[p.split(os.sep) for p in paths])
        return os.sep.join(x[0] for x in takewhile(names_equal, directory_levels))

    def template_name(self, path, base):
        """Find out the name of a JS template"""
        if not base:
            path = os.path.basename(path)
        if path == base:
            base = os.path.dirname(path)
        name = re.sub(
            r"^{}[\/\\]?(.*){}$".format(
                re.escape(base), re.escape(settings.TEMPLATE_EXT)
            ),
            r"\1",
            path,
        )
        return re.sub(r"[\/\\]", settings.TEMPLATE_SEPARATOR, name)

    def concatenate_and_rewrite(self, paths, output_filename, variant=None):
        """Concatenate together files and rewrite urls"""
        warnings.warn(
            "Compressor.concatenate_and_rewrite() is deprecated. Please "
            "call concatenate() instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.concatenate(
            paths=paths,
            file_sep="",
            rewrite_path_re=CSS_REWRITE_PATH_RE,
            output_filename=output_filename,
            variant=variant,
        )

    def concatenate(
        self,
        paths: Sequence[str],
        *,
        file_sep: str | None = None,
        output_filename: str | None = None,
        rewrite_path_re: re.Pattern | None = None,
        variant: str | None = None,
    ) -> str:
        """Concatenate together a list of files.

        The caller can specify a delimiter between files and any regexes
        used to normalize relative paths. Path normalization is important for
        ensuring that local resources or sourcemaps can be updated in time
        for Django's static media post-processing phase.
        """

        def _reconstruct(
            m: re.Match,
            source_path: str,
        ) -> str:
            groups = m.groupdict()
            asset_path: str | None = None
            prefix = ""
            suffix = ""

            for prefix in ("sourcemap", "url"):
                asset_path = groups.get(f"{prefix}_path")

                if asset_path is not None:
                    asset_path = asset_path.strip()
                    prefix, suffix = m.group(f"{prefix}_prefix", f"{prefix}_suffix")
                    break

            if asset_path is None:
                # This is empty. Return the whole match as-is.
                return m.group()

            if asset_path and not NON_REWRITABLE_URL.match(asset_path):
                asset_path = self.construct_asset_path(
                    asset_path=asset_path,
                    source_path=source_path,
                    output_filename=output_filename,
                    variant=variant,
                )

            return f"{prefix}{asset_path}{suffix}"

        def _iter_files() -> Iterator[str]:
            if not output_filename or not rewrite_path_re:
                # This is legacy call, which does not support sourcemap-aware
                # asset rewriting. Pipeline itself won't invoke this outside
                # of tests, but it maybe important for third-parties who
                # are specializing these classes.
                warnings.warn(
                    "Compressor.concatenate() was called without passing "
                    "rewrite_path_re_= or output_filename=. If you are "
                    "specializing Compressor, please update your call "
                    "to remain compatible with future changes.",
                    DeprecationWarning,
                    stacklevel=3,
                )

                return (self.read_text(path) for path in paths)

            # Now that we can attempt the modern support for concatenating
            # files, handling rewriting of relative assets in the process.
            return (
                rewrite_path_re.sub(
                    lambda m: _reconstruct(m, path), self.read_text(path)
                )
                for path in paths
            )

        if file_sep is None:
            warnings.warn(
                "Compressor.concatenate() was called without passing "
                "file_sep=. If you are specializing Compressor, please "
                "update your call to remain compatible with future changes. "
                "Defaulting to JavaScript behavior for "
                "backwards-compatibility.",
                DeprecationWarning,
                stacklevel=2,
            )
            file_sep = ";"

        return f"\n{file_sep}".join(_iter_files())

    def construct_asset_path(
        self, asset_path, source_path, output_filename, variant=None
    ):
        """Return a rewritten asset URL for a stylesheet or JavaScript file."""
        public_path = self.absolute_path(
            asset_path,
            os.path.dirname(source_path).replace("\\", "/"),
        )
        if self.embeddable(public_path, variant):
            return f"__EMBED__{public_path}"
        if not posixpath.isabs(asset_path):
            asset_path = self.relative_path(public_path, output_filename)
        return asset_path

    def embeddable(self, path, variant):
        """Is the asset embeddable ?"""
        name, ext = os.path.splitext(path)
        font = ext in FONT_EXTS
        if not variant:
            return False
        if not (
            re.search(settings.EMBED_PATH, path.replace("\\", "/"))
            and self.storage.exists(path)
        ):
            return False
        if ext not in EMBED_EXTS:
            return False
        if not (
            font or len(self.encoded_content(path)) < settings.EMBED_MAX_IMAGE_SIZE
        ):
            return False
        return True

    def with_data_uri(self, css):
        def datauri(match):
            path = match.group(1)
            mime_type = self.mime_type(path)
            data = self.encoded_content(path)
            return f'url("data:{mime_type};charset=utf-8;base64,{data}")'

        return URL_REPLACER.sub(datauri, css)

    def encoded_content(self, path):
        """Return the base64 encoded contents"""
        if path in self.__class__.asset_contents:
            return self.__class__.asset_contents[path]
        data = self.read_bytes(path)
        self.__class__.asset_contents[path] = force_str(base64.b64encode(data))
        return self.__class__.asset_contents[path]

    def mime_type(self, path):
        """Get mime-type from filename"""
        name, ext = os.path.splitext(path)
        return MIME_TYPES[ext]

    def absolute_path(self, path, start):
        """
        Return the absolute public path for an asset,
        given the path of the stylesheet that contains it.
        """
        if posixpath.isabs(path):
            path = posixpath.join(staticfiles_storage.location, path)
        else:
            path = posixpath.join(start, path)
        return posixpath.normpath(path)

    def relative_path(self, absolute_path, output_filename):
        """Rewrite paths relative to the output stylesheet path"""
        absolute_path = posixpath.join(settings.PIPELINE_ROOT, absolute_path)
        output_path = posixpath.join(
            settings.PIPELINE_ROOT, posixpath.dirname(output_filename)
        )
        return relpath(absolute_path, output_path)

    def read_bytes(self, path):
        """Read file content in binary mode"""
        file = staticfiles_storage.open(path)
        content = file.read()
        file.close()
        return content

    def read_text(self, path):
        content = self.read_bytes(path)
        return force_str(content)


class CompressorBase:
    def __init__(self, verbose):
        self.verbose = verbose

    def filter_css(self, css):
        raise NotImplementedError

    def filter_js(self, js):
        raise NotImplementedError


class SubProcessCompressor(CompressorBase):
    def execute_command(self, command, content):
        argument_list = []
        for flattening_arg in command:
            if isinstance(flattening_arg, (str,)):
                argument_list.append(flattening_arg)
            else:
                argument_list.extend(flattening_arg)

        pipe = subprocess.Popen(
            argument_list,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if content:
            content = smart_bytes(content)
        stdout, stderr = pipe.communicate(content)
        set_std_streams_blocking()
        if stderr.strip() and pipe.returncode != 0:
            raise CompressorError(force_str(stderr))
        elif self.verbose:
            print(force_str(stderr))
        return force_str(stdout)


class NoopCompressor(CompressorBase):
    def compress_js(self, js):
        return js

    def compress_css(self, css):
        return css

    def compress_html(self, html):
        return html
