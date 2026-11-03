.. _ref-installation:

============
Installation
============

1. Either check out Pipeline from GitHub_ or to pull a release off PyPI_ ::

       pip install django-pipeline


2. Add 'pipeline' to your ``INSTALLED_APPS`` ::

       INSTALLED_APPS = (
           'pipeline',
       )

3. Use a pipeline storage for static files.

   **For Django < 4.2:**

        STATICFILES_STORAGE = 'pipeline.storage.PipelineManifestStorage'

   **For Django >= 4.2:**

        STORAGES = {
            'default': {
                'BACKEND': 'django.core.files.storage.FileSystemStorage',
            },
            'staticfiles': {
                'BACKEND': 'pipeline.storage.PipelineManifestStorage',
            },
        }

4. Add the ``PipelineFinder`` to ``STATICFILES_FINDERS`` ::

        STATICFILES_FINDERS = (
            'django.contrib.staticfiles.finders.FileSystemFinder',
            'django.contrib.staticfiles.finders.AppDirectoriesFinder',
            'pipeline.finders.PipelineFinder',
        )


.. note::
  You need to use ``Django>=1.11`` to be able to use this version of pipeline.

.. _GitHub: http://github.com/jazzband/django-pipeline
.. _PyPI: http://pypi.python.org/pypi/django-pipeline

Upgrading from 1.3
==================

To upgrade from pipeline 1.3, you will need to follow these steps:

1. Update templates to use the new syntax

    .. code-block:: python

        {# pipeline<1.4 #}
        {% load compressed %}
        {% compressed_js 'group' %}
        {% compressed_css 'group' %}

    .. code-block:: python

        {# pipeline>=1.4 #}
        {% load pipeline %}
        {% javascript 'group' %}
        {% stylesheet 'group' %}

2. Add the ``PipelineFinder`` to ``STATICFILES_FINDERS`` ::

        STATICFILES_FINDERS = (
            'django.contrib.staticfiles.finders.FileSystemFinder',
            'django.contrib.staticfiles.finders.AppDirectoriesFinder',
            'pipeline.finders.PipelineFinder',
        )


Upgrading from 1.5
==================

To upgrade from pipeline 1.5, you will need update all your ``PIPELINE_*``
settings and move them under the new ``PIPELINE`` setting.
See :ref:`ref-configuration`.

Recommendations
===============

Pipeline's default CSS and JS compressor is Yuglify.
Yuglify wraps UglifyJS and cssmin, applying the default YUI configurations to them.
It can be downloaded from: https://github.com/yui/yuglify/.

If you do not install yuglify, make sure to disable the compressor in your settings.
