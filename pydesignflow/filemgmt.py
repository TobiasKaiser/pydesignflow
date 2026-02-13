# SPDX-FileCopyrightText: 2024 Tobias Kaiser <mail@tb-kaiser.de>
# SPDX-License-Identifier: Apache-2.0

"""
File management helpers for organizing VLSI library and design files.

This module provides utilities for managing collections of files with associated
attributes (e.g., process corners, temperatures, voltages). It is independent of
the core PyDesignFlow functionality.
"""

from pathlib import Path
from dataclasses import dataclass
import re

class FileManagementError(Exception):
    """Exception raised for file management related errors."""
    pass

def checkfile(path: Path) -> Path:
    """
    Check that path exists and is a file, then return path.

    Args:
        path: Path to verify.

    Returns:
        The input path if validation succeeds.

    Raises:
        FileManagementError: If path does not exist or is not a file.
    """
    if not path.exists():
        raise FileManagementError(f"Path '{path}' does not exist.")
    if not path.is_file():
        raise FileManagementError(f"'{path}' is not a file.")
    return path

def checkdir(path: Path) -> Path:
    """
    Check that path exists and is a directory, then return path.

    Args:
        path: Path to verify.

    Returns:
        The input path if validation succeeds.

    Raises:
        FileManagementError: If path does not exist or is not a directory.
    """
    if not path.exists():
        raise FileManagementError(f"Path '{path}' does not exist.")
    if not path.is_dir():
        raise FileManagementError(f"'{path}' is not a directory.")
    return path

@dataclass
class FileCollectionItem:
    """
    A file with associated attributes.

    Attributes:
        path: File path.
        attrs: Dictionary of attributes (e.g., process corner, temperature).
    """
    path: Path
    attrs: dict[str, object]

    def __iter__(self):
        return iter((self.path, self.attrs))

class FileCollection:
    """
    A collection of files with associated attributes.

    Manages files of the same type (e.g., timing libraries, design files) that differ
    in attributes such as voltage, process corner, or temperature. Supports filtering,
    tagging, and pattern-based creation from directories.
    """

    def __init__(self, items: list[FileCollectionItem]=None):
        """
        Initialize FileCollection.

        Args:
            items: Optional list of FileCollectionItem objects.
        """
        if items == None:
            items = []
        self.items = items

    def __add__(self, other):
        """Combine two FileCollections."""
        return FileCollection(self.items + other.items)

    def __len__(self):
        return len(self.items)

    def __getitem__(self, key):
        return self.items[key]

    def __iter__(self):
        return iter(self.items)

    def tag(self, **attrs: dict[str, object]):
        """
        Add attributes to all items in the collection.

        Args:
            **attrs: Attributes to add to each file.

        Returns:
            New FileCollection with updated attributes.
        """
        ret = FileCollection()
        for i in self.items:
            ret.items.append(FileCollectionItem(i.path, i.attrs | attrs))
        return ret

    def add(self, path: Path, **attrs: dict[str, object]):
        """
        Add a file to the collection.

        Args:
            path: File path to add.
            **attrs: Attributes for this file.

        Raises:
            FileManagementError: If file does not exist.
        """
        self.items.append(FileCollectionItem(checkfile(path), attrs))

    def __repr__(self):
        return f"FileCollection:{self.items}"

    def filter(self, missing_key_deselects: bool = False, **filters: dict[str, object]):
        """
        Filter files by attributes.

        Args:
            missing_key_deselects: If True, exclude items that lack any filter key.
                                   If False (default), only check keys that exist.
            **filters: Attribute filters (e.g., speed='fast', temp=100).

        Returns:
            New FileCollection with matching files.
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
        Get the single file matching the filters.

        Args:
            missing_key_deselects: Passed to :meth:`filter`.
            **filters: Attribute filters.

        Returns:
            Path of the unique matching file.

        Raises:
            FileManagementError: If no match or multiple matches found.
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
        Shorthand for :meth:`one`. Allows ``collection(speed='fast')`` syntax.
        """
        return self.one(*args, **kwargs)

    @classmethod
    def frompattern(cls, dir: Path, pattern: str, decoder):
        """
        Create FileCollection using pattern and decoder function.

        Args:
            dir: Directory (Path) in which to locate files.
            pattern: Regular expression (Python's re module) for finding
                desired files.
            decoder: Decoder function, receives first regular expression
                group string as argument, returns dictionary of file
                attributes.

        Returns:
            new FileCollection object
        """
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
