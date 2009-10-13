#!/usr/bin/python

##################
# init_TIRF.py
#
# Copyright David Baddeley, 2009
# d.baddeley@auckland.ac.nz
#
# This file may NOT be distributed without express permision from David Baddeley
#
##################

from PYME.Acquire.Hardware.AndorIXon import AndorIXon
from PYME.Acquire.Hardware.AndorIXon import AndorControlFrame

from PYME.Acquire.Hardware import fakeShutters
import time

InitBG('EMCCD Camera', '''
scope.cam = AndorIXon.iXonCamera()
''')
InitGUI('''
acf = AndorControlFrame.AndorPanel(MainFrame, scope.cam, scope)
camPanels.append((acf, 'Andor EMCCD Properties'))
''')

#setup for the channels to aquire - b/w camera, no shutters
class chaninfo:
    names = ['bw']
    cols = [1] #1 = b/w, 2 = R, 4 = G1, 8 = G2, 16 = B
    hw = [fakeShutters.CH1] #unimportant - as we have no shutters
    itimes = [100]

scope.chaninfo = chaninfo
scope.shutters = fakeShutters


#PIFoc
InitBG('PIFoc', '''
from PYME.Acquire.Hardware.Piezos import piezo_e816
scope.piFoc = piezo_e816.piezo_e816('COM2', 400, -0.399)
scope.piezos.append((scope.piFoc, 1, 'PIFoc'))
''')

InitGUI('''
from PYME.Acquire import sarcSpacing
ssp = sarcSpacing.SarcomereChecker(MainFrame, menuBar1, scope)
''')

InitGUI('''
from PYME.Acquire.Hardware import focusKeys
fk = focusKeys.FocusKeys(MainFrame, menuBar1, scope.piezos[-1])
time1.WantNotification.append(fk.refresh)
''')

#splitter
InitGUI('''
from PYME.Acquire.Hardware import splitter
fk = splitter.Splitter(MainFrame, mControls, scope)
''')

#Z stage
InitBG('Nikon Z-Stage', '''
from PYME.Acquire.Hardware import NikonTE2000
scope.zStage = NikonTE2000.zDrive()
#scope.piezos.append((scope.zStage, 1, 'Z Stepper'))
''')

#from PYME.Acquire.Hardware import frZStage
#frz = frZStage.frZStepper(MainFrame, scope.zStage)
#frz.Show()

##3-axis piezo
#InitBG('Thorlabs Piezo', '''
#from PYME.Acquire.Hardware import thorlabsPiezo
#
##check to see what we've got attached
#piezoSerialNums = thorlabsPiezo.EnumeratePiezos()
#if len(piezoSerialNums) == 3: #expect to see 3 piezos
#    scope.pzx = thorlabsPiezo.TLPiezo(91814461, 'X Axis')
#    scope.pzy = thorlabsPiezo.TLPiezo(91814462, 'Y Axis')
#    scope.pzz = thorlabsPiezo.TLPiezo(91814463, 'Z Axis')
#
#    scope.piezos.append((scope.pzx, 1, 'X Piezo'))
#    scope.piezos.append((scope.pzy, 1, 'Y Piezo'))
#    scope.piezos.append((scope.pzz, 1, 'Z Piezo'))
#
#    #centre the piezos
#    scope.pzx.MoveTo(0,50)
#    scope.pzy.MoveTo(0,50)
#    scope.pzz.MoveTo(0,40)
#else:
#    raise HWNotPresent
#
#''')
    
from PYME.Acquire.Hardware.FilterWheel import WFilter, FiltFrame
filtList = [WFilter(1, 'EMPTY', 'EMPTY', 0),
    WFilter(2, 'ND.5' , 'UVND 0.5', 0.5),
    WFilter(3, 'ND1'  , 'UVND 1'  , 1),
    WFilter(4, 'ND1.5', 'UVND 1.5', 1.5),
    WFilter(5, 'ND2'  , 'UVND 2'  , 2),
    WFilter(6, 'ND3'  , 'UVND 3'  , 3)]

InitGUI('''
try:
    scope.filterWheel = FiltFrame(MainFrame, filtList)
    toolPanels.append((scope.filterWheel, 'Filter Wheel'))
except:
    print 'Error starting filter wheel ...'
''')


#DigiData
#scope.lasers = []
InitBG('DigiData', '''
from PYME.Acquire.Hardware.DigiData import DigiDataClient
dd = DigiDataClient.getDDClient()


from PYME.Acquire.Hardware import lasers
scope.lFibre = lasers.DigiDataSwitchedLaser('Fibre',dd,1)
scope.l405 = lasers.DigiDataSwitchedLaserInvPol('405',dd,0)
scope.l543 = lasers.DigiDataSwitchedAnalogLaser('543',dd,0)
#scope.l671 = lasers.DigiDataSwitchedAnalogLaser('671',dd,1)

pport = lasers.PPort()
scope.l671 = lasers.ParallelSwitchedLaser('671',pport,0)
scope.l488 = lasers.ParallelSwitchedLaser('488',pport,1)

scope.lasers = [scope.l488,scope.l405,scope.l543,scope.l671, scope.lFibre]
''')

InitGUI('''
if 'lasers'in dir(scope):
    from PYME.Acquire.Hardware import LaserControlFrame
    lcf = LaserControlFrame.LaserControlLight(MainFrame,scope.lasers)
    time1.WantNotification.append(lcf.refresh)
    toolPanels.append((lcf, 'Laser Control'))
''')

##Focus tracking
#from PYME.Acquire.Hardware import FocCorrR
#InitBG('Focus Corrector', '''
#scope.fc = FocCorrR.FocusCorrector(scope.zStage, tolerance=0.20000000000000001, estSlopeDyn=False, recDrift=False, axis='Y', guideLaser=l488)
#scope.StatusCallbacks.append(fc.GetStatus)
#''')
#InitGUI('''
#if 'fc' in dir(scope):
#    scope.fc.addMenuItems(MainFrame, MainMenu)
#    scope.fc.Start(2000)
#''')

from PYME import cSMI


Is = []

def calcSum(caller):
    Is.append(cSMI.CDataStack_AsArray(caller.ds, 0).sum())


#must be here!!!
joinBGInit() #wait for anyhting which was being done in a separate thread
time.sleep(.5)
scope.initDone = True
