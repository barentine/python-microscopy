#!/usr/bin/python

# layers.py
#
# Copyright Michael Graff
#   graff@hm.edu
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
import abc
import warnings

from PYME.LMVis.shader_programs.ShaderProgramFactory import ShaderProgramFactory

from PYME.recipes.traits import HasTraits, Bool, Instance

class BaseEngine(object):
    def __init__(self):
        self._shader_program = None
    
    def set_shader_program(self, shader_program):
        self._shader_program = ShaderProgramFactory.get_program(shader_program)

    @property
    def shader_program(self):
        return self._shader_program
    
    @abc.abstractmethod
    def render(self, gl_canvas, layer):
        pass
    
    def _set_shader_clipping(self, gl_canvas):
        self.shader_program.xmin, self.shader_program.xmax = gl_canvas.bounds['x'][0]
        self.shader_program.ymin, self.shader_program.ymax = gl_canvas.bounds['y'][0]
        self.shader_program.zmin, self.shader_program.zmax = gl_canvas.bounds['z'][0]
        self.shader_program.vmin, self.shader_program.vmax = gl_canvas.bounds['v'][0]
        

class BaseLayer(HasTraits):
    """
    This class represents a layer that should be rendered. It should represent a fairly high level concept of a layer -
    e.g. a Point-cloud of data coming from XX, or a Surface representation of YY. If such a layer can be rendered multiple
    different but similar ways (e.g. points/pointsprites or shaded/wireframe etc) which otherwise share common settings
    e.g. point size, point colour, etc ... these representations should be coded as one layer with a selectable rendering
    backend or 'engine' responsible for managing shaders and actually executing the opengl code. In this case use the
    `EngineLayer` class as a base
.
    In simpler cases, such as rendering an overlay it is acceptable for a layer to do it's own rendering and manage it's
    own shader. In this case, use `SimpleLayer` as a base.
    """
    visible = Bool(True)
        
    @property
    def bbox(self):
        """Bounding box in form [x0,y0,z0, x1,y1,z1] (or none if a bounding box does not make sense for this layer)
        
        over-ride in derived classes
        """
        return None

    

    @abc.abstractmethod
    def render(self, gl_canvas):
        """
        Abstract render method to be over-ridden in derived classes. Should check self.visible before drawing anything.
        
        Parameters
        ----------
        gl_canvas : the canvas to draw to - an instance of PYME.LMVis.gl_render3D_shaders.LMGLShaderCanvas


        """
        pass
    
class EngineLayer(BaseLayer):
    """
    Base class for layers who delegate their rendering to an engine.
    """
    engine = Instance(BaseEngine)

    def render(self, gl_canvas):
        if self.visible:
            return self.engine.render(gl_canvas, self)
        
    
    @abc.abstractmethod
    def get_vertices(self):
        """
        Provides the engine with a way of obtaining vertex data. Should be over-ridden in derived class
        
        Returns
        -------
        a numpy array of vertices suitable for passing to glVertexPointerf()

        """
        raise(NotImplementedError())

    @abc.abstractmethod
    def get_normals(self):
        """
        Provides the engine with a way of obtaining vertex data. Should be over-ridden in derived class

        Returns
        -------
        a numpy array of normals suitable for passing to glNormalPointerf()

        """
        raise (NotImplementedError())

    @abc.abstractmethod
    def get_colors(self):
        """
        Provides the engine with a way of obtaining vertex data. Should be over-ridden in derived class

        Returns
        -------
        a numpy array of vertices suitable for passing to glColorPointerf()

        """
        raise (NotImplementedError())
    
    
class SimpleLayer(BaseLayer):
    """
    Layer base class for layers which do their own rendering and manage their own shaders
    """
    def __init__(self):
        self._shader_program = None
    
    def set_shader_program(self, shader_program):
        self._shader_program = ShaderProgramFactory.get_program(shader_program)

    @property
    def shader_program(self):
        return self._shader_program

    def get_shader_program(self):
        warnings.warn("use the shader_program property instead", DeprecationWarning)
        return self.shader_program
    
    def _clear_shader_clipping(self):
        self.shader_program.xmin, self.shader_program.xmax = [-1e6, 1e6]
        self.shader_program.ymin, self.shader_program.ymax = [-1e6, 1e6]
        self.shader_program.zmin, self.shader_program.zmax = [-1e6, 1e6]
        self.shader_program.vmin, self.shader_program.vmax = [-1e6, 1e6]