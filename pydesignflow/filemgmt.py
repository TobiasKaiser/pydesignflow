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

class FileCollection:
    """
    A collection of files of the same type with different attributes such as voltage, process corner, temperature etc.
    """

    def __init__(self):
        self.items = []

    def add(self, path: Path, **attrs: dict[str, object]):
        """
        Adds file with given path and attributes to collection. Also ensures file existence via checkfile.
        """
        self.items.append(FileCollectionItem(checkfile(path), attrs))

    def __repr__(self):
        return f"FileCollection:{self.items}"

    def all(self, **filters: dict[str, object]):
        """
        Returns iterator over all elements that match **filters.
        """
        for itm in self.items:
            selected = True
            for key, value in filters.items():
                try:
                    if itm.attrs[key] != value:
                        selected = False
                except KeyError:
                    selected = False
            if selected:
                yield itm.path

    def one(self, filter_dict={}, **filters: dict[str, object]):
        """
        Returns element that matches **filters. Alternatively, a filter dict can be passed as single argument.

        Raises FileManagementError if **filters are ambiguous (multiple matches) or when no match is found.
        """
        filters |= filter_dict
        res = list(self.all(**filters))
        if len(res) < 1:
            raise FileManagementError(f"No result for FileCollection filters {filters}.")
        elif len(res) > 1:
            raise FileManagementError(f"Ambiguous result for FileCollection filters {filters}.")
        else:
            return res[0]

    def __call__(self, *args, **filters):
        """
        Alias for .one()
        """
        return self.one(*args, **filters)

    def __len__(self):
        return len(self.items)

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
