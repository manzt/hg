import webbrowser
import urllib.parse

def open_browser(viewconf):
    contents = viewconf._repr_mimebundle_()['text/html']
    encoded = urllib.parse.quote(contents)
    webbrowser.open("data:text/html," + encoded)
    input("Press any key to exit.")


if __name__ == "__main__":
    import hg
    import sys

    ts = hg.cooler(sys.argv[1])
    conf = hg.view(ts.track("heatmap"))
    open_browser(conf)
