from fsspec.asyn import sync, sync_wrapper
from fsspec.implementations.http import HTTPFile, HTTPFileSystem, HTTPStreamFile


def is_url(url: str):
    return url.startswith("http://") or url.startswith("https://")


def to_url(path: str) -> str:
    if is_url(path):
        return path

    if path.startswith("/http/"):
        path = "http://" + path[6:]

    elif path.startswith("/https/"):
        path = "https://" + path[7:]

    if path[-2:] == "..":
        path = path[:-2]

    return path


class GlobalHTTPFileSystem(HTTPFileSystem):
    def _cat_file(self, url, **kwargs):
        url = to_url(url)
        return super()._cat_file(url, **kwargs)

    cat_file = sync_wrapper(_cat_file)

    async def _info(self, path, _force_file=False, **kwargs):
        if not _force_file and self.isdir(path):
            return {"name": path, "size": None, "type": "directory"}
        url = to_url(path)
        return await super()._info(url, **kwargs)

    info = sync_wrapper(_info)

    def ls(self, path, detail=False, **kwargs):
        if not self.isdir(path):
            raise ValueError("Path is a directory")
        return []

    def isdir(self, path):
        return path == "/" or path[-2:] != ".."

    # modified from fsspec.implementations.http.HTTPFileSystem
    def _open(self, path, **kwargs):
        url = to_url(path)
        return super()._open(url, _force_file=True, **kwargs)

    # fsspec.fuse.run( GlobalHTTPFileSystem(), '/', '/home/manzt/github/fuse/mnt/')
