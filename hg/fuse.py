import multiprocessing as mp
import os
from time import time
from typing import Optional
from urllib.parse import urlparse

import fsspec.fuse
from fsspec.asyn import sync_wrapper
from fsspec.implementations.http import HTTPFileSystem


class GlobalHTTPFileSystem(HTTPFileSystem):
    def _cat_file(self, url, **kwargs):
        url = path_to_url(url)
        return super()._cat_file(url, **kwargs)

    cat_file = sync_wrapper(_cat_file)

    async def _info(self, path, **kwargs):
        if self.isdir(path):
            return direntry(path)
        url = path_to_url(path)
        entry = await super()._info(url, **kwargs)
        # rename name with filesystem name (not url)
        entry["name"] = path
        return entry

    info = sync_wrapper(_info)

    def ls(self, path, detail=False, **kwargs):
        if not self.isdir(path):
            raise NotADirectoryError(path)
        if path != "/":
            return []
        dirs = ["http/", "https/"]
        if detail:
            return [direntry(n) for n in dirs]
        return dirs

    def isdir(self, path):
        return path[-2:] != ".."

    # modified from fsspec.implementations.http.HTTPFileSystem
    def _open(self, path, **kwargs):
        file = super()._open(path, **kwargs)
        # override HTTPFile/HTTPStreamFile url with real url
        file.url = path_to_url(file.path)
        return file


class FuseProcess:
    def __init__(self):
        self._p: Optional[mp.Process] = None
        self._mount_point: Optional[str] = None

    def start(self, mount_point: str):
        # no need to restart
        if self._p and mount_point == self._mount_point:
            return

        self.stop()

        mount_point = mount_point.rstrip("/") + "/"
        assert os.path.isabs(mount_point), "must provide an absolute path"
        assert os.path.isdir(
            mount_point
        ), f"mount directory doesn't exist: {mount_point}"

        self._p = mp.Process(
            target=fsspec.fuse.run,
            args=(GlobalHTTPFileSystem(), "/", mount_point),
            kwargs={"ready_file": True},
            daemon=True,  # TODO: hmm, this doesn't seem to kill the underlying process
        )

        max_iters = 1000
        for i in range(max_iters):

            if os.path.exists(os.path.join(mount_point, ".fuse_ready")):
                break

            if i == max_iters - 1:
                self.stop()
                raise RuntimeError("Failed to setup FUSE")

            time.sleep(0.5)

    def stop(self):
        if self._p:
            self._p.terminate()
            self._p = None

        # TODO: more teardown, fuser

    def path(self, href: str):
        url = urlparse(href)
        return f"/{url.scheme}/{url.netloc}{url.path}.."


def path_to_url(path: str) -> str:
    if path[-2:] != "..":
        raise FileNotFoundError(path)

    path = path[:-2]

    if path.startswith("/http/"):
        path = "http://" + path[6:]

    elif path.startswith("/https/"):
        path = "https://" + path[7:]

    return path


def direntry(name: str):
    return {
        "name": name,
        "size": None,
        "type": "directory",
    }
