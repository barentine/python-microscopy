#!/usr/bin/python

##################
# FrSpool.py
#
# Copyright David Baddeley, 2009
# d.baddeley@auckland.ac.nz
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##################

#Boa:Frame:FrSpool

import wx
import datetime
import win32api
import os

from PYME.Acquire import Spooler

def create(parent):
    return FrSpool(parent)

[wxID_FRSPOOL, wxID_FRSPOOLBSETSPOOLDIR, wxID_FRSPOOLBSTARTSPOOL, 
 wxID_FRSPOOLBSTOPSPOOLING, wxID_FRSPOOLPANEL1, wxID_FRSPOOLSTATICBOX1, 
 wxID_FRSPOOLSTATICBOX2, wxID_FRSPOOLSTATICTEXT1, wxID_FRSPOOLSTNIMAGES, 
 wxID_FRSPOOLSTSPOOLDIRNAME, wxID_FRSPOOLSTSPOOLINGTO, 
 wxID_FRSPOOLTCSPOOLFILE, 
] = [wx.NewId() for _init_ctrls in range(12)]

def baseconvert(number,todigits):
        x = number
    
        # create the result in base 'len(todigits)'
        res=""

        if x == 0:
            res=todigits[0]
        
        while x>0:
            digit = x % len(todigits)
            res = todigits[digit] + res
            x /= len(todigits)

        return res


class FrSpool(wx.Frame):
    def _init_ctrls(self, prnt):
        # generated method, don't edit
        wx.Frame.__init__(self, id=wxID_FRSPOOL, name='FrSpool', parent=prnt,
              pos=wx.Point(543, 403), size=wx.Size(290, 240),
              style=wx.DEFAULT_FRAME_STYLE, title='Spooling')
        self.SetClientSize(wx.Size(282, 213))

        self.panel1 = wx.Panel(id=wxID_FRSPOOLPANEL1, name='panel1',
              parent=self, pos=wx.Point(0, 0), size=wx.Size(282, 213),
              style=wx.TAB_TRAVERSAL)

        self.bStartSpool = wx.Button(id=wxID_FRSPOOLBSTARTSPOOL,
              label='Start Spooling', name='bStartSpool', parent=self.panel1,
              pos=wx.Point(186, 67), size=wx.Size(88, 23), style=0)
        self.bStartSpool.Bind(wx.EVT_BUTTON, self.OnBStartSpoolButton,
              id=wxID_FRSPOOLBSTARTSPOOL)

        self.staticBox1 = wx.StaticBox(id=wxID_FRSPOOLSTATICBOX1,
              label='Spooling Progress', name='staticBox1', parent=self.panel1,
              pos=wx.Point(7, 101), size=wx.Size(265, 104), style=0)
        self.staticBox1.Enable(False)

        self.stSpoolingTo = wx.StaticText(id=wxID_FRSPOOLSTSPOOLINGTO,
              label='Spooling to .....', name='stSpoolingTo',
              parent=self.panel1, pos=wx.Point(26, 125), size=wx.Size(76, 13),
              style=0)
        self.stSpoolingTo.Enable(False)

        self.stNImages = wx.StaticText(id=wxID_FRSPOOLSTNIMAGES,
              label='NNNNN images spooled in MM minutes', name='stNImages',
              parent=self.panel1, pos=wx.Point(26, 149), size=wx.Size(181, 13),
              style=0)
        self.stNImages.Enable(False)

        self.bStopSpooling = wx.Button(id=wxID_FRSPOOLBSTOPSPOOLING,
              label='Stop', name='bStopSpooling', parent=self.panel1,
              pos=wx.Point(105, 173), size=wx.Size(75, 23), style=0)
        self.bStopSpooling.Enable(False)
        self.bStopSpooling.Bind(wx.EVT_BUTTON, self.OnBStopSpoolingButton,
              id=wxID_FRSPOOLBSTOPSPOOLING)

        self.staticBox2 = wx.StaticBox(id=wxID_FRSPOOLSTATICBOX2,
              label='Spool Directory', name='staticBox2', parent=self.panel1,
              pos=wx.Point(8, 8), size=wx.Size(264, 48), style=0)

        self.stSpoolDirName = wx.StaticText(id=wxID_FRSPOOLSTSPOOLDIRNAME,
              label='Save images in: Blah Blah', name='stSpoolDirName',
              parent=self.panel1, pos=wx.Point(21, 28), size=wx.Size(136, 13),
              style=0)

        self.bSetSpoolDir = wx.Button(id=wxID_FRSPOOLBSETSPOOLDIR, label='Set',
              name='bSetSpoolDir', parent=self.panel1, pos=wx.Point(222, 23),
              size=wx.Size(40, 23), style=0)
        self.bSetSpoolDir.SetThemeEnabled(False)
        self.bSetSpoolDir.Bind(wx.EVT_BUTTON, self.OnBSetSpoolDirButton,
              id=wxID_FRSPOOLBSETSPOOLDIR)

        self.tcSpoolFile = wx.TextCtrl(id=wxID_FRSPOOLTCSPOOLFILE,
              name='tcSpoolFile', parent=self.panel1, pos=wx.Point(81, 68),
              size=wx.Size(100, 21), style=0, value='dd_mm_series_a')
        self.tcSpoolFile.Bind(wx.EVT_TEXT, self.OnTcSpoolFileText,
              id=wxID_FRSPOOLTCSPOOLFILE)

        self.staticText1 = wx.StaticText(id=wxID_FRSPOOLSTATICTEXT1,
              label='Series name:', name='staticText1', parent=self.panel1,
              pos=wx.Point(11, 72), size=wx.Size(66, 13), style=0)

    def __init__(self, parent, scope, defDir, defSeries='%(day)d_%(month)d_series'):
        self._init_ctrls(parent)
        self.scope = scope
        
        dtn = datetime.datetime.now()
        
        dateDict = {'username' : win32api.GetUserName(), 'day' : dtn.day, 'month' : dtn.month, 'year':dtn.year}
        
        self.dirname = defDir % dateDict
        self.seriesStub = defSeries % dateDict

        self.seriesCounter = 0
        self.seriesName = self._GenSeriesName()
        
        self.stSpoolDirName.SetLabel(self.dirname)
        self.tcSpoolFile.SetValue(self.seriesName)

    def _GenSeriesName(self):
        return self.seriesStub + '_' + self._NumToAlph(self.seriesCounter)

    def _NumToAlph(self, num):
        return baseconvert(num, 'ABCDEFGHIJKLMNOPQRSTUVXWYZ')
        

    def OnBStartSpoolButton(self, event):
        #fn = wx.FileSelector('Save spooled data as ...', default_extension='.log',wildcard='*.log')
        #if not fn == '': #if the user cancelled 
        #    self.spooler = Spooler.Spooler(self.scope, fn, self.scope.frameWrangler, self)
        #    self.bStartSpool.Enable(False)
        #    self.bStopSpooling.Enable(True)
        #    self.stSpoolingTo.Enable(True)
        #    self.stNImages.Enable(True)
        #    self.stSpoolingTo.SetLabel('Spooling to ' + fn)
        #    self.stNImages.SetLabel('0 images spooled in 0 minutes')
        
        fn = self.tcSpoolFile.GetValue()

        if fn == '': #sanity checking
            wx.MessageBox('Please enter a series name', 'No series name given', wx.OK)
            return #bail
        
        if not os.path.exists(self.dirname):
            os.makedirs(self.dirname)

        if fn in os.listdir(self.dirname): #check to see if data with the same name exists
            ans = wx.MessageBox('A series with the same name already exists ... overwrite?', 'Warning', wx.YES_NO)
            if ans == wx.NO:
                return #bail

        self.spooler = Spooler.Spooler(self.scope, self.dirname + fn + '.log', self.scope.frameWrangler, self)
        self.bStartSpool.Enable(False)
        self.bStopSpooling.Enable(True)
        self.stSpoolingTo.Enable(True)
        self.stNImages.Enable(True)
        self.stSpoolingTo.SetLabel('Spooling to ' + fn)
        self.stNImages.SetLabel('0 images spooled in 0 minutes')
        

    def OnBStopSpoolingButton(self, event):
        self.spooler.StopSpool()
        self.bStartSpool.Enable(True)
        self.bStopSpooling.Enable(False)
        self.stSpoolingTo.Enable(False)
        self.stNImages.Enable(False)

        self.seriesCounter +=1
        self.seriesName = self._GenSeriesName() 
        self.tcSpoolFile.SetValue(self.seriesName)
        
    def Tick(self):
        dtn = datetime.datetime.now()
        
        dtt = dtn - self.spooler.dtStart
        
        self.stNImages.SetLabel('%d images spooled in %d seconds' % (self.spooler.imNum, dtt.seconds))

    def OnBSetSpoolDirButton(self, event):
        ndir = wx.DirSelector()
        if not ndir == '':
            self.dirname = ndir + os.sep
            self.stSpoolDirName.SetLabel(self.dirname)

    def OnTcSpoolFileText(self, event):
        event.Skip()
        
