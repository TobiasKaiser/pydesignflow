"""
File management helper for cell libraries and PDKs.
"""

from pathlib import Path
from dataclasses import dataclass
import re

class FileManagementError(Exception):
    pass

def checkfile(path: Path) -> Path:
    if not path.exists():
        raise FileManagementError(f"Path '{path}' does not exist.")
    if not path.is_file():
        raise FileManagementError(f"'{path}' is not a file.")
    return path

def checkdir(path: Path) -> Path:
    if not path.exists():
        raise FileManagementError(f"Path '{path}' does not exist.")
    if not path.is_dir():
        raise FileManagementError(f"'{path}' is not a directory.")
    return path

@dataclass
class FileCollectionItem:
    path: Path
    attrs: dict[str, object]

    def __iter__(self):
        return iter((self.path, self.attrs))

class FileCollection:
    """
    A collection of files of the same type with different attributes such as voltage, process corner, temperature etc.
    """

    def __init__(self, items: list[FileCollectionItem]=None):
        if items == None:
            items = []
        self.items = items

    def __add__(self, other):
        return FileCollection(self.items + other.items)

    def __len__(self):
        return len(self.items)

    def __getitem__(self, key):
        return self.items[key]

    def __iter__(self):
        return iter(self.items)

    def tag(self, **attrs: dict[str, object]):
        """
        Returns copy of the FileCollection with passed attrs added to all elements.
        """
        ret = FileCollection()
        for i in self.items:
            ret.items.append(FileCollectionItem(i.path, i.attrs | attrs))
        return ret

    def add(self, path: Path, **attrs: dict[str, object]):
        """
        Adds file with given path and attributes to collection. Also ensures file existence via checkfile.
        """
        self.items.append(FileCollectionItem(checkfile(path), attrs))

    def __repr__(self):
        return f"FileCollection:{self.items}"

    def filter(self, missing_key_deselects: bool = False, **filters: dict[str, object]):
        """
        Returns FileCollection with all files that match given filters.
        """
        
        def filter_func(item):
            for key, value in filters.items():
                try:
                    if item.attrs[key] != value:
                        return False
                except KeyError:
                    if missing_key_deselects:
                        return False
            return True
        
        return FileCollection(list(filter(filter_func, self.items)))

    def one(self, missing_key_deselects: bool = False, **filters: dict[str, object]):
        """
        Returns element that matches **filters.

        Raises FileManagementError if **filters are ambiguous (multiple matches) or when no match is found.
        """
        res = self.filter(missing_key_deselects=missing_key_deselects, **filters)
        if len(res) < 1:
            raise FileManagementError(f"No result for FileCollection filters {filters}.")
        elif len(res) > 1:
            raise FileManagementError(f"Ambiguous result for FileCollection filters {filters}.")
        else:
            return res[0].path

    def __call__(self, *args, **kwargs):
        """
        Alias for .one()
        """
        return self.one(*args, **kwargs)

    @classmethod
    def frompattern(cls, dir, pattern, decoder):
        coll = cls()

        for fn in dir.iterdir():
            m = re.match(pattern, fn.name)
            if m:
                attr_str = m.group(1)
                attrs = decoder(attr_str)
                coll.add(fn, **attrs)

        if len(coll) < 1:
            raise FileManagementError("No files matched in FileCollection.frompattern.")

        return coll
