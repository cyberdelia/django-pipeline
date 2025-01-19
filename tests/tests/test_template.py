import base64
import hashlib

from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.management import call_command
from django.template import Context, Template
from django.test import TestCase
from jinja2 import Environment, PackageLoader

from pipeline.jinja2 import PipelineExtension
from tests.utils import pipeline_settings


class JinjaTest(TestCase):
    def setUp(self):
        staticfiles_storage._setup()
        call_command("collectstatic", verbosity=0, interactive=False)
        self.env = Environment(
            extensions=[PipelineExtension],
            loader=PackageLoader("pipeline", "templates"),
        )

    def test_no_package(self):
        template = self.env.from_string("""{% stylesheet "unknow" %}""")
        self.assertEqual("", template.render())
        template = self.env.from_string("""{% javascript "unknow" %}""")
        self.assertEqual("", template.render())

    def test_package_css(self):
        template = self.env.from_string("""{% stylesheet "screen" %}""")
        self.assertEqual(
            '<link href="/static/screen.css" rel="stylesheet" type="text/css" />',
            template.render(),
        )

    @pipeline_settings(PIPELINE_ENABLED=False)
    def test_package_css_disabled(self):
        template = self.env.from_string("""{% stylesheet "screen" %}""")
        self.assertEqual(
            """<link href="/static/pipeline/css/first.css" rel="stylesheet" type="text/css" />
<link href="/static/pipeline/css/second.css" rel="stylesheet" type="text/css" />
<link href="/static/pipeline/css/urls.css" rel="stylesheet" type="text/css" />""",  # noqa
            template.render(),
        )

    def test_package_js(self):
        template = self.env.from_string("""{% javascript "scripts" %}""")
        self.assertEqual(
            '<script type="text/javascript" src="/static/scripts.js" charset="utf-8"></script>',  # noqa
            template.render(),
        )

    def test_package_js_async(self):
        template = self.env.from_string("""{% javascript "scripts_async" %}""")
        self.assertEqual(
            '<script async type="text/javascript" src="/static/scripts_async.js" charset="utf-8"></script>',  # noqa
            template.render(),
        )

    def test_package_js_defer(self):
        template = self.env.from_string("""{% javascript "scripts_defer" %}""")
        self.assertEqual(
            '<script defer type="text/javascript" src="/static/scripts_defer.js" charset="utf-8"></script>',  # noqa
            template.render(),
        )

    def test_package_js_async_defer(self):
        template = self.env.from_string("""{% javascript "scripts_async_defer" %}""")
        self.assertEqual(
            '<script async defer type="text/javascript" src="/static/scripts_async_defer.js" charset="utf-8"></script>',  # noqa
            template.render(),
        )

    def test_crossorigin(self):
        template = self.env.from_string("""{% javascript "scripts_crossorigin" %}""")
        self.assertEqual(
            (
                '<script type="text/javascript" src="/static/scripts_crossorigin.js" '
                'charset="utf-8" crossorigin="anonymous"></script>'
            ),
            template.render(),
        )  # noqa
        template = self.env.from_string("""{% stylesheet "screen_crossorigin" %}""")
        self.assertEqual(
            (
                '<link href="/static/screen_crossorigin.css" rel="stylesheet" '
                'type="text/css" crossorigin="anonymous" />'
            ),
            template.render(),
        )  # noqa

    def test_sri_sha256(self):
        template = self.env.from_string("""{% javascript "scripts_sri_sha256" %}""")
        hash_ = self.get_integrity("scripts_sha256.js", "sha256")
        self.assertEqual(
            (
                '<script type="text/javascript" src="/static/scripts_sha256.js" '
                f'charset="utf-8" integrity="{hash_}"></script>'
            ),
            template.render(),
        )  # noqa
        template = self.env.from_string("""{% stylesheet "screen_sri_sha256" %}""")
        hash_ = self.get_integrity("screen_sri_sha256.css", "sha256")
        self.assertEqual(
            (
                f'<link href="/static/screen_sri_sha256.css" rel="stylesheet" '
                f'type="text/css" integrity="{hash_}" />'
            ),
            template.render(),
        )  # noqa

    def test_sri_sha384(self):
        template = self.env.from_string("""{% javascript "scripts_sri_sha384" %}""")
        hash_ = self.get_integrity("scripts_sha384.js", "sha384")
        self.assertEqual(
            (
                '<script type="text/javascript" src="/static/scripts_sha384.js" '
                f'charset="utf-8" integrity="{hash_}"></script>'
            ),
            template.render(),
        )  # noqa
        template = self.env.from_string("""{% stylesheet "screen_sri_sha384" %}""")
        hash_ = self.get_integrity("screen_sri_sha384.css", "sha384")
        self.assertEqual(
            (
                f'<link href="/static/screen_sri_sha384.css" rel="stylesheet" '
                f'type="text/css" integrity="{hash_}" />'
            ),
            template.render(),
        )  # noqa

    def test_sri_sha512(self):
        template = self.env.from_string("""{% javascript "scripts_sri_sha512" %}""")
        hash_ = self.get_integrity("scripts_sha512.js", "sha512")
        self.assertEqual(
            (
                '<script type="text/javascript" src="/static/scripts_sha512.js" '
                f'charset="utf-8" integrity="{hash_}"></script>'
            ),
            template.render(),
        )  # noqa
        template = self.env.from_string("""{% stylesheet "screen_sri_sha512" %}""")
        hash_ = self.get_integrity("screen_sri_sha512.css", "sha512")
        self.assertEqual(
            (
                f'<link href="/static/screen_sri_sha512.css" rel="stylesheet" '
                f'type="text/css" integrity="{hash_}" />'
            ),
            template.render(),
        )  # noqa

    @staticmethod
    def get_integrity(path, method):
        with staticfiles_storage.open(path) as fd:
            h = getattr(hashlib, method)(fd.read())
        digest = base64.b64encode(h.digest()).decode()
        return f"{method}-{digest}"


class DjangoTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        staticfiles_storage._setup()
        call_command("collectstatic", verbosity=0, interactive=False)

    def render_template(self, template):
        return Template(template).render(Context())

    def test_compressed_empty(self):
        rendered = self.render_template(
            """{% load pipeline %}{% stylesheet "unknow" %}""",
        )
        self.assertEqual("", rendered)

    def test_compressed_css(self):
        rendered = self.render_template(
            """{% load pipeline %}{% stylesheet "screen" %}""",
        )
        self.assertEqual(
            '<link href="/static/screen.css" rel="stylesheet" type="text/css" media="all" />',  # noqa
            rendered,
        )

    def test_compressed_css_media(self):
        rendered = self.render_template(
            """{% load pipeline %}{% stylesheet "screen_media" %}""",
        )
        self.assertEqual(
            '<link href="/static/screen_media.css" rel="stylesheet" type="text/css" media="screen and (min-width:500px)" />',  # noqa
            rendered,
        )

    def test_compressed_css_title(self):
        rendered = self.render_template(
            """{% load pipeline %}{% stylesheet "screen_title" %}""",
        )
        self.assertEqual(
            '<link href="/static/screen_title.css" rel="stylesheet" type="text/css" media="all" title="Default Style" />',  # noqa
            rendered,
        )

    def test_compressed_js(self):
        rendered = self.render_template(
            """{% load pipeline %}{% javascript "scripts" %}""",
        )
        self.assertEqual(
            '<script type="text/javascript" src="/static/scripts.js" charset="utf-8"></script>',  # noqa
            rendered,
        )

    def test_compressed_js_async(self):
        rendered = self.render_template(
            """{% load pipeline %}{% javascript "scripts_async" %}""",
        )
        self.assertEqual(
            '<script async type="text/javascript" src="/static/scripts_async.js" charset="utf-8"></script>',  # noqa
            rendered,
        )

    def test_compressed_js_defer(self):
        rendered = self.render_template(
            """{% load pipeline %}{% javascript "scripts_defer" %}""",
        )
        self.assertEqual(
            '<script defer type="text/javascript" src="/static/scripts_defer.js" charset="utf-8"></script>',  # noqa
            rendered,
        )

    def test_compressed_js_async_defer(self):
        rendered = self.render_template(
            """{% load pipeline %}{% javascript "scripts_async_defer" %}""",
        )
        self.assertEqual(
            '<script async defer type="text/javascript" src="/static/scripts_async_defer.js" charset="utf-8"></script>',  # noqa
            rendered,
        )

    def test_crossorigin(self):
        rendered = self.render_template(
            """{% load pipeline %}{% javascript "scripts_crossorigin" %}"""
        )  # noqa
        self.assertEqual(
            (
                '<script type="text/javascript" src="/static/scripts_crossorigin.js" '
                'charset="utf-8" crossorigin="anonymous"></script>'
            ),
            rendered,
        )  # noqa
        rendered = self.render_template(
            """{% load pipeline %}{% stylesheet "screen_crossorigin" %}"""
        )  # noqa
        self.assertEqual(
            (
                '<link href="/static/screen_crossorigin.css" rel="stylesheet" '
                'type="text/css" media="all" crossorigin="anonymous" />'
            ),
            rendered,
        )  # noqa

    def test_sri_sha256(self):
        rendered = self.render_template(
            """{% load pipeline %}{% javascript "scripts_sri_sha256" %}"""
        )  # noqa
        hash_ = JinjaTest.get_integrity("scripts_sha256.js", "sha256")
        self.assertEqual(
            (
                '<script type="text/javascript" src="/static/scripts_sha256.js" '
                f'charset="utf-8" integrity="{hash_}"></script>'
            ),
            rendered,
        )  # noqa
        rendered = self.render_template(
            """{% load pipeline %}{% stylesheet "screen_sri_sha256" %}"""
        )  # noqa
        hash_ = JinjaTest.get_integrity("screen_sri_sha256.css", "sha256")
        self.assertEqual(
            (
                f'<link href="/static/screen_sri_sha256.css" rel="stylesheet" '
                f'type="text/css" media="all" integrity="{hash_}" />'
            ),
            rendered,
        )  # noqa

    def test_sri_sha384(self):
        rendered = self.render_template(
            """{% load pipeline %}{% javascript "scripts_sri_sha384" %}"""
        )  # noqa
        hash_ = JinjaTest.get_integrity("scripts_sha384.js", "sha384")
        self.assertEqual(
            (
                '<script type="text/javascript" src="/static/scripts_sha384.js" '
                f'charset="utf-8" integrity="{hash_}"></script>'
            ),
            rendered,
        )  # noqa
        rendered = self.render_template(
            """{% load pipeline %}{% stylesheet "screen_sri_sha384" %}"""
        )  # noqa
        hash_ = JinjaTest.get_integrity("screen_sri_sha384.css", "sha384")
        self.assertEqual(
            (
                f'<link href="/static/screen_sri_sha384.css" rel="stylesheet" '
                f'type="text/css" media="all" integrity="{hash_}" />'
            ),
            rendered,
        )  # noqa

    def test_sri_sha512(self):
        rendered = self.render_template(
            """{% load pipeline %}{% javascript "scripts_sri_sha512" %}"""
        )  # noqa
        hash_ = JinjaTest.get_integrity("scripts_sha512.js", "sha512")
        self.assertEqual(
            (
                '<script type="text/javascript" src="/static/scripts_sha512.js" '
                f'charset="utf-8" integrity="{hash_}"></script>'
            ),
            rendered,
        )  # noqa
        rendered = self.render_template(
            """{% load pipeline %}{% stylesheet "screen_sri_sha512" %}"""
        )  # noqa
        hash_ = JinjaTest.get_integrity("screen_sri_sha512.css", "sha512")
        self.assertEqual(
            (
                f'<link href="/static/screen_sri_sha512.css" rel="stylesheet" '
                f'type="text/css" media="all" integrity="{hash_}" />'
            ),
            rendered,
        )  # noqa
