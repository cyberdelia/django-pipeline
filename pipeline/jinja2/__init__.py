from jinja2 import nodes, TemplateSyntaxError
from jinja2.ext import Extension

from django.contrib.staticfiles.storage import staticfiles_storage

from ..packager import PackageNotFound
from ..utils import guess_type
from ..templatetags.pipeline import PipelineMixin


class PipelineExtension(PipelineMixin, Extension):
    tags = set(['stylesheet', 'javascript'])

    def parse(self, parser):
        tag = next(parser.stream)

        package_name = parser.parse_expression()
        if not package_name:
            raise TemplateSyntaxError("Bad package name", tag.lineno)

        args = [package_name]
        if tag.value == "stylesheet":
            return nodes.CallBlock(self.call_method('package_css', args), [], [], []).set_lineno(tag.lineno)

        if tag.value == "javascript":
            return nodes.CallBlock(self.call_method('package_js', args), [], [], []).set_lineno(tag.lineno)

        return []

    def package_css(self, package_name, *args, **kwargs):
        try:
            package = self.package_for(package_name, 'css')
        except PackageNotFound:
            return ''  # fail silently, do not return anything if an invalid group is specified
        return self.render_compressed(package, package_name, 'css')

    def render_css(self, package, path):
        template_name = package.template_name or "pipeline/css.jinja"
        context = package.extra_context
        context.update({
            'type': guess_type(path, 'text/css'),
            'url': staticfiles_storage.url(path)
        })
        template = self.environment.get_template(template_name)
        return template.render(context)

    def render_individual_css(self, package, paths, **kwargs):
        tags = [self.render_css(package, path) for path in paths]
        return '\n'.join(tags)

    def package_js(self, package_name, *args, **kwargs):
        try:
            package = self.package_for(package_name, 'js')
        except PackageNotFound:
            return ''  # fail silently, do not return anything if an invalid group is specified
        return self.render_compressed(package, package_name, 'js')

    def render_js(self, package, path):
        template_name = package.template_name or "pipeline/js.jinja"
        context = package.extra_context
        context.update({
            'type': guess_type(path, 'text/javascript'),
            'url': staticfiles_storage.url(path),
            "crossorigin": package.config.get("crossorigin"),
            "integrity": package.get_sri(path),
        })
        template = self.environment.get_template(template_name)
        return template.render(context)

    def render_inline(self, package, js):
        context = package.extra_context
        context.update({
            'source': js
        })
        template = self.environment.get_template("pipeline/inline_js.jinja")
        return template.render(context)

    def render_individual_js(self, package, paths, templates=None):
        tags = [self.render_js(package, js) for js in paths]
        if templates:
            tags.append(self.render_inline(package, templates))
        return '\n'.join(tags)
