import glob
import os
import shutil

from django.utils import version


def local_path(path):
    return os.path.join(os.path.dirname(__file__), path)


DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "TEST_NAME": ":memory:"}
}

DEBUG = False

SITE_ID = 1

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sites",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "django.contrib.auth",
    "django.contrib.admin",
    "pipeline",
    "tests.tests",
]


ROOT_URLCONF = "tests.urls"

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
]

MEDIA_URL = "/media/"

MEDIA_ROOT = local_path("media")

django_version = version.get_complete_version()
if django_version >= (4, 2):

    STORAGES = {
        "default": {
            "BACKEND": "pipeline.storage.PipelineStorage",
        },
        "staticfiles": {
            "BACKEND": "pipeline.storage.PipelineStorage",
        },
    }
else:
    STATICFILES_STORAGE = "pipeline.storage.PipelineStorage"
STATIC_ROOT = local_path("static/")
STATIC_URL = "/static/"
STATICFILES_DIRS = (("pipeline", local_path("assets/")),)
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "pipeline.finders.PipelineFinder",
)

SECRET_KEY = "django-pipeline"

PIPELINE = {
    "PIPELINE_ENABLED": True,
    "JS_COMPRESSOR": None,
    "CSS_COMPRESSOR": None,
    "STYLESHEETS": {
        "screen": {
            "source_filenames": (
                "pipeline/css/first.css",
                "pipeline/css/second.css",
                "pipeline/css/urls.css",
            ),
            "output_filename": "screen.css",
        },
        "screen_media": {
            "source_filenames": (
                "pipeline/css/first.css",
                "pipeline/css/second.css",
                "pipeline/css/urls.css",
            ),
            "output_filename": "screen_media.css",
            "extra_context": {
                "media": "screen and (min-width:500px)",
            },
        },
        "screen_title": {
            "source_filenames": (
                "pipeline/css/first.css",
                "pipeline/css/second.css",
                "pipeline/css/urls.css",
            ),
            "output_filename": "screen_title.css",
            "extra_context": {
                "title": "Default Style",
            },
        },
        "screen_crossorigin": {
            "source_filenames": (
                "pipeline/css/first.css",
                "pipeline/css/second.css",
                "pipeline/css/urls.css",
            ),
            "output_filename": "screen_crossorigin.css",
            "crossorigin": "anonymous",
        },
        "screen_sri_sha256": {
            "source_filenames": (
                "pipeline/css/first.css",
                "pipeline/css/second.css",
                "pipeline/css/urls.css",
            ),
            "output_filename": "screen_sri_sha256.css",
            "integrity": "sha256",
        },
        "screen_sri_sha384": {
            "source_filenames": (
                "pipeline/css/first.css",
                "pipeline/css/second.css",
                "pipeline/css/urls.css",
            ),
            "output_filename": "screen_sri_sha384.css",
            "integrity": "sha384",
        },
        "screen_sri_sha512": {
            "source_filenames": (
                "pipeline/css/first.css",
                "pipeline/css/second.css",
                "pipeline/css/urls.css",
            ),
            "output_filename": "screen_sri_sha512.css",
            "integrity": "sha512",
        },
    },
    "JAVASCRIPT": {
        "scripts": {
            "source_filenames": (
                "pipeline/js/first.js",
                "pipeline/js/second.js",
                "pipeline/js/application.js",
                "pipeline/templates/**/*.jst",
            ),
            "output_filename": "scripts.js",
        },
        "scripts_async": {
            "source_filenames": (
                "pipeline/js/first.js",
                "pipeline/js/second.js",
                "pipeline/js/application.js",
                "pipeline/templates/**/*.jst",
            ),
            "output_filename": "scripts_async.js",
            "extra_context": {
                "async": True,
            },
        },
        "scripts_defer": {
            "source_filenames": (
                "pipeline/js/first.js",
                "pipeline/js/second.js",
                "pipeline/js/application.js",
                "pipeline/templates/**/*.jst",
            ),
            "output_filename": "scripts_defer.js",
            "extra_context": {
                "defer": True,
            },
        },
        "scripts_async_defer": {
            "source_filenames": (
                "pipeline/js/first.js",
                "pipeline/js/second.js",
                "pipeline/js/application.js",
                "pipeline/templates/**/*.jst",
            ),
            "output_filename": "scripts_async_defer.js",
            "extra_context": {
                "async": True,
                "defer": True,
            },
        },
        "scripts_crossorigin": {
            "source_filenames": (
                "pipeline/js/first.js",
                "pipeline/js/second.js",
                "pipeline/js/application.js",
                "pipeline/templates/**/*.jst",
            ),
            "output_filename": "scripts_crossorigin.js",
            "crossorigin": "anonymous",
        },
        "scripts_sri_sha256": {
            "source_filenames": (
                "pipeline/js/first.js",
                "pipeline/js/second.js",
                "pipeline/js/application.js",
                "pipeline/templates/**/*.jst",
            ),
            "output_filename": "scripts_sha256.js",
            "integrity": "sha256",
        },
        "scripts_sri_sha384": {
            "source_filenames": (
                "pipeline/js/first.js",
                "pipeline/js/second.js",
                "pipeline/js/application.js",
                "pipeline/templates/**/*.jst",
            ),
            "output_filename": "scripts_sha384.js",
            "integrity": "sha384",
        },
        "scripts_sri_sha512": {
            "source_filenames": (
                "pipeline/js/first.js",
                "pipeline/js/second.js",
                "pipeline/js/application.js",
                "pipeline/templates/**/*.jst",
            ),
            "output_filename": "scripts_sha512.js",
            "integrity": "sha512",
        },
    },
}

