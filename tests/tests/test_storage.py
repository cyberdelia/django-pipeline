from __future__ import unicode_literals

from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import override_settings
from django.conf import settings
from django.contrib.staticfiles import finders

from pipeline.storage import PipelineStorage

from tests.tests.test_compiler import DummyCompiler
from tests.utils import pipeline_settings

try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO


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


class DummyCSSCompiler(DummyCompiler):
    """ Handles css files """
    output_extension = 'css'

    def match_file(self, path):
        return path.endswith('.css')


class StorageTest(TestCase):
    def tearDown(self):
        staticfiles_storage._setup()

    def test_post_process_dry_run(self):
        with pipeline_settings(JS_COMPRESSOR=None, CSS_COMPRESSOR=None):
            processed_files = PipelineStorage().post_process({}, True)
            self.assertEqual(list(processed_files), [])

    def test_post_process(self):
        storage = PipelineStorage()
        with pipeline_settings(JS_COMPRESSOR=None, CSS_COMPRESSOR=None):
            processed_files = storage.post_process({})
            self.assertTrue(('screen.css', 'screen.css', True) in processed_files)
            self.assertTrue(('scripts.js', 'scripts.js', True) in processed_files)

    def test_post_process_no_path(self):
        """
        Test post_process with a storage that doesn't implement the path method.
        """
        with override_settings(STATICFILES_STORAGE='tests.tests.test_storage.PipelineNoPathStorage'):
            with pipeline_settings(JS_COMPRESSOR=None, CSS_COMPRESSOR=None, COMPILERS=['tests.tests.test_storage.DummyCSSCompiler']):
                staticfiles_storage._setup()
                try:
                    call_command('collectstatic', verbosity=0, interactive=False)
                except NotImplementedError:
                    self.fail('Received an error running collectstatic')

    # def test_find_storage(self):
    #     try:
    #         storage = PipelineFinderStorage()
    #         storage.find_storage('app.css')
    #     except ValueError:
    #         self.fail()

    def test_nonexistent_file_pipeline_finder(self):
        CUSTOM_FINDERS = settings.STATICFILES_FINDERS + ('pipeline.finders.PipelineFinder',)
        with self.settings(STATICFILES_FINDERS=CUSTOM_FINDERS):
            path = finders.find('nothing.css')
            self.assertIsNone(path)

    def test_nonexistent_file_cached_finder(self):
        CUSTOM_FINDERS = settings.STATICFILES_FINDERS + ('pipeline.finders.CachedFileFinder',)
        with self.settings(STATICFILES_FINDERS=CUSTOM_FINDERS):
            path = finders.find('nothing.css')
            self.assertIsNone(path)

    def test_nonexistent_double_extension_file_pipeline_finder(self):
        CUSTOM_FINDERS = settings.STATICFILES_FINDERS + ('pipeline.finders.PipelineFinder',)
        with self.settings(STATICFILES_FINDERS=CUSTOM_FINDERS):
            path = finders.find('app.css.map')
            self.assertIsNone(path)

    def test_nonexistent_double_extension_file_cached_finder(self):
        CUSTOM_FINDERS = settings.STATICFILES_FINDERS + ('pipeline.finders.CachedFileFinder',)
        with self.settings(STATICFILES_FINDERS=CUSTOM_FINDERS):
            path = finders.find('app.css.map')
            self.assertIsNone(path)
