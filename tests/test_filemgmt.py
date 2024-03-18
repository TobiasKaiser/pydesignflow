# SPDX-FileCopyrightText: 2024 Tobias Kaiser <mail@tb-kaiser.de>
# SPDX-License-Identifier: Apache-2.0

import pytest
from pydesignflow import filemgmt
from pathlib import Path

def test_checkfile_checkdir(tmp_path):
    fn1 = tmp_path / 'file1'
    with open(fn1, 'w') as f:
        f.write('hello')
    fn2 = tmp_path / 'dir'
    fn2.mkdir()
    fn3 = tmp_path / 'missing_file'

    # Test checkfile:
    assert filemgmt.checkfile(fn1) == fn1
    with pytest.raises(filemgmt.FileManagementError):
        filemgmt.checkfile(fn2)
    with pytest.raises(filemgmt.FileManagementError):
        filemgmt.checkfile(fn3)

    # Test checkdir:
    assert filemgmt.checkdir(fn2) == fn2
    with pytest.raises(filemgmt.FileManagementError):
        filemgmt.checkdir(fn1)
    with pytest.raises(filemgmt.FileManagementError):
        filemgmt.checkdir(fn3)

def test_filecollection(tmp_path):
    c = filemgmt.FileCollection()
    fn_fh = tmp_path / Path("fast_hot.lib")
    fn_fc = tmp_path / Path("fast_cold.lib")
    fn_sh = tmp_path / Path("slow_hot.lib")
    fn_sc = tmp_path / Path("slow_cold.lib")

    for fn in (fn_fh, fn_fc, fn_sh, fn_sc):
        with open(fn, "w") as f: 
            f.write("test")

    c.add(fn_fh, speed='fast', temp=100)
    c.add(fn_fc, speed='fast', temp=-10)
    c.add(fn_sh, speed='slow', temp=100)
    c.add(fn_sc, speed='slow', temp=-10)

    assert c(speed='fast', temp=100) == fn_fh
    assert c(speed='slow', temp=-10) == fn_sc
    assert c(speed='slow', temp=-10, additional_key=1234) == fn_sc

    paths_found = set()
    attrs_found = set()
    for path, attrs in iter(c):
        paths_found.add(path)
        assert attrs['speed'] in ('fast', 'slow')
        assert attrs['temp'] in (-10,100)

    assert paths_found == {fn_fh, fn_fc, fn_sh, fn_sc}
    assert len(paths_found) == 4

    paths_found = set()
    for path, attrs in c.filter(speed='fast'):
        paths_found.add(path)
        assert attrs['speed'] == 'fast'
        assert attrs['temp'] in (-10,100)

    assert paths_found == {fn_fh, fn_fc}
    assert len(paths_found) == 2

    with pytest.raises(filemgmt.FileManagementError):
        c(speed='fast') # Does not give unique result, therefore fails.
