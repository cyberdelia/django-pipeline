.. _ref-usage:

=====
Usage
=====

Describes how to use Pipeline when it is installed and configured.

Templatetags
============

Pipeline includes two template tags: ``stylesheet`` and ``javascript``,
in a template library called ``pipeline``.

They are used to output the ``<link>`` and ``<script>``-tags for the
specified CSS/JavaScript-groups (as specified in the settings).
The first argument must be the name of the CSS/JavaScript group.

When ``settings.DEBUG`` is set to ``True`` the use of these template tags will
result in a separate tag for each resource in a given group (i.e., the
combined, compressed files will not be used), in order to make local debugging
easy. When ``settings.DEBUG`` is set to ``False`` the opposite is true. You can
override the default behavior by setting ``settings.PIPELINE['PIPELINE_ENABLED']``
manually. When set to ``True`` or ``False`` this enables or disables,
respectively, the usage of the combined, compressed file for each resource
group. This can be useful, if you encounter errors in your compressed code that
don't occur in your uncompressed code and you want to debug them locally.

If you need to change the output of the HTML-tags generated from the templatetags,
this can be done by overriding the templates ``pipeline/css.html`` and ``pipeline/js.html``.

Example
-------

If you have specified the CSS-groups “colors” and “stats” and a JavaScript-group
with the name “scripts”, you would use the following code to output them all ::

   {% load pipeline %}
   {% stylesheet 'colors' %}
   {% stylesheet 'stats' %}
   {% javascript 'scripts' %}


Form Media
==========

Django forms and widgets can specify individual CSS or JavaScript files to
include on a page by defining a ``Form.Media`` class with ``css`` and ``js``
attributes.

Pipeline builds upon this by allowing packages to be listed in
``css_packages`` and ``js_packages``. This is equivalent to manually including
these packages in a page's template using the template tags.

To use these, just have your form or widget's ``Media`` class inherit from
``pipeline.forms.PipelineFormMedia`` and define ``css_packages`` and
``js_packages``. You can also continue to reference individual CSS/JavaScript
files using the original ``css``/``js`` attributes, if needed.

Note that unlike the template tags, you cannot customize the HTML for
referencing these files. The ``pipeline/css.html`` and ``pipeline/js.html``
files will not be used. Django takes care of generating the HTML for form and
widget media.


Example
-------

.. code-block:: python

    from django import forms
    from pipeline.forms import PipelineFormMedia


    class MyForm(forms.Form):
        ...

        class Media(PipelineFormMedia):
            css_packages = {
                'all': ('my-styles',)
            }
            js_packages = ('my-scripts',)
            js = ('https://cdn.example.com/some-script.js',)


Collect static
==============

Pipeline integrates with staticfiles, you just need to configure the static files storage.

.. note::

   ``STATICFILES_STORAGE`` is deprecated in Django 4.2 and removed in Django 5.1.
   For Django 4.2+, use the ``STORAGES`` setting instead.

**For Django < 4.2:**

    STATICFILES_STORAGE = 'pipeline.storage.PipelineStorage'

**For Django >= 4.2:**

    STORAGES = {
        'default': {
            'BACKEND': 'django.core.files.storage.FileSystemStorage',
        },
        'staticfiles': {
            'BACKEND': 'pipeline.storage.PipelineStorage',
        },
    }

Then when you run ``collectstatic`` command, your CSS and your javascripts will be compressed at the same time ::

    $ python manage.py collectstatic

Cache-busting
-------------

Pipeline 1.2+ no longer provides its own cache-busting URL support (using e.g. the ``PIPELINE_VERSIONING`` setting) but uses
Django's built-in staticfiles support for this. To set up cache-busting in conjunction with ``collectstatic`` as above, use:

**For Django < 4.2:**

    STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'

**For Django >= 4.2:**

    STORAGES = {
        'default': {
            'BACKEND': 'django.core.files.storage.FileSystemStorage',
        },
        'staticfiles': {
            'BACKEND': 'pipeline.storage.PipelineCachedStorage',
        },
    }

This will handle cache-busting just as ``staticfiles``'s built-in ``CachedStaticFilesStorage`` does.

Middleware
==========

To enable HTML compression add ``pipeline.middleware.MinifyHTMLMiddleware``,
to your ``MIDDLEWARE_CLASSES`` settings.

Ensure that it comes after any middleware which modifies your HTML, like ``GZipMiddleware`` ::

   MIDDLEWARE_CLASSES = (
      'django.middleware.gzip.GZipMiddleware',
      'pipeline.middleware.MinifyHTMLMiddleware',
   )


Jinja
=====

Pipeline also includes Jinja2 support and is used almost identically to the Django Template tags implementation.
You just need to pass ``pipeline.jinja2.PipelineExtension`` to your Jinja2 environment::


    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'environment': 'myproject.jinja2.environment',
            'extensions': ['pipeline.jinja2.PipelineExtension']
        }
    }


Templates
---------

Unlike the Django template tag implementation the Jinja2 implementation uses different templates, so if you wish to override them please override pipeline/css.jinja and pipeline/js.jinja.
