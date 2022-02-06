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
