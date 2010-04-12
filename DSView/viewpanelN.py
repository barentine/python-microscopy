#!/usr/bin/python

##################
# viewpanel.py
#
# Copyright David Baddeley, 2009
# d.baddeley@auckland.ac.nz
#
# This file may NOT be distributed without express permision from David Baddeley
#
##################

#!/usr/bin/env python
# generated by wxGlade 0.3.3 on Mon Jun 14 07:44:41 2004

import wx
import pylab
from PYME.misc import extraCMaps
from PYME.Analysis.LMVis import histLimits

def fast_grey(data):
    return data[:,:,None]*pylab.ones((1,1,4))

fast_grey.name = 'fastGrey'

class OptionsPanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        kwargs['style'] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, parent, *args, **kwargs)

        self.parent = parent

        vsizer = wx.BoxSizer(wx.VERTICAL)

        self.hIds = []
        self.cIds = []
        self.cbIds = []
        self.hcs = []

        cmapnames = pylab.cm.cmapnames + ['fastGrey']# + [n + '_r' for n in pylab.cm.cmapnames]
        cmapnames.sort()
        do = parent.do

        for i in range(len(do.Chans)):
            ssizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Chan %d' %i), wx.VERTICAL)

            id = wx.NewId()
            self.hIds.append(id)
            c = self.parent.ds[:,:,self.parent.zp,do.Chans[i]].ravel()
            hClim = histLimits.HistLimitPanel(self, id, c[::max(1, len(c)/1e4)], do.Offs[i], do.Offs[i] + 1./do.Gains[i], size=(120, 80), log=True)

            hClim.Bind(histLimits.EVT_LIMIT_CHANGE, self.OnCLimChanged)
            self.hcs.append(hClim)

            ssizer.Add(hClim, 0, wx.ALL, 5)

            id = wx.NewId()
            self.cIds.append(id)
            cCmap = wx.Choice(self, id, choices=cmapnames)
            cCmap.SetSelection(cmapnames.index(do.cmaps[i].name))
            cCmap.Bind(wx.EVT_CHOICE, self.OnCMapChanged)
            ssizer.Add(cCmap, 0, wx.ALL, 5)

            vsizer.Add(ssizer, 0, wx.ALL, 5)

        self.bOptimise = wx.Button(self, -1, "Optimise")
        vsizer.Add(self.bOptimise, 0, wx.ALL|wx.ALIGN_CENTER, 5)

        ssizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Slice'), wx.VERTICAL)
        self.cbSlice = wx.Choice(self, -1, choices=["X-Y", "X-Y @ 90 Deg", "X-Z", "Y-Z"])
        self.cbSlice.SetSelection(0)
        ssizer.Add(self.cbSlice, 1, wx.ALL|wx.EXPAND, 5)

        vsizer.Add(ssizer, 0, wx.ALL|wx.EXPAND, 5)

        ssizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Scale'), wx.VERTICAL)
        self.cbScale = wx.Choice(self, -1, choices=["1:4", "1:2", "1:1", "2:1", "4:1"])
        self.cbScale.SetSelection(2)
        ssizer.Add(self.cbScale, 1, wx.ALL|wx.EXPAND, 5)

        vsizer.Add(ssizer, 0, wx.ALL|wx.EXPAND, 5)

        self.SetSizerAndFit(vsizer)

        self.cbSlice.Bind(wx.EVT_CHOICE, self.OnSliceChanged)
        self.cbScale.Bind(wx.EVT_CHOICE, self.OnScaleChanged)

        self.bOptimise.Bind(wx.EVT_BUTTON, self.parent.Optim)

    def OnSliceChanged(self, event):
        if (self.parent.updating == 0):
            if (self.cbSlice.GetSelection() == 0):
                self.parent.do.slice =(self.parent.do.SLICE_XY)
                self.parent.do.orientation = (self.parent.do.UPRIGHT)
            elif (self.cbSlice.GetSelection() == 1):
                self.parent.do.slice = (self.parent.do.SLICE_XY)
                self.parent.do.orientation = (self.parent.do.ROT90)
            elif (self.cbSlice.GetSelection() == 2):
                self.parent.do.slice =(self.parent.do.SLICE_XZ)
                self.parent.do.orientation=(self.parent.do.UPRIGHT)
            elif (self.cbSlice.GetSelection() == 3):
                self.parent.do.slice =(self.parent.do.SLICE_YZ)
                self.parent.do.orientation  =self.parent.do.UPRIGHT

            #self.parent.Refresh()
            self.parent.GetOpts()

    def OnScaleChanged(self, event):
        if (self.parent.updating == 0):
            self.parent.scale = self.cbScale.GetSelection()
            self.parent.GetOpts()

    def OnCLimChanged(self, event):
        #print event.GetId()
        ind = self.hIds.index(event.GetId())
        self.parent.do.Offs[ind] = event.lower
        self.parent.do.Gains[ind] = 1./(event.upper- event.lower)
        self.parent.Refresh()

    def OnCMapChanged(self, event):
        #print event.GetId()
        ind = self.cIds.index(event.GetId())

        cmn = event.GetString()
        if cmn == 'fastGrey':
            self.parent.do.cmaps[ind] = fast_grey
        else:
            self.parent.do.cmaps[ind] = pylab.cm.__getattribute__(cmn)
            
        self.parent.Refresh()

    def RefreshHists(self):
        do = self.parent.do
        for i in range(len(do.Chans)):
            c = self.parent.ds[:,:,self.parent.zp,do.Chans[i]].ravel()
            self.hcs[i].SetData(c[::max(1, len(c)/1e4)], do.Offs[i], do.Offs[i] + 1./do.Gains[i])



class ImagePanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)

        self.parent = parent


        wx.EVT_PAINT(self, self.OnPaint)
        wx.EVT_ERASE_BACKGROUND(self, self.DoNix)

    def DoNix(self, event):
        pass

    def OnPaint(self,event):
        
        #self.painting = True
        DC = wx.PaintDC(self)
#        if not time.time() > (self.lastUpdateTime + 2*self.lastFrameTime): #avoid paint floods
#            if not self.refrTimer.IsRunning():
#                self.refrTimer.Start(.2, True) #make sure we do get a refresh after disposing of flood
#            return

        #frameStartTime = time.time()

        self.PrepareDC(DC)

        #x0,y0 = self.parent.CalcUnscrolledPosition(0,0)

        #s = self.imagepanel.GetVirtualSize()
        s = self.GetClientSize()
        MemBitmap = wx.EmptyBitmap(s.GetWidth(), s.GetHeight())
        #del DC
        MemDC = wx.MemoryDC()
        OldBitmap = MemDC.SelectObject(MemBitmap)
        try:
            DC.BeginDrawing()
            #DC.Clear()
            #Perform(WM_ERASEBKGND, MemDC, MemDC);
            #Message.DC := MemDC;
            self.parent.parent.DoPaint(MemDC);
            #Message.DC := 0;
            #DC.BlitXY(0, 0, s.GetWidth(), s.GetHeight(), MemDC, 0, 0)
            DC.Blit(0, 0, s.GetWidth(), s.GetHeight(), MemDC, 0, 0)
            DC.EndDrawing()
        finally:
            #MemDC.SelectObject(OldBitmap)
            del MemDC
            del MemBitmap

        #self.lastUpdateTime = time.time()
        #self.lastFrameTime = self.lastUpdateTime - frameStartTime

        #self.painting = False




class ScrolledImagePanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)

        self.parent = parent
        
        self.imSize = (0,0)
        self.xOff = 0
        self.yOff = 0

        self.scrollRangeX = 0
        self.scrollRangeY = 0

        gridSizer = wx.FlexGridSizer(2)

        self.impanel = ImagePanel(self, -1, size = self.Size)
        gridSizer.Add(self.impanel, 1, wx.EXPAND, 0)

        self.scrollY = wx.ScrollBar(self, -1, style=wx.SB_VERTICAL)
        gridSizer.Add(self.scrollY, 0, wx.EXPAND, 0)

        self.scrollX = wx.ScrollBar(self, -1)
        gridSizer.Add(self.scrollX, 0, wx.EXPAND, 0)

        gridSizer.AddGrowableRow(0)
        gridSizer.AddGrowableCol(0)

        self.SetSizerAndFit(gridSizer)

        self.scrollX.Bind(wx.EVT_COMMAND_SCROLL, self.OnScrollX)
        self.scrollY.Bind(wx.EVT_COMMAND_SCROLL, self.OnScrollY)

        wx.EVT_SIZE(self, self.OnSize)


    def CalcUnscrolledPosition(self, x, y):
        return x + self.xOff, y + self.yOff

    def SetVirtualSize(self,size):
        self.imSize = size
        
        self.RefreshScrollbars()


    def RefreshScrollbars(self):
        self.scrollRangeX = max(0, self.imSize[0] - self.impanel.Size[0])
        self.xOff = min(self.xOff, self.scrollRangeX)
        self.scrollX.SetScrollbar(self.xOff, max(1,  self.scrollRangeX*self.impanel.Size[0]/max(1, self.imSize[0])), self.scrollRangeX, 10)

        self.scrollRangeY = max(0, self.imSize[1] - self.impanel.Size[1])
        self.yOff = min(self.yOff, self.scrollRangeY)
        self.scrollY.SetScrollbar(self.yOff, max(1,  self.scrollRangeY*self.impanel.Size[1]/max(1, self.imSize[1])), self.scrollRangeY, 10)

#        if self.imSize[0] < self.impanel.Size[0]: #don't need scrollbar
#            self.scrollX.Hide()
#        else:
#            self.scrollX.Show()

        self.impanel.Refresh()

#    def GetClientSize(self):
#        return self.impanel.Get
#        pass

    def GetScrollPixelsPerUnit(self):
        return (1,1)

    def OnScrollX(self,event):
        self.xOff = event.GetPosition()

        self.impanel.Refresh()

    def OnScrollY(self,event):
        self.yOff = event.GetPosition()
        print self.yOff

        self.impanel.Refresh()

    def OnSize(self, event):
        self.RefreshScrollbars()
        event.Skip()

    def Scroll(self, dx, dy):
        self.xOff += dx
        self.yOff += dy

        self.RefreshScrollbars()


class ViewPanel(wx.Panel):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)

        vpsizer = wx.BoxSizer(wx.HORIZONTAL)

        self.imagepanel = ScrolledImagePanel(self, -1, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL)
        #self.imagepanel.SetMinSize((50,50))
        #self.imagepanel.SetScrollRate(10, 10)
        vpsizer.Add(self.imagepanel, 1, wx.EXPAND, 0)

        self.bShowOpts = wx.Button(self, -1, "", size=wx.Size(7,-1))
        vpsizer.Add(self.bShowOpts, 0, wx.EXPAND, 0)
        
        self.optionspanel = OptionsPanel(self, -1)
        #self.optionspanel = wx.ScrolledWindow(self, -1)
        #self.optionspanel.SetScrollRate(10, 10)
        vpsizer.Add(self.optionspanel, 0, wx.EXPAND, 0)


        self.SetSizerAndFit(vpsizer)

    

   


