define(["@jupyter-widgets/base"], function (base) {
	// hack to let us use an ES module
	return import("./lib.js").then(lib => {
		// export hglib globally... for plugins?
		window.hglib = lib.hglib;

		class HgModel extends base.DOMWidgetModel {}

		class HgView extends base.DOMWidgetView {

			render() {
				this.el.textContent = "hello, world!";
			}

		}

		return { HgModel, HgView };
	})
});
