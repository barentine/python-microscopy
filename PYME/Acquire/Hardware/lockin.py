
# import time


def lockin_signal_to_Vpkpk_square(vrms_sine):
    """Convert from Vrms of a sine wave, i.e. lock-in signal, to the equivalent
    Vpk-pk of a square wave modulated input. This is useful if using a binary
    modulation scheme, i.e. a square wave, rather than a sineusoidal modulation
    scheme.

    Parameters
    ----------
    vrms_sine : float
        Vrms signal of the lock-in.

    Returns
    -------
    float
        Vpk-pk of the equivalent square wave
    
    Notes
    -----
    a 1 V pk-pk square wave results in a 0.45 V RMS signal reading on the lockin
    This can be decomposed as:
    1.273 [sine/square] * 1/sqrt(2) [RMS amplitude / PK amplitude] * 0.5 [PK amplitude / PK-PK amplitude] = 0.45
    So a 1 V RMS signal on the lock-in is equivalent to a 2.22 V pk-pk square wave
    signal from the detector (or whatever the input is)
    """
    return vrms_sine / 0.45

def analog_read_to_lockin_signal(xout, sensitivity, offset=0, expand=1):
    """Convert from the lock-in's Xout (or Yout or Rout) analog signal to the 
    measured RMS sine wave signal it corresponds to, accounting for offset
    and expand settings, if applicable. This is based on the SR850 manual,
    and might not be correct for other lock-ins.

    Parameters
    ----------
    xout : float, ndarray
        output voltage of the lock-in for either X, Y, or R (magnitude)
    sensitivity : float
        full scale sensitivity, in [V]
    offset : float, optional
        an offset, if added to the output, by default 0
    expand : int, optional
        expansion factor, if applied to the output. Default is 1 (no expansion).

    Returns
    -------
    vrms_sine: float, ndarray
        Vrms signal of the lock-in that would produce this analog output.
    """
    return ((xout / 10) / expand + offset) * sensitivity 

class OpticalReceiverBase(object):
    """Base class for optical receivers"""
    def __init__(self, responsivity):
        self.responsivity = responsivity  # [A/W]
    
    def watts_from_volts(self, volts, responsivity=None):
        """Convert from measured voltage to incident wattage, 
        using the responsivity of the detector"""
        raise NotImplementedError('Subclasses must implement this method')
    
    @property
    def gain(self):
        """Voltage gain of the detector, in [V/A]"""
        raise NotImplementedError('Subclasses must implement this method')
    
    def shot_noise(self, watts, rms=False):
        """Calculate the shot noise for a given incident wattage
        
        Returns
        -------
        noise: float
            expected shot noise in [V/sqrt(Hz)], i.e. the noise spectral density, for the given incident power
        """
        # Shot noise current: i_shot = sqrt(2 * e * I * B), where I is the photocurrent
        # Photocurrent: I = P * R, where P is the incident power and R is the responsivity
        # So i_shot = sqrt(2 * e * P * R * B)
        import numpy as np
        e = 1.602e-19  # elementary charge in Coulombs
        I = watts * self.responsivity  # [W] * [A/W] = [A]
        v_shot = self.gain* np.sqrt(2 * e * I)  # V/sqrt(Hz)
        v_shot_mad = np.sqrt(2 / np.pi) * v_shot  # convert from RMS to MAD
        return v_shot_mad if not rms else v_shot

PDA100A2_GAIN = {  # [kV/A]
    0: {'50 Ohm': 0.75, 'Hi-Z': 1.51},
    10: {'50 Ohm': 2.38, 'Hi-Z': 4.75},
    20: {'50 Ohm': 7.5, 'Hi-Z': 15.0},
    30: {'50 Ohm': 23.8, 'Hi-Z': 47.5},
}
class PDA100A2(OpticalReceiverBase):
    """holds detector gain and responsivity information for the Thorlabs PDA100A2"""
    def __init__(self, responsivity=0.5, gain_db=0, load_impedance='50 Ohm'):
        self.gain = 1e3* PDA100A2_GAIN[gain_db][load_impedance]  # [V/A]
        self.load_impedance = load_impedance
        self.responsivity = responsivity  # [A/W]
    
    def watts_from_volts(self, volts):
        """Convert from volts to watts, using the responsivity of the detector"""
        self.gain = 1e3* PDA100A2_GAIN[self.gain_db][self.load_impedance]  # [V/A]
        return volts / self.gain / self.responsivity

Nirvana2007GAIN = {  # Linear Output only, [V/A]
    'DC': {
        'SIG':20 * 1e3,
        'BAL':20 * 1e3,
        'AUTOBAL':0,
        '10X':0,
        'SigMon': -10 * 1e3  # Signal Monitor output
        },
    'AC': {
        'SIG':100 * 1e3,  # at f > 50 Hz
        'BAL':100 * 1e3,  # at f > 50 Hz
        'AUTOBAL':100 * 1e3,  # at f > fc
        '10X':1000 * 1e3,  # at f > fc
        'SigMon': -10 * 1e3  # at f > fc, Signal Monitor output
        },
    }
    
class Nirvana(OpticalReceiverBase):
    """ 
    Newport/New Focus 2007 auto-balanced receivers

    
    """
    def __init__(self, responsivity, mode='AUTOBAL', frequency_regime='AC'):
        self.responsivity = responsivity  # [A/W]
        self.mode = mode
        self.frequency_regime = frequency_regime
        self._gain = Nirvana2007GAIN[frequency_regime][mode]  # [V/A]

    @property
    def gain(self):
        return Nirvana2007GAIN[self.frequency_regime][self.mode]

    def watts_from_volts(self, volts, mode=None, frequency_regime=None):
        """Convert from volts to watts, using the responsivity of the detector"""
        if mode is None:
            mode = self.mode
        if frequency_regime is None:
            frequency_regime = self.frequency_regime
        gain = Nirvana2007GAIN[frequency_regime][mode]  # [V/A]
        return volts / gain / self.responsivity  # [W/A] / [V/A] = [W/V] = [W] (watts)


class LockinWrapper(object):
    """Thin wrapper around e.g. PyMeasure lockin classes to provide metadata
    and handlers for PYME

    Parameters
    ----------
    object : _type_
        _description_
    """
    def __init__(self, lockin, name='Lockin'):
        self.lockin = lockin
        self.name = name

    def GenStartMetadata(self, mdh):
        """
        Generate start metadata for the lockin.
        """
        # t0 = time.time()
        mdh[self.name + '.time_constant'] = self.lockin.time_constant  # [s]
        mdh[self.name + '.phase'] = self.lockin.phase  # [degrees]
        mdh[self.name + '.sensitivity'] = self.lockin.sensitivity  # [V full scale]
        mdh[self.name + '.filter_slope'] = self.lockin.filter_slope  # [dB/octave]
        mdh[self.name + '.frequency'] = self.lockin.frequency  # [Hz]
        mdh[self.name + '.reference_source'] = self.lockin.reference_source
        mdh[self.name + '.reference_source_trigger'] = self.lockin.reference_source_trigger
        mdh[self.name + '.reserve'] = self.lockin.reserve
        # print('Lockin metadata generation took %f seconds' % (time.time() - t0))
    
    def register(self, scope):
        """
        Add start metadata (anything interesting) and add a state handler for
        a couple of critical values if desired
        """
        from PYME.IO import MetaDataHandler
        MetaDataHandler.provideStartMetadata.append(self.GenStartMetadata)