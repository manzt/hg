import logging
import multiprocessing as mp
import os
import pathlib
import time
from errno import ENOENT
from typing import List, Optional, Union
from typing_extensions import Literal
from urllib.parse import urlparse

from fuse import FUSE, FuseOSError, LoggingMixIn, Operations
from simple_httpfs import HttpFs

FsName = Literal["http", "https", "ftp"]

logger = logging.getLogger("hg.fuse")


class MultiHttpFs(LoggingMixIn, Operations):
    def __init__(self, schemas: List[FsName], **kwargs):
        logger.info("Starting FUSE at /")
        self.fs = {schema: HttpFs(schema, **kwargs) for schema in schemas}

    def _deref(self, path: str):
        root, *rest = path.lstrip("/").split("/")
        if len(rest) == 1 and rest[0] == "":
            # path == "/http/", "/https/", "/ftp/"
            raise FuseOSError(ENOENT)
        try:
            fs = self.fs[root]
        except KeyError:
            raise FuseOSError(ENOENT)
        return fs, "/" + "/".join(rest)

    def getattr(self, path, fh=None):
        logger.debug("getattr %s", path)
        if path == "/":
            first = next(iter(self.fs.values()))
            return first.getattr("/", fh)
        fs, path = self._deref(path)
        return fs.getattr(path, fh)

    def read(self, path, size, offset, fh):
        logger.debug("read %s", (path, size, offset))
        fs, path = self._deref(path)
        return fs.read(path, size, offset, fh)

    def readdir(self, path, fh):
        logger.debug("readdir %s", path)
        if path[-2:] == "..":
            raise NotADirectoryError(path)
        files = list(self.fs) if path == "/" else []
        return [".", ".."] + files

    def destroy(self, path):
        for fs in self.fs.values():
            fs.destroy(path)


def run(mount_point: str, disk_cache_dir: str):
    fs = MultiHttpFs(
        ["http", "https"],
        disk_cache_size=2**25,
        disk_cache_dir=disk_cache_dir,
        lru_capacity=400,
    )
    FUSE(fs, mount_point, foreground=True)


class FuseProcess:
    def __init__(self):
        self._fuse_process: Optional[mp.Process] = None
        self._tmp_dir: Optional[pathlib.Path] = None

    def start(self, tmp_dir: Union[str, pathlib.Path]):
        # no need to restart
        tmp_dir = pathlib.Path(tmp_dir).absolute()
        if self._fuse_process and tmp_dir == self._tmp_dir:
            return

        self.stop()

        assert tmp_dir.is_dir(), f"mount dir doesn't exist: {tmp_dir}"

        mount_point = tmp_dir / "mnt"
        disk_cache_dir = tmp_dir / "dc"

        if not mount_point.exists():
            mount_point.mkdir()

        if not disk_cache_dir.exists():
            disk_cache_dir.mkdir()

        args = (str(mount_point) + "/", str(disk_cache_dir) + "/")
        self._fuse_process = mp.Process(target=run, args=args, daemon=True)
        self._fuse_process.start()

        max_iters = 10
        for i in range(max_iters):

            # wait until http is mounted
            if os.path.exists(os.path.join(mount_point, "http")):
                break

            if i == max_iters - 1:
                self.stop()
                raise RuntimeError("Failed to setup FUSE")

            time.sleep(0.5)

        self._mount_point = mount_point

    def stop(self):
        if self._fuse_process:
            self._fuse_process.terminate()
            self._fuse_process = None

        # TODO: more teardown?

    def path(self, href: str):
        if self._mount_point is None:
            raise RuntimeError("FUSE processes not started")
        url = urlparse(href)
        return str(self._mount_point / f"{url.scheme}/{url.netloc}{url.path}..")
