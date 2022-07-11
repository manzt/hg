import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import jinja2

HTML_TEMPLATE = jinja2.Template(
    """
<!DOCTYPE html>
<html>
    <head>
        <link rel="stylesheet" href="{{ css_url }}">
    </head>
    <body>
        <div id="{{ output_div }}"></div>
    </body>
    {% for plugin_url in plugin_urls %}
        <script src="{{ plugin_url }}"></script>
    {% endfor %}
    <script type="module">
        import hglib from "{{ js_url }}";
        let el = document.getElementById('{{ output_div }}');
        lef conf =  JSON.parse({{ spec }});
        hglib.viewer(el, conf);
    </script>
</html>
"""
)


def spec_to_html(
    spec: Dict[str, Any],
    higlass_version: str = "1.11",
    react_version: str = "17",
    pixijs_version: str = "6",
    output_div: str = "vis",
    json_kwds: Optional[Dict[str, Any]] = None,
    plugin_urls: Optional[List[str]] = None,
):
    json_kwds = json_kwds or {}
    plugin_urls = plugin_urls or []

    base = f"https://esm.sh/higlass@{higlass_version}"
    js_url = f"{base}?deps=react@{react_version},react-dom@{react_version},pixi.js@{pixijs_version}"
    css_url = f"{base}/dist/hglib.css"

    return HTML_TEMPLATE.render(
        spec=json.dumps(spec, **json_kwds),
        js_url=js_url,
        css_url=css_url,
        output_div=output_div,
        plugin_urls=plugin_urls,
    )


class BaseRenderer:
    def __init__(self, output_div: str = "jupyter-hg-{}", **kwargs):
        self._output_div = output_div
        self.kwargs = kwargs

    @property
    def output_div(self):
        return self._output_div.format(uuid.uuid4().hex)

    def __call__(self, spec, **metadata):
        raise NotImplementedError()


class HTMLRenderer(BaseRenderer):
    def __call__(self, spec, **metadata):
        kwargs = self.kwargs.copy()
        kwargs.update(metadata)
        html = spec_to_html(spec=spec, output_div=self.output_div, **kwargs)
        return {"text/html": html}


@dataclass
class RendererRegistry:
    renderers: Dict[str, BaseRenderer] = field(default_factory=dict)
    active: Optional[str] = None

    def register(self, name: str, renderer: BaseRenderer):
        self.renderers[name] = renderer

    def enable(self, name: str):
        assert name in self.renderers
        self.active = name

    def get(self):
        assert isinstance(self.active, str) and self.active in self.renderers
        return self.renderers[self.active]


html_renderer = HTMLRenderer()

renderers = RendererRegistry()
renderers.register("default", html_renderer)
renderers.register("html", html_renderer)
renderers.register("colab", html_renderer)
renderers.register("kaggle", html_renderer)
renderers.register("zeppelin", html_renderer)
renderers.enable("default")
