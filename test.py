import logging

from rich import print
from rich.logging import RichHandler

logger = logging.getLogger("fsspec.fuse")
logger.setLevel(logging.DEBUG)

import hg.fuse

if __name__ == "__main__":

    logger.addHandler(RichHandler())
    url = "http://example.com"
    mapped = f"/http/{url[7:]}.."
    # print(f"{url=}, {mapped=}")
    # HTTPFileSystem().cat_file(url)

    # fsspec.fuse.run( GlobalHTTPFileSystem(), '/', '/home/manzt/github/fuse/mnt/')
    fs = hg.fuse.GlobalHTTPFileSystem()
    print(
        fs.info("/http/example.com")
    )
    print(
        fs.info("/http/example.com..")
    )
    print(
        fs.cat("/http/example.com..")
    )
    print(fs.ls("/", True))

    with fs.open("/http/example.com..") as f:
        print(f)
