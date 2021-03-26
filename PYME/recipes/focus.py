
from .base import register_module, ModuleBase, Filter
from .traits import Input, Output, Float, ListFloat
import numpy as np
from PYME.IO import tabular, MetaDataHandler
import logging

logger = logging.getLogger(__name__)


@register_module('StackSettingsAboutFocus')
class StackSettingsAboutFocus(ModuleBase):
    """
    
    """
    input_stack = Input('input')
    bounds = ListFloat([-1, 1])
    step_size = Float(0)
    output = Output('with_stack_settings')

    def execute(self, namespace):
        from scipy.interpolate import interp1d
        from PYME.Analysis.piezo_movement_correction import correct_target_positions

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

        metric_interp = interp1d(z_filt, metric, kind='quadratic')

        zz = np.linspace(z.min(), z.max(), 10 * len(z_filt))
        zinterpmax = float(zz[np.argmax(metric_interp(zz))])
        # fitted = fitter._model_function(res, zz)
        # plt.plot(zz, fitted)

        bottom = zinterpmax + self.bounds[0]
        top = zinterpmax + self.bounds[1]

        mdh = MetaDataHandler.DictMDHandler({
            'StackSettings.StartPos': bottom,
            'StackSettings.EndPos': top,
            # numpy floats won't serialize later
            'StackSettingsAboutFocus.Center': zinterpmax
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
