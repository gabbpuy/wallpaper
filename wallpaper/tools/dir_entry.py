from dataclasses import dataclass
import os

ImageExtensions = {'.png', '.jpg', '.jpeg', '.gif', '.fli', '.flc', '.fpx', '.gbr', '.gd', '.ico', '.im', '.pcd',
                   '.pcx', '.ppm', '.psd', '.sgi', '.tga', '.tiff', '.wal', '.xbm', '.xpm', '.bmp'}


@dataclass
class DirEntry:
    path: str
    _files: list[str] | None = None
    stat: float | None = None

    @property
    def files(self) -> list[str]:
        """
        Delay loading of files until we care
        """
        ops = os.path.splitext
        opj = os.path.join
        if self._files is None:
            root, _dirs, files = next(os.walk(self.path))
            self._files = [opj(root, f) for f in files if ops(f)[1] in ImageExtensions]

        return self._files

    def __eq__(self, other) -> bool:
        return self.path == other.path and self.stat == other.stat