NODE_MODULES_PATH = local_path("../node_modules")
NODE_BIN_PATH = os.path.join(NODE_MODULES_PATH, ".bin")
NODE_EXE_PATH = shutil.which("node")
JAVA_EXE_PATH = shutil.which("java")
CSSTIDY_EXE_PATH = shutil.which("csstidy")
HAS_NODE = bool(NODE_EXE_PATH)
HAS_JAVA = bool(JAVA_EXE_PATH)
HAS_CSSTIDY = bool(CSSTIDY_EXE_PATH)

if HAS_NODE:

    def node_exe_path(command):
        exe_ext = ".cmd" if os.name == "nt" else ""
        return os.path.join(NODE_BIN_PATH, "{}{}".format(command, exe_ext))

    PIPELINE.update(
        {
            "SASS_BINARY": node_exe_path("sass"),
            "COFFEE_SCRIPT_BINARY": node_exe_path("coffee"),
            "COFFEE_SCRIPT_ARGUMENTS": ["--no-header"],
            "LESS_BINARY": node_exe_path("lessc"),
            "BABEL_BINARY": node_exe_path("babel"),
            "BABEL_ARGUMENTS": ["--presets", "es2015"],
            "STYLUS_BINARY": node_exe_path("stylus"),
            "LIVE_SCRIPT_BINARY": node_exe_path("lsc"),
            "LIVE_SCRIPT_ARGUMENTS": ["--no-header"],
            "YUGLIFY_BINARY": node_exe_path("yuglify"),
            "UGLIFYJS_BINARY": node_exe_path("uglifyjs"),
            "TERSER_BINARY": node_exe_path("terser"),
            "CSSMIN_BINARY": node_exe_path("cssmin"),
            "TYPE_SCRIPT_BINARY": node_exe_path("tsc"),
        }
    )

if HAS_NODE and HAS_JAVA:
    PIPELINE.update(
        {
            "CLOSURE_BINARY": [
                JAVA_EXE_PATH,
                "-jar",
                os.path.join(
                    NODE_MODULES_PATH,
                    "google-closure-compiler-java",
                    "compiler.jar",
                ),
            ],
            "YUI_BINARY": [
                JAVA_EXE_PATH,
                "-jar",
                glob.glob(
                    os.path.join(NODE_MODULES_PATH, "yuicompressor", "build", "*.jar")
                )[0],
            ],
        }
    )

if HAS_CSSTIDY:
    PIPELINE.update({"CSSTIDY_BINARY": CSSTIDY_EXE_PATH})

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "DIRS": [local_path("templates")],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    },
    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "APP_DIRS": True,
        "DIRS": [local_path("templates")],
        "OPTIONS": {"extensions": ["pipeline.jinja2.PipelineExtension"]},
    },
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "pipeline.templatetags.pipeline": {
            "handlers": ["console"],
            "level": "ERROR",
        },
    },
}
