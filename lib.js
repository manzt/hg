function loadCss(url) {
	let link = document.createElement("link");
	link.type = "text/css";
	link.rel = "stylesheet";
	link.href = url;
	document.getElementsByTagName("head")[0].appendChild(link);
}

loadCss("https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css");
loadCss("http://unpkg.com/higlass@1.11/dist/hglib.css");

export * as hglib from "higlass";
