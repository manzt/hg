import tempfile
import webbrowser

def open_browser(viewconf):
    contents = viewconf._repr_mimebundle_()['text/html']
    tmp = tempfile.NamedTemporaryFile(suffix=".html")
    with open(tmp.name, "w") as f:
        f.write(contents)
    webbrowser.open("file://" + tmp.name)
    input("Press any key to exit.")
    tmp.flush()


def main():
    import hg
    import sys

    ts = hg.cooler(sys.argv[1])
    conf = hg.view(ts.track("heatmap"))
    open_browser(conf)



if __name__ == "__main__":
    main()

