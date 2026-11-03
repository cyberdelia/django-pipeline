from io import StringIO

import django
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import modify_settings, override_settings

from pipeline.collector import default_collector
from pipeline.storage import PipelineStorage
from tests.tests.test_compiler import DummyCompiler
from tests.utils import pipeline_settings


class PipelineNoPathStorage(PipelineStorage):
    """Storage without an implemented path method"""

    def path(self, *args):
        raise NotImplementedError()

    def delete(self, *args):
        return

    def exists(self, *args):
        return True

    def save(self, *args):
        return

    def open(self, *args):
        return StringIO()

    def listdir(self, *args):
        return []


class DummyCSSCompiler(DummyCompiler):
    """Handles css files"""

    output_extension = "css"

    def match_file(self, path):
        return path.endswith(".css")


class StorageTest(TestCase):
    def tearDown(self):
        staticfiles_storage._setup()

    @pipeline_settings(JS_COMPRESSOR=None, CSS_COMPRESSOR=None)
    def test_post_process_dry_run(self):
        default_collector.collect()
        processed_files = PipelineStorage().post_process({}, True)
        self.assertEqual(list(processed_files), [])

    @pipeline_settings(
        JS_COMPRESSOR=None,
        CSS_COMPRESSOR=None,
        COMPILERS=["tests.tests.test_storage.DummyCSSCompiler"],
    )
    def test_post_process(self):
        default_collector.collect()
        storage = PipelineStorage()
        processed_files = storage.post_process({})
        self.assertTrue(("screen.css", "screen.css", True) in processed_files)
        self.assertTrue(("scripts.js", "scripts.js", True) in processed_files)

    @override_settings(
        STATICFILES_STORAGE="tests.tests.test_storage.PipelineNoPathStorage",
    )
    @pipeline_settings(
        JS_COMPRESSOR=None,
        CSS_COMPRESSOR=None,
        COMPILERS=["tests.tests.test_storage.DummyCSSCompiler"],
    )
    def test_post_process_no_path(self):
        """
        Test post_process with a storage that doesn't implement the path method.
        """
        staticfiles_storage._setup()
        try:
            call_command("collectstatic", verbosity=0, interactive=False)
        except NotImplementedError:
            self.fail("Received an error running collectstatic")

    @modify_settings(STATICFILES_FINDERS={"append": "pipeline.finders.PipelineFinder"})
    def test_nonexistent_file_pipeline_finder(self):
        path = finders.find("nothing.css")
        self.assertIsNone(path)

    @modify_settings(STATICFILES_FINDERS={"append": "pipeline.finders.PipelineFinder"})
    def test_nonexistent_file_pipeline_finder_find_all(self):
        if django.__version__ < "5.2":
            self.skipTest("Only applicable to Django 5.2 and up")

        path = finders.find("nothing.css", find_all=True)
        self.assertIsNotNone(path)
        self.assertEqual([], path)

    @modify_settings(STATICFILES_FINDERS={"append": "pipeline.finders.PipelineFinder"})
    def test_nonexistent_file_pipeline_finder_all(self):
        if django.__version__ >= "6.0":
            self.skipTest("Only applicable to versions of Django before 6.0")

        path = finders.find("nothing.css", all=True)
        self.assertIsNotNone(path)
        self.assertEqual([], path)

    @modify_settings(
        STATICFILES_FINDERS={"append": "pipeline.finders.CachedFileFinder"}
    )
    def test_nonexistent_file_cached_finder(self):
        path = finders.find("nothing.css")
        self.assertIsNone(path)

    @modify_settings(STATICFILES_FINDERS={"append": "pipeline.finders.PipelineFinder"})
    def test_nonexistent_double_extension_file_pipeline_finder(self):
        path = finders.find("app.css.map")
        self.assertIsNone(path)

    @modify_settings(
        STATICFILES_FINDERS={"append": "pipeline.finders.CachedFileFinder"}
    )
    def test_nonexistent_double_extension_file_cached_finder(self):
        path = finders.find("app.css.map")
        self.assertIsNone(path)

    @modify_settings(STATICFILES_FINDERS={"append": "pipeline.finders.ManifestFinder"})
    def test_manifest_finder_finds_stylesheet(self):
        path = finders.find("screen.css")
        self.assertIsNotNone(path)

        path = finders.find("screen.scss")
        self.assertIsNone(path)

    @modify_settings(STATICFILES_FINDERS={"append": "pipeline.finders.ManifestFinder"})
    def test_manifest_finder_finds_all_stylesheet(self):
        if django.__version__ < "5.2":
            paths = finders.find("screen.css", all=True)
        else:
            paths = finders.find("screen.css", find_all=True)
        self.assertIsNotNone(paths)
        self.assertEqual(1, len(paths))

        if django.__version__ < "5.2":
            paths = finders.find("screen.scss", all=True)
        else:
            paths = finders.find("screen.scss", find_all=True)
        self.assertIsNotNone(paths)
        self.assertEqual([], paths)
