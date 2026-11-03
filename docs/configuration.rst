.. _ref-configuration:

=============
Configuration
=============


Configuration and list of available settings for Pipeline. Pipeline settings are namespaced in a PIPELINE dictionary in your project settings, e.g.: ::

  PIPELINE = {
      'PIPELINE_ENABLED': True,
      'JAVASCRIPT': {
          'stats': {
              'source_filenames': (
                'js/jquery.js',
                'js/d3.js',
                'js/collections/*.js',
                'js/application.js',
              ),
              'output_filename': 'js/stats.js',
          }
      }
  }


Specifying files
================

You specify groups of files to be compressed in your settings. You can use glob
syntax to select multiples files.

The basic syntax for specifying CSS/JavaScript groups files is ::

  PIPELINE = {
      'STYLESHEETS': {
          'colors': {
              'source_filenames': (
                'css/core.css',
                'css/colors/*.css',
                'css/layers.css'
              ),
              'output_filename': 'css/colors.css',
              'extra_context': {
                  'media': 'screen,projection',
              },
          },
      },
      'JAVASCRIPT': {
          'stats': {
              'source_filenames': (
                'js/jquery.js',
                'js/d3.js',
                'js/collections/*.js',
                'js/application.js',
              ),
              'output_filename': 'js/stats.js',
          }
      }
  }

Group options
-------------

``source_filenames``
....................

**Required**

Is a tuple with the source files to be compressed.
The files are concatenated in the order specified in the tuple.


``output_filename``
...................

**Required**

Is the filename of the (to be) compressed file.

``variant``
...........

**Optional**

Is the variant you want to apply to your CSS. This allow you to embed images
and fonts in CSS with data-URI.
Allowed values are : ``None`` and ``datauri``.

Defaults to ``None``.

``template_name``
.................

**Optional**

Name of the template used to render ``<script>`` for js package or ``<link>`` for css package.

Defaults to ``None``.

``extra_context``
.................

**Optional**

Is a dictionary of values to add to the template context,
when generating the HTML for the HTML-tags with the templatetags.

For CSS, if you do not specify ``extra_context``/``media``, the default media in
the ``<link>`` output will be ``media="all"``.

For JS, the default templates support the ``async`` and ``defer`` tag attributes which are controlled via ``extra_context``: ::

  'extra_context': {
      'async': True,
  },

``manifest``
............

**Optional**

Indicate if you want this group to appear in your cache manifest.

Defaults to ``True``.

``compiler_options``
....................

**Optional**

A dictionary passed to compiler's ``compile_file`` method as kwargs. None of default compilers use it currently. It's to be used by custom compilers in case they need some special parameters.

Defaults to ``{}``.


Other settings
--------------

``PIPELINE_ENABLED``
....................

``True`` if assets should be compressed, ``False`` if not.

Defaults to ``not settings.DEBUG``.

``PIPELINE_COLLECTOR_ENABLED``
..............................

``True`` if assets should be collected in develop , ``False`` if not.

Defaults to ``True``

.. note::

  This only applies when ``PIPELINE_ENABLED`` is ``False``.

``SHOW_ERRORS_INLINE``
......................

``True`` if errors compiling CSS/JavaScript files should be shown inline at
the top of the browser window, or ``False`` if they should trigger exceptions
(the older behavior).

This only applies when compiling through the ``{% stylesheet %}`` or
``{% javascript %}`` template tags. It won't impact ``collectstatic``.

Defaults to ``settings.DEBUG``.

``CSS_COMPRESSOR``
..................

Compressor class to be applied to CSS files.

If empty or ``None``, CSS files won't be compressed.

Defaults to ``'pipeline.compressors.yuglify.YuglifyCompressor'``.

``JS_COMPRESSOR``
.................

Compressor class to be applied to JavaScript files.

If empty or ``None``, JavaScript files won't be compressed.

Defaults to ``'pipeline.compressors.yuglify.YuglifyCompressor'``

.. note::

  Please note that in order to use Yuglify compressor, you need to install Yuglify (see :doc:`installation` for more details).

``HTML_COMPRESSOR``
...................

Compressor class to be applied to HTML responses.

If empty or ``None``, HTML responses won't be compressed.

Defaults to ``'pipeline.compressors.djangohtml.DjangoHtmlCompressor'``

``TEMPLATE_NAMESPACE``
......................

Object name where all of your compiled templates will be added, from within your browser.
To access them with your own JavaScript namespace, change it to the object of your choice.

Defaults to ``"window.JST"``


``TEMPLATE_EXT``
................

The extension for which Pipeline will consider the file as a Javascript template.
To use a different extension, like ``.mustache``, set this settings to ``.mustache``.

Defaults to ``".jst"``

``TEMPLATE_FUNC``
.................

JavaScript function that compiles your JavaScript templates.
Pipeline doesn't bundle a javascript template library, but the default
setting is to use the
`underscore <http://documentcloud.github.com/underscore/>`_ template function.

Defaults to ``"_.template"``

``TEMPLATE_SEPARATOR``
......................

Character chain used by Pipeline as replacement for directory separator.

Defaults to ``"_"``


``MIMETYPES``
.............

Tuple that match file extension with their corresponding mimetypes.

Defaults to ::

  (
    ('text/coffeescript', '.coffee'),
    ('text/less', '.less'),
    ('text/javascript', '.js'),
    ('text/x-sass', '.sass'),
    ('text/x-scss', '.scss')
  )

.. warning::
  If you support Internet Explorer version 8 and below, you should
  declare javascript files as ``text/javascript``.


Embedding fonts and images
==========================

You can embed fonts and images directly in your compiled css, using Data-URI in
modern browsers.

To do so, setup variant group options to the method you wish to use : ::

  'STYLESHEETS' = {
      'master': {
          'source_filenames': (
            'css/core.css',
            'css/button/*.css',
          ),
          'output_filename': 'css/master.css',
          'variant': 'datauri',
      },
  }

Images and fonts are embedded following these rules :

- If asset is under **32 kilobytes** to avoid rendering delay or not rendering
  at all in Internet Explorer 8.
- If asset path contains a directory named "**embed**".

Overriding embedding settings
-----------------------------

You can override these rules using the following settings:

``EMBED_MAX_IMAGE_SIZE``
........................

Setting that controls the maximum image size (in bytes) to embed in CSS using Data-URIs.
Internet Explorer 8 has issues with assets over 32 kilobytes.

Defaults to ``32700``

``EMBED_PATH``
..............

Setting the directory that an asset needs to be in so that it is embedded

Defaults to ``r'[/]?embed/'``


Rewriting CSS urls
==================

If the source CSS contains relative URLs (i.e. relative to current file),
those URLs will be converted to full relative path.


Wrapped javascript output
=========================

All javascript output is wrapped in an anonymous function : ::

  (function(){
    //JS output...
  })();

This safety wrapper, make it difficult to pollute the global namespace by accident and improve performance.

You can override this behavior by setting ``DISABLE_WRAPPER`` to ``True``. If you want to use your own wrapper, change
the ``JS_WRAPPER`` setting. For example: ::

  JS_WRAPPER = "(function(){stuff();%s})();"
