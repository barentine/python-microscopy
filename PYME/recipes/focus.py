
from .base import register_module, ModuleBase, Filter
from .traits import Input, Output, Float, ListFloat
import numpy as np
from PYME.IO import tabular, MetaDataHandler
import logging

logger = logging.getLogger(__name__)


class GaussFitter1D(object):
    """
    1D gaussian fitter for use with focus locks which either have line-cameras, or whose frames are summed alone one
    direction to create a line profile, the peak position of which indicates the current focal position.
    """
    def __init__(self, maxfev=200, min_amp=0, max_sigma=np.finfo(float).max):
        """
        Parameters
        ----------
        maxfev: int
            see scipy.optimize.leastsq argument by the same name
        min_amp : float
            minimum fit result amplitude which we are willing to accept as a
            successful fit.
        max_sigma : float
            maximum fit result sigma which we are willing to accept as a
            successful fit.
        """
        self.maxfev = maxfev
        self._min_amp = min_amp
        self._max_sigma = max_sigma

    def _model_function(self, parameters, position):
        """
        1D gaussian
        Parameters
        ----------
        parameters : tuple
            fit model parameters
        distance : ndarray
            1D position array [pixel]
        Returns
        -------
        model : ndarray
        """
        amplitude, center, sigma, bx, b = parameters
        return amplitude * np.exp(-((position - center) ** 2) / (2 * sigma ** 2)) + bx * position + b

    def _error_function(self, parameters, position, data):
        """
        """
        return data - self._model_function(parameters, position)

    def _calc_guess(self, position, data):
        offset = data.min()
        p95 = np.percentile(data, 95)
        amplitude = p95 - offset
        max_ind = np.argmin(np.abs(data - p95))
        fwhm = np.sum(data > offset + 0.5 * amplitude)
        # amplitude, center, sigma, bx, b = parameters
        return amplitude, position[max_ind], fwhm / 2.355, 0, offset

    def fit(self, position, data):
        from scipy import optimize

        guess = self._calc_guess(position, data)

        (res, cov_x, infodict, mesg, res_code) = optimize.leastsq(self._error_function, guess, args=(position, data),
                                                                 full_output=True, maxfev=self.maxfev)

        success = res_code > 0 and res_code < 5 and res[0] > self._min_amp and res[2] < self._max_sigma
        return tuple(res.astype('f')), success


@register_module('StackSettingsAboutFocus')
class StackSettingsAboutFocus(ModuleBase):
    """
    
    """
    input_stack = Input('input')
    bounds = ListFloat([-1, 1])
    step_size = Float(0)
    output = Output('with_stack_settings')

    def execute(self, namespace):
        from scipy.ndimage import laplace
        from PYME.Analysis.piezo_movement_correction import correct_target_positions
        # from PYME.recipes.processing import Threshold

        im = namespace[self.input_stack]
        
        z = correct_target_positions(np.arange(im.data.shape[2]), im.events, im.mdh)

        bin_edges = np.arange(z.min() - 0.5 * im.mdh['StackSettings.StepSize'],
                              z.max() + 1.5 * im.mdh['StackSettings.StepSize'],
                              im.mdh['StackSettings.StepSize'])
        
        binned = np.digitize(z, bin_edges)
        uni = np.unique(binned)
        
            
        if 'Multiview.ActiveViews' in im.mdh:
            # dodge striping in the middle
            from PYME.recipes.multiview import ExtractMultiviewChannel
            nvars = []
            for view in im.mdh['Multiview.ActiveViews']:
                chan = ExtractMultiviewChannel(view_number=view).apply_simple(im)
                nvars.append(np.var(chan.data[:,:,:,0], axis=(0, 1)) / np.mean(chan.data[:,:,:,0], axis=(0, 1)))
            nvar = np.mean(nvars, axis=0)
        else:
            nvar = np.var(im.data[:,:,:,0], axis=(0, 1)) / np.mean(im.data[:,:,:,0], axis=(0, 1))

        metric = []
        z_filt = []
        for label in uni:
            this = label == binned
            I = np.argmax(nvar[this])
            metric.append(nvar[this][I])
            z_filt.append(z[this][I])

        fitter = GaussFitter1D()
        res, success = fitter.fit(np.array(z_filt), np.array(metric))
        if not success:
            raise RuntimeError('Fit did not converge')

        # zz = np.linspace(z.min(), z.max(), 100)
        # fitted = fitter._model_function(res, zz)
        # plt.plot(zz, fitted)

        bottom = res[1] + self.bounds[0]
        top = res[1] + self.bounds[1]

        mdh = MetaDataHandler.DictMDHandler({
            'StackSettings.StartPos': bottom,
            'StackSettings.EndPos': top,
            'StackSettingsAboutFocus.Center': res[1]
        })
        logger.debug('StartPos %.3f, EndPos %.3f' % (bottom, top))
        if self.step_size != 0:
            mdh['StackSettings.StepSize'] = self.step_size
        for k in im.mdh.keys():
            if k.startswith('Sample'):
                mdh[k] = im.mdh[k]

        vx, vy, _ = im.mdh.voxelsize_nm

        roi_position = tabular.DictSource({
            # set position to be center of the field of view imaged
            'x': np.asarray([1e3 * im.mdh['Positioning.x'] + vx * (im.mdh['Multiview.ROI0Origin'][0] + 0.5 * im.mdh['Multiview.ROISize'][0])]),
            'y': np.asarray([1e3 * im.mdh['Positioning.y'] + vy * (im.mdh['Multiview.ROI0Origin'][1] + 0.5 * im.mdh['Multiview.ROISize'][1])])
        })

        roi_position.mdh = mdh

        namespace[self.output] = roi_position