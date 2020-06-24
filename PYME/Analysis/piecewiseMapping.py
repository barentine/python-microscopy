#!/usr/bin/python

##################
# piecewiseMapping.py
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

import numpy as np

def times_to_frames(t, events, mdh):
    """
    Use events and metadata to convert time-stamps to frame numbers

    Parameters
    ----------
    t: ndarray
        times [seconds since the epoch] to map to frame numbers
    events: ndarray
        TODO - if events-related type fixing goes through, use events helpers to accept list here as well
    mdh: PYME.IO.MetaDataHandler
        Metadata handler with 'Camera.CycleTime' and 'StartTime' entries

    Returns
    -------
    fr: ndarray
        array of frame numbers corresponding to `t` input
    """
    cycTime = mdh.getEntry('Camera.CycleTime')
    startTime = mdh.getEntry('StartTime')

    #se = array([('0', 'start', startTime)], dtype=events.dtype)
    se = np.empty(1, dtype=events.dtype)
    se['EventName'] = 'start'
    se['EventDescr'] = '0'
    se['Time'] = startTime

    #sf = array([('%d' % iinfo(int32).max, 'end', startTime + 60*60*24*7)], dtype=events.dtype)
    sf = np.empty(1, dtype=events.dtype)
    sf['EventName'] = 'end'
    sf['EventDescr'] = '%d' % np.iinfo(np.int32).max
    sf['Time'] = startTime + 60*60*24*7

    #get events corresponding to aquisition starts
    startEvents = hstack((se, events[events['EventName'] == 'StartAq'], sf))

    #print startEvents

    sfr = np.array([int(e['EventDescr']) for e in startEvents])

    si = startEvents['Time'].searchsorted(t, side='right')
    
    #print t    
    #print((si, startEvents, sfr))
    
    #try:
    #    if len(si) > 1:
    #        si = si[-1]
    #except:
    #    pass
    
    #fr = np.zeros_like(t)
    
    
    fr = sfr[si-1] + ((t - startEvents['Time'][si-1]) / cycTime)
    
    if np.isscalar(fr):
        if si < len(sfr):
            return np.minimum(fr, sfr[si])
    else:
        M = (si < len(sfr))
        fr[M] = np.minimum(fr[M], sfr[si[M]])

        return fr

def frames_to_times(fr, events, mdh):
    """
    Use events and metadata to convert frame numbers to seconds

    Parameters
    ----------
    fr: ndarray
        frame numbers to map to time (in seconds since the epoch), e.g. localization data_souce['t']
    events: ndarray
        TODO - if events-related type fixing goes through, use events helpers to accept list here as well
    mdh: PYME.IO.MetaDataHandler
        Metadata handler with 'Camera.CycleTime' and 'StartTime' entries

    Returns
    -------
    t: ndarray
        times [seconds since the epoch] to map to frame numbers
    """
    cycTime = mdh.getEntry('Camera.CycleTime')
    startTime = mdh.getEntry('StartTime')

    #se = array([('0', 'start', startTime)], dtype=events.dtype)
    se = np.empty(1, dtype=events.dtype)
    se['EventName'] = 'start'
    se['EventDescr'] = '0'
    se['Time'] = startTime

    #get events corresponding to aquisition starts
    startEvents = hstack((se, events[events['EventName'] == 'StartAq']))
    #print(events)
    #print(startEvents)

    sfr = np.array([int(e['EventDescr']) for e in startEvents])

    si = sfr.searchsorted(fr, side = 'right')
    return startEvents['Time'][si-1] + (fr - sfr[si-1]) * cycTime
    

class piecewiseMap:
    def __init__(self, y0, xvals, yvals, secsPerFrame=1, xIsSecs=True):
        self.y0 = y0

        if xIsSecs: #store in frame numbers
            self.xvals = xvals / secsPerFrame
        else:
            self.xvals = xvals
        self.yvals = yvals

        self.secsPerFrame = secsPerFrame
        self.xIsSecs = xIsSecs

    def __call__(self, xp, xpInFrames=True):
        xp = xp.astype('f') #fast to float in case we get passed an int
        yp = 0 * xp

        if not xpInFrames:
            xp = xp / self.secsPerFrame
        
