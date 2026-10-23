import importlib.util
import os

import pytest

pytest.importorskip('django')

import PYME


def _load_views():
    # clusterUI is a django project directory rather than a package, so load the module by path
    path = os.path.join(os.path.dirname(PYME.__file__), 'cluster', 'clusterUI', 'localization', 'views.py')
    spec = importlib.util.spec_from_file_location('clusterui_localization_views', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


views = _load_views()


def test_drop_unset_map_fields_removes_empty_and_default():
    data = {'Camera.DarkMapID': '', 'Camera.VarianceMapID': '<none>', 'Analysis.DetectionThreshold': 1.0}
    views.drop_unset_map_fields(data)
    assert data == {'Analysis.DetectionThreshold': 1.0}


def test_drop_unset_map_fields_keeps_selected_maps():
    data = {'Camera.DarkMapID': 'pyme-cluster:///dark.tif', 'Camera.VarianceMapID': '',
            'Camera.FlatfieldMapID': 'pyme-cluster:///flat.tif'}
    views.drop_unset_map_fields(data)
    assert data == {'Camera.DarkMapID': 'pyme-cluster:///dark.tif',
                    'Camera.FlatfieldMapID': 'pyme-cluster:///flat.tif'}


def test_unset_maps_do_not_override_series_metadata():
    from PYME.IO import MetaDataHandler

    series_mdh = MetaDataHandler.NestedClassMDHandler()
    series_mdh['Camera.DarkMapID'] = 'C:\\CALIBRATION\\dark_200ms.tif'

    analysis_mdh = MetaDataHandler.NestedClassMDHandler()
    analysis_mdh.update(views.drop_unset_map_fields({'Camera.DarkMapID': '', 'Camera.FlatfieldMapID': ''}))

    # mirrors how the rule / task pushers merge series and analysis metadata
    series_mdh.update(analysis_mdh)
    assert series_mdh['Camera.DarkMapID'] == 'C:\\CALIBRATION\\dark_200ms.tif'
    assert 'Camera.FlatfieldMapID' not in series_mdh.getEntryNames()
