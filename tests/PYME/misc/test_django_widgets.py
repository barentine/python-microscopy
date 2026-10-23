import pytest

django = pytest.importorskip('django')


@pytest.fixture(scope='module', autouse=True)
def django_settings():
    from django.conf import settings
    if not settings.configured:
        settings.configure()
    django.setup()


def _map_form():
    from django import forms
    from PYME.misc.django_widgets import ClusterFileInput

    class MapForm(forms.Form):
        pass

    MapForm.base_fields['Camera.DarkMapID'] = forms.CharField(required=False, initial='<none>',
                                                              widget=ClusterFileInput())
    return MapForm


def test_cluster_file_input_has_name_attribute():
    # inputs without a name attribute are silently dropped from form submissions
    html = str(_map_form()()['Camera.DarkMapID'])
    assert 'name="Camera.DarkMapID"' in html
    assert 'Camera.DarkMapID="Camera.DarkMapID"' not in html


def test_cluster_file_input_renders_value():
    form = _map_form()({'Camera.DarkMapID': 'pyme-cluster:///dark.tif'})
    html = str(form['Camera.DarkMapID'])
    assert 'value="pyme-cluster:///dark.tif"' in html
