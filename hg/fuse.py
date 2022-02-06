from fsspec.asyn import sync_wrapper
from fsspec.implementations.http import HTTPFileSystem


def to_url(path: str) -> str:
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


class GlobalHTTPFileSystem(HTTPFileSystem):
    def _cat_file(self, url, **kwargs):
        url = to_url(url)
        return super()._cat_file(url, **kwargs)

    cat_file = sync_wrapper(_cat_file)

    async def _info(self, path, **kwargs):
        if self.isdir(path):
            return direntry(path)
        url = to_url(path)
        return await super()._info(url, **kwargs)

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
        f = super()._open(path, **kwargs)
        f.url = to_url(f.path)
        return f
