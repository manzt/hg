from fsspec.asyn import sync_wrapper
from fsspec.implementations.http import HTTPFileSystem


def is_url(url: str):
    return url.startswith("http://") or url.startswith("https://")


def to_url(path: str) -> str:
    if is_url(path):
        return path

    if path.startswith("/http/"):
        path = "http://" + path[6:]

    elif path.startswith("/https/"):
        path = "https://" + path[7:]

    assert path[-2:] == ".."

    return path[:-2]


class GlobalHTTPFileSystem(HTTPFileSystem):
    def _cat_file(self, url, **kwargs):
        url = to_url(url)
        return super()._cat_file(url, **kwargs)

    cat_file = sync_wrapper(_cat_file)

    async def _info(self, path, _path_normalized=False, **kwargs):
        if not _path_normalized:
            if self.isdir(path):
                return {"name": path, "size": None, "type": "directory"}
            url = to_url(path)
        else:
            url = path
        return await super()._info(url, **kwargs)

    info = sync_wrapper(_info)

    def ls(self, path, detail=False, **kwargs):
        if not self.isdir(path):
            raise ValueError("Path is a directory")
        if path != "/":
            return []
        out = ["http/", "https/"]
        if detail:
            return [{"name": u, "size": None, "type": "directory"} for u in out]
        return out

    def isdir(self, path):
        return path[-2:] != ".."

    # modified from fsspec.implementations.http.HTTPFileSystem
    def _open(self, path, **kwargs):
        url = to_url(path)
        return super()._open(url, _path_normalized=True, **kwargs)

    # fsspec.fuse.run( GlobalHTTPFileSystem(), '/', '/home/manzt/github/fuse/mnt/')
