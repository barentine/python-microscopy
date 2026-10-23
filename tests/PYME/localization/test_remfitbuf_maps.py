import os

import numpy as np
import pytest

from PYME.IO import MetaDataHandler
from PYME.localization.remFitBuf import CameraInfoManager


@pytest.fixture
def dark_map(tmp_path):
    tifffile = pytest.importorskip('tifffile')
    os.makedirs(tmp_path / 'CALIBRATION')
    data = np.arange(12, dtype='f4').reshape(4, 3)
    tifffile.imwrite(str(tmp_path / 'CALIBRATION' / 'dark.tif'), data)
    return tmp_path, data


def _mdh():
    md = MetaDataHandler.NestedClassMDHandler()
    # no task queue, so maps are loaded from file
    md.taskQueue = None
    md.dataSourceID = None
    return md


def test_fetch_map_local_path(dark_map):
    root, data = dark_map
    m = CameraInfoManager()._fetchMap(_mdh(), str(root / 'CALIBRATION' / 'dark.tif'))
    np.testing.assert_array_equal(m, data)


def test_fetch_map_cluster_uri(dark_map, monkeypatch):
    # pyme-cluster:/// URIs (as produced by the clusterUI file selector) should resolve to the local data root
    from PYME.IO import clusterIO
    root, data = dark_map
    monkeypatch.setattr(clusterIO, 'local_dataroot', str(root))

    m = CameraInfoManager()._fetchMap(_mdh(), 'pyme-cluster:///CALIBRATION/dark.tif')
    np.testing.assert_array_equal(m, data)