#        y0 = self.y0
#        x0 = -inf
#
#        for x, y in zip(self.xvals, self.yvals):
#            yp += y0 * (xp >= x0) * (xp < x)
#            x0, y0 = x, y
#
#        x  = +inf
#        yp += y0 * (xp >= x0) * (xp < x)

        inds = self.xvals.searchsorted(xp, side='right')
        yp  = self.yvals[np.maximum(inds-1, 0)]
        yp[inds == 0] = self.y0

        return yp

def GeneratePMFromProtocolEvents(events, metadata, x0, y0, id='setPos', idPos = 1, dataPos=2):
    x = []
    y = []

    secsPerFrame = metadata.getEntry('Camera.CycleTime')

    for e in events[events['EventName'] == 'ProtocolTask']:
        #if e['EventName'] == eventName:
        ed = e['EventDescr'].split(', ')
        if ed[idPos] == id:
            x.append(e['Time'])
            y.append(float(ed[dataPos]))
            
    x = np.array(x)
    y = np.array(y)
    
    I = np.argsort(x)
    
    x = x[I]
    y = y[I]

    return piecewiseMap(y0, times_to_frames(x, events, metadata), y, secsPerFrame, xIsSecs=False)


def GeneratePMFromEventList(events, metadata, x0, y0, eventName='ProtocolFocus', dataPos=1):
    """
    Parameters
    ----------
    events:
    metadata:
    x0: why?
    y0:
    eventName:
    dataPos: int
        position in comma-separated event['EventDesc'] str of the float which makes 'y' for this mapping

    Returns
    -------
    map: piecewiseMap
    """
    x = []
    y = []

    secsPerFrame = metadata.getEntry('Camera.CycleTime')

    for e in events[events['EventName'] == eventName]:
        #if e['EventName'] == eventName:
        #print(e)
        x.append(e['Time'])
        y.append(float(e['EventDescr'].split(', ')[dataPos]))
        
    x = np.array(x)
    y = np.array(y)
        
    I = np.argsort(x)
    
    x = x[I]
    y = y[I]

    #print array(x) - metadata.getEntry('StartTime'), timeToFrames(array(x), events, metadata)

    return piecewiseMap(y0, times_to_frames(x, events, metadata), y, secsPerFrame, xIsSecs=False)

def bool_map_between_events(events, metadata, trigger_high, trigger_low, default=False):
    """
    generate a TTL output mapping [input time in units of frames] using events to trigger high/low

    Parameters
    ----------
    events: list or structured ndarray
        acquisition events
    metadata: PYME.IO.MetaDataHandler.MDHandlerBase
        metadata with 'Camera.CycleTime' and 'StartTime' entries
    trigger_high: bytes
        name of event to set output mapping high
    trigger_low: bytes
        name of event to set output mapping low
    default: bool
        start mapping low (False) or high (True) at t=0

    Returns
    -------
    bool_map: piecewiseMap
        callable mapping object
    """
    t, y = [], []

    fps = metadata.getEntry('Camera.CycleTime')

    for event in events:
        if event['EventName'] == trigger_high:
            t.append(event['Time'])
            y.append(True)
        elif event['EventName'] == trigger_low:
            t.append(event['Time'])
            y.append(False)

    t = np.asarray(t)
    y = np.asarray(y)
    I = np.argsort(t)

    return piecewiseMap(default, times_to_frames(t[I], events, metadata), y[I], fps, xIsSecs=False)

def GenerateBacklashCorrPMFromEventList(events, metadata, x0, y0, eventName='ProtocolFocus', dataPos=1, backlash=0):
    x = []
    y = []

    secsPerFrame = metadata.getEntry('Camera.CycleTime')

    for e in events[events['EventName'] == eventName]:
        #if e['EventName'] == eventName:
        x.append(e['Time'])
        y.append(float(e['EventDescr'].split(', ')[dataPos]))

    x = np.array(x)
    y = np.array(y)

    dy = np.diff(np.hstack(([y0], y)))

    for i in range(1, len(dy)):
        if dy[i] == 0:
            dy[i] = dy[i-1]

    y += backlash*(dy < 0)


    return piecewiseMap(y0, times_to_frames(x, events, metadata), y, secsPerFrame, xIsSecs=False)

