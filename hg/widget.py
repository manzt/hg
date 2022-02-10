from typing import Optional
from .api import Viewconf

try:
    import ipywidgets
    from traitlets import Unicode  # type: ignore
except ImportError as e:
    raise ImportError('Install "ipywidgets" to use hg.widget') from e


class HgWidget(ipywidgets.DOMWidget):
    _model_name = Unicode("HgModel").tag(sync=True)
    _model_module = Unicode("hg").tag(sync=True)
    _model_module_version = Unicode("0.0.0").tag(sync=True)

    _view_name = Unicode("HgView").tag(sync=True)
    _view_module = Unicode("hg").tag(sync=True)
    _view_module_version = Unicode("0.0.0").tag(sync=True)

    _viewconf = Unicode("null").tag(sync=True)

    def __init__(self, viewconf: Optional[Viewconf] = None, **kwargs):
        super().__init__(**kwargs)
        if viewconf is not None:
            self._viewconf = viewconf.json()
