
from PYME.Acquire.ExecTools import joinBGInit, init_gui, init_hardware
from PYME import config

@init_hardware('AndorClara')
def pco_cam(scope):
    from PYME.Acquire.Hardware.AndorNeo.AndorClara import AndorClara

    import logging
    logger = logging.getLogger(__name__)

    cam = AndorClara(0)
    cam.Init()

    scope.register_camera(cam, 'AndorClara', rotate=False, flipx=False, 
                          flipy=False)

@init_gui('camera controls')
def cam_controls(main_frame, scope):
    from PYME.Acquire.Hardware.AndorNeo.AndorZyla import ZylaControl
    scope.camControls['AndorClara'] = ZylaControl(main_frame, 
                                                  scope.cameras['AndorClara'],
                                                  scope)
    camPanels.append((scope.camControls['AndorClara'], 'CCD Properties'))

joinBGInit() 
scope.initDone = True
