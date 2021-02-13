from __future__ import annotations
from typing import Optional, List, Tuple, Callable
from enum import Enum
import numpy as np
import math
import tkinter as tk

"""This tk.Canvas derived class allows to transform the entire scene using translation, scaling and rotation."""

__author__ = "Anton Höß"
__copyright__ = "Copyright 2021"
__credits__ = list()
__license__ = "BSD"
__version__ = "0.1"
__maintainer__ = "Anton Höß"
__email__ = "anton.hoess42@gmail.com"
__status__ = "Development"


class TransformCanvas(tk.Canvas):
    """A canvas that can be scaled, rotated and translated.
    If no arguments are given, it behaves like a normal tk.Canvas.

    If not configured otherwise (using canvas.omit_draw), this canvas will call the drawing routine (using update())
    when the canvas gets resized or any of the parameters influencing the visualization (e.g. scaling) gets changed.

    To draw without any transformation (i.e. in pixels like normal) use the base canvas (see base property) and set
    the keyword no_trans=True when using create*().
    Example: self._canvas.base.create_line(x1[0], x1[1], x2[0], x2[1], dash=(3, 5), no_trans=True)

    If no rotation is used (which tk.Canvas does not support natively) the widgets can remain in place and manipulated
    in the drawing callback instead of deleting all of them before redrawing all anew. But if rotation is set,
    its mandatory to redraw all of them, since in this case they cannot be manipulated directly.

    All properties will get updated automatically when changing any of the influential parameters.
    But be aware that when binding co the <Configure> event, the canvas' width and height property will not be updated yet.
    In this case use canvas.winfo_width() and self.winfo_height() to get the canvas' width and height, respectively.

    There are many functions that have a transformation_matrix argument. This matrix needs to be of shape (3, 3). The
    easiest way to create such a matrix is to use the Matrix class.

    Parameters
    ----------
    master : tk.Misc
        The parent widget.
    scale_base : float, default 1.
        Base scale factor for all objects based to the origin. A value of 1. means the original size.
    scale_ratio : float, optional
        Defines the scale ratio (= width / height) that forces the view to keep this ratio
        when adjusting the content to its area.
    zoom_factor : float, default 1.
        Defines the zoom factor for zooming in or out one step.
    direction : str, default tk.SE
        Direction of positive x- and y-values. The default value of tk.SE means that the x value increases
        when going to the right and the y value when going down.
        Allowed values are tk.NE, v.SE, tk.SW and tk.NW.
    origin : str, default tk.NW
        Origin of the canvas. The default value of tk.NE means the top left corner (0, 0).
        Allowed values are tk.N, tk, NE, tk.E, tk.SE, tk.S,
        tk.SW, tk.W, tk.NW and tk.CENTER.
    offset : (int, int), default (0, 0)
        Offset in x- and y-direction in pixels. Useful to move the view in pixel coordinates.
    *args
        List of arguments passed to tk.Canvas.
    **kwargs
        Keyword arguments passed to tk.Canvas.
    """

    class ZoomDir(Enum):
        """Enumerates the zoom direction."""

        IN = 1
        OUT = 2
    # end class

    class MoveDir(Enum):
        """Enumerates the movement direction."""

        LEFT = 1
        RIGHT = 2
        UP = 3
        DOWN = 4
    # end class

    def __init__(self, master: tk.Misc, scale_base: float = 1., scale_ratio: Optional[float] = None,
                 zoom_factor: float = 1.1, direction: str = tk.SE, origin: str = tk.CENTER,
                 offset: Tuple[float, float] = (0., 0.), rotation: float = 0., *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        # Prerequisite
        self._is_init = False
        self._width = 0
        self._height = 0
        self._cb_draw = None

        # Save values - some values get set using their respective properties to use the checks built in there
        self.scale_base = scale_base
        self.scale_ratio = scale_ratio
        self.zoom_factor = zoom_factor
        self.direction = direction
        self.origin = origin
        self._offset = np.asarray(offset, dtype=np.float64)
        self._rotation = rotation

        # Useful for temporarily omit automatic drawing
        # (e.g. when doing multiple settings and only draw once at the end)
        self._omit_draw = False

        self._zoom_value = 1.  # Initial zoom factor
        self._transformation_matrix = None
        self._transformation_matrix_inv = None  # Store value to call the expensive matrix invsion only once

        # Private callbacks
        self._funcid_motion = None
        self._funcid_configure = None
        self._rebinding_private_cbs = False  # Used to prevent recursion
        self._rebind_private_cbs()

        # Update the values after saving all initial settings
        self._is_init = True
        self.update()
    # end def

    @property
    def width(self) -> int:
        """Returns the width (pixels) of the canvas widget.

        Returns
        -------
        width : int
            The width of the canvas.
        """

        return self._width
    # end def

    @property
    def height(self) -> int:
        """Returns the height (pixels) of the canvas widget.

        Returns
        -------
        height : int
            The height of the canvas.
        """

        return self._height
    # end def

    @property
    def pointer(self) -> Tuple[int, int]:
        """Returns the cursor position (x, y) in pixels relative to the widget's origin (0, 0).
        This value is not transformed in any way.

        Returns
        -------
        pointer : (int, int))
            The the cursor position.
        """

        x = self.winfo_pointerx() - self.winfo_rootx()
        y = self.winfo_pointery() - self.winfo_rooty()

        return x, y
    # end def

    @property
    def scale_base(self) -> float:
        """Returns the base scaling factor.

        Returns
        -------
        scale_base : float
            The base scaling factor.
        """

        return self._scale_base
    # end def

    @scale_base.setter
    def scale_base(self, value: float) -> None:
        """Returns the base scaling factor.
        If omit_draw is False, the drawing callback functions gets called.

        Parameters
        ----------
        value : float
            The base scaling factor.
        """

        if value == 0.:
            raise ValueError(f"The value ({value}) for scale_base needs to be != 0 (and usually > 0).")
        # end if

        self._scale_base = value
        self.update()
    # end def

    @property
    def scale_ratio(self) -> Optional[float]:
        """Returns the scale ratio. This value defines an additional scaling factor by fitting a virtual frame
        (with a width / height ratio of scale_ratio) into the canvas.
        In case the canvas has the same ratio as the given one, the scaling factor is 1 (= no scaling),
        otherwise the scaling factor will be < 1.
        A value of None disables the application of the scale ratio.

        Returns
        -------
        scale_ratio : float, optional
            The scale ratio.
        """

        ratio = 1.

        if self._scale_ratio:
            canvas_ratio = self.width / self.height
            ratio *= self._scale_ratio / canvas_ratio
        # end if

        return ratio
    # end def

    @scale_ratio.setter
    def scale_ratio(self, value: Optional[float]) -> None:
        """Sets the scale ratio. This value defines an additional scaling factor by fitting a virtual frame
        (with a width / height ratio of scale_ratio) into the canvas.
        In case the canvas has the same ratio as the given one, the scaling factor is 1 (= no scaling),
        otherwise the scaling factor will be < 1.
        A value of None disables the application of the scale ratio.
        If omit_draw is False, the drawing callback functions gets called.

        Parameters
        ----------
        value : float, optional
            The scale ratio.
        """

        if value and value <= 0.:
            raise ValueError(f"The value ({value}) for scale_ratio needs to be >0.")
        # end if

        self._scale_ratio = value
        self.update()
    # end def

    @property
    def zoom_factor(self) -> float:
        """Returns the current zoom factor. The zoom factor indicates with which value the zoom value is
        multiplied / divided when scrolling in the corresponding direction.

        Returns
        -------
        zoom_factor : str
            The zoom factor.
        """

        return self._zoom_factor
    # end def

    @zoom_factor.setter
    def zoom_factor(self, value: float) -> None:
        """Sets the current zoom factor. The zoom factor indicates with which value the zoom value is
        multiplied / divided when scrolling in the corresponding direction.
        If omit_draw is False, the drawing callback functions gets called.

        Parameters
        ----------
        value : str
            The zoom factor.
        """

        if value <= 0.:
            raise ValueError(f"The value ({value}) for zoom_factor needs to be > 0 (and usually > 1).")
        # end if

        self._zoom_factor = value
        self.update()
    # end def

    @property
    def zoom(self) -> float:
        """Sets the current zoom value.

        Returns
        -------
        zoom : str
            The zoom value.
        """

        return self._zoom_value
    # end def

    @zoom.setter
    def zoom(self, value: float) -> None:
        """Sets the current zoom value.
        If omit_draw is False, the drawing callback functions gets called.

        Parameters
        ----------
        value : str
            The zoom value.
        """

        self._zoom_value = value
        self.update()
    # end def

    @property
    def direction(self) -> str:
        """Returns the vector defining the direction of positive x- and y-values.
        A value of tk.SE e.g. means that the x value increases when going to the right
        and the y value when going down.

        Returns
        -------
        direction : str
            The direction string of the canvas.
        """

        return self._direction
    # end def

    @direction.setter
    def direction(self, value: str) -> None:
        """Sets the vector defining the direction of positive x- and y-values.
        A value of tk.SE e.g. means that the x value increases when going to the right
        and the y value when going down.
        If omit_draw is False, the drawing callback functions gets called.

        Parameters
        ----------
        value : str
            The direction string of the canvas.
        """

        self._get_direction_vector(value)  # Test the validity of the direction string
        self._direction = value
        self.update()
    # end def

    @property
    def origin(self) -> str:
        """Returns the origin string of the canvas. A value of tk.NE e.g. means the top left corner (0, 0).
        Allowed values are tk.N, tk, NE, tk.E, tk.SE, tk.S, tk.SW, tk.W, tk.NW and tk.CENTER.

        Returns
        -------
        origin : str
            The origin string of the canvas.
        """

        return self._origin
    # end def

    @origin.setter
    def origin(self, value: str) -> None:
        """Sets the origin string of the canvas. A value of tk.NE e.g. means the top left corner (0, 0).
        Allowed values are tk.N, tk, NE, tk.E, tk.SE, tk.S, tk.SW, tk.W, tk.NW and tk.CENTER.
        If omit_draw is False, the drawing callback functions gets called.

        Parameters
        ----------
        value : str
            The origin string of the canvas.
        """

        self._get_origin_vector(value)  # Test the validity of the origin string
        self._origin = value
        self.update()
    # end def

    @property
    def offset(self) -> Tuple[float, float]:
        """Returns the global translation offset.

        Returns
        -------
        offset : (float, float)
            The global translation offset (x, y).
        """

        return tuple(self._offset.tolist())
    # end def

    @offset.setter
    def offset(self, value: Tuple[Optional[float], Optional[float]]) -> None:
        """Sets the global translation offset (x, y).
        Each component can be set individually by setting the other component to None.
        If omit_draw is False, the drawing callback functions gets called.

        Parameters
        ----------
        value : (float (optional), float (optional))
            The global translation offset.
        """

        x = value[0] if value[0] else self._offset[0]
        y = value[1] if value[1] else self._offset[1]

        self._offset = np.asarray((x, y), dtype=np.float64)
        self.update()
    # end def

    @property
    def rotation(self) -> float:
        """Returns the global rotation angle (rad).

        Returns
        -------
        rotation : np.ndarray
            The global rotation angle (rad).
        """

        return self._rotation
    # end def

    @rotation.setter
    def rotation(self, value: float) -> None:
        """Sets the global rotation angle (rad). To have a defined value range, the angle is converted into a range from
        (-pi, pi).
        If omit_draw is False, the drawing callback functions gets called.

        Parameters
        ----------
        value : float
            The global rotation angle (rad).
        """

        rotation = (value + 2 * np.pi) % (2 * np.pi)
        rotation = rotation if rotation <= np.pi else -2 * np.pi + rotation
        self._rotation = rotation
        self.update()
    # end def

    @property
    def translation_vector(self) -> np.ndarray:
        """Returns the global translation vector (x, y).

        Returns
        -------
        translation_vector : np.ndarray
            The global translation vector (x, y).
        """

        return self._v_translate()
    # end def

    @property
    def scaling_vector(self) -> np.ndarray:
        """Returns the global scaling vector (x, y).

        Returns
        -------
        scaling_vector : np.ndarray
            The global scaling vector (x, y).
        """

        return self._v_scale()
    # end def

    @property
    def transformation_matrix(self) -> np.ndarray:
        """Returns the global transformation matrix.

        Returns
        -------
        transformation_matrix : np.ndarray
            The global transformation matrix.
        """

        return self._transformation_matrix
    # end def

    @property
    def transformation_matrix_inv(self) -> np.ndarray:
        """Returns the inverted global transformation matrix.

        Returns
        -------
        transformation_matrix_inv : np.ndarray
            The inverted global transformation matrix.
        """

        return self._transformation_matrix_inv
    # end def

    @property
    def cb_draw(self) -> Optional[Callable]:
        """Returns if the drawing callback from user space.

        Returns
        -------
        cb_draw : callable, optional
            The drawing callback.
        """

        return self._cb_draw
    # end def

    @cb_draw.setter
    def cb_draw(self, value: Optional[Callable]) -> None:
        """Sets the drawing callback from user space. If value is None, the callback gets removed.
        The callback can also get changed at any time.
        This callback will be called automatically (if omit_draw is False) and
        can also me manually triggered by calling update().
        Hint: update() needs to be called manually after settings this to immediately update the canvas.

        Parameters
        ----------
        value : callable, optional
            The drawing callback.
        """

        if value and not callable(value):
            raise ValueError(f"The value ({value}) for cb_draw is not a callable.")
        # end if

        self._cb_draw = value
        # Here we don't update, since it may be that this gets called
        # before all other widgets besides this one are created.
    # end def

    @property
    def omit_draw(self) -> bool:
        """Returns if the automatic redrawing of the canvas is disabled.

        Returns
        -------
        omit_draw : bool
            If True, the automatic redrawing of the canvas is disabled (until it gets set to False again),
            otherwise it is enabled (default).
        """

        return self._omit_draw
    # end def

    @omit_draw.setter
    def omit_draw(self, value: bool) -> None:
        """Sets the flag the determines if there should be triggered any automatic redrawing of the canvas.

        Parameters
        ----------
        value : bool
            If True, the automatic redrawing of the canvas gets disabled (until it gets set to False again),
            otherwise it gets enabled (default).
        """

        self._omit_draw = value
    # end def

    @property
    def base(self) -> tk.Canvas:
        """Returns the underlying tk.Canvas. This allows for drawing without any transformation

        Returns
        -------
        base_canvas : tk.Canvas
            The base canvas.
        """

        return super()
    # end def

    def create_line(self, *args, transformation_matrix: Optional[np.ndarray] = None, **kwargs):
        """Create line with coordinates x1, y1, ..., xn, yn.
        See tk.Canvas.create_line() besides the additional functionality added (see below).

        Parameters
        ----------
        transformation_matrix : np.ndarray, default None
            Local transformation matrix applied to the object before applying the global transformation matrix.
        *args
            List of arguments passed to tk.Canvas.create_oval.
        **kwargs
            Keyword arguments passed to tk.Canvas.create_oval.
        """

        # Check transformation matrix for validity
        if transformation_matrix is not None:
            self.transformation_matrix_is_valid(transformation_matrix)
        # end if

        if self._rotation != 0 or transformation_matrix is not None:
            # Local transformation
            if transformation_matrix is not None:
                args = self.transform_coords(args, matrix=transformation_matrix)

            # Global transformation
            args = self.transform_coords(args)
        # end if

        return super().create_line(*args, **kwargs)
    # end def

    def create_oval(self, *args, n_segments: Optional[int] = 100, transformation_matrix: Optional[np.ndarray] = None, **kwargs):
        """Create oval with coordinates x1, y1, x2, y2.
        See tk.Canvas.create_oval() besides the additional functionality added (see below).

        Parameters
        ----------
        n_segments : int, default 100
            Number of line segments to approximate the oval using a polygon.
            For symmetric shapes this number should be divisible by 4 to produce a symmetric shape.
        transformation_matrix : np.ndarray, default None
            Local transformation matrix applied to the object before applying the global transformation matrix.
        *args
            List of arguments passed to tk.Canvas.create_oval.
        **kwargs
            Keyword arguments passed to tk.Canvas.create_oval.
        """

        # Check transformation matrix for validity
        if transformation_matrix is not None:
            self.transformation_matrix_is_valid(transformation_matrix)
        # end if

        if self._rotation != 0 or transformation_matrix is not None:
            x1, y1, x2, y2 = args
            r1 = (x2 - x1) / 2
            r2 = (y2 - y1) / 2
            center = x1 + r1, y1 + r2

            # Adapted from https://stackoverflow.com/questions/22694850/approximating-an-ellipse-with-a-polygon
            # I've removed Nth point calculation, that involves indefinite Tan(Pi/2)
            # It would better to assign known value 0 to Fi in this point
            args = list()
            for i in range(0, n_segments):
                _theta = 2 * math.pi * i / n_segments
                if r1 != r2:
                    phi = math.atan(math.tan(_theta) * math.sqrt(r2 / r1))
                    phi += math.pi * int(np.cos(_theta) < 0)  # Compensate for atan (instead of atan2)
                else:
                    phi = _theta
                # end if
                _x = r1 * math.cos(phi)
                _y = r2 * math.sin(phi)
                args.append(_x)
                args.append(_y)
            # end for

            # Local transformation
            if transformation_matrix is not None:
                args = self.transform_coords(args, matrix=Matrix().translate(*center))

            # Local transformation
            if transformation_matrix is not None:
                args = self.transform_coords(args, matrix=transformation_matrix)

            # Global transformation
            args = self.transform_coords(args)

            return super().create_polygon(*args, **kwargs)

        else:
            return super().create_oval(*args, **kwargs)
        # end if
    # end def

    def create_polygon(self, *args, transformation_matrix: Optional[np.ndarray] = None, **kwargs):
        """Create polygon with coordinates x1, y1, ..., xn, yn.
        See tk.Canvas.create_polygon() besides the additional functionality added (see below).

        Parameters
        ----------
        transformation_matrix : np.ndarray, default None
            Local transformation matrix applied to the object before applying the global transformation matrix.
        *args
            List of arguments passed to tk.Canvas.create_oval.
        **kwargs
            Keyword arguments passed to tk.Canvas.create_oval.
        """

        # Check transformation matrix for validity
        if transformation_matrix is not None:
            self.transformation_matrix_is_valid(transformation_matrix)
        # end if

        if self._rotation != 0 or transformation_matrix is not None:
            # Local transformation
            if transformation_matrix is not None:
                args = self.transform_coords(args, matrix=transformation_matrix)

            # Global transformation
            args = self.transform_coords(args)
        # end if

        return super().create_polygon(*args, **kwargs)
    # end def

    def create_rectangle(self, *args, transformation_matrix: Optional[np.ndarray] = None, **kwargs):
        """Create rectangle with coordinates x1, y1, x2, y2.
        See tk.Canvas.create_rectangle() besides the additional functionality added (see below).

        Parameters
        ----------
        transformation_matrix : np.ndarray, default None
            Local transformation matrix applied to the object before applying the global transformation matrix.
        *args
            List of arguments passed to tk.Canvas.create_oval.
        **kwargs
            Keyword arguments passed to tk.Canvas.create_oval.
        """

        # Check transformation matrix for validity
        if transformation_matrix is not None:
            self.transformation_matrix_is_valid(transformation_matrix)
        # end if

        if self._rotation != 0 or transformation_matrix is not None:
            p0 = args[:2]
            p1 = args[2:4]
            args = [p0[0], p0[1],
                    p1[0], p0[1],
                    p1[0], p1[1],
                    p0[0], p1[1]]

            # Local transformation
            if transformation_matrix is not None:
                args = self.transform_coords(args, matrix=transformation_matrix)

            # Global transformation
            args = self.transform_coords(args)

            return super().create_polygon(*args, **kwargs)

        else:
            return super().create_rectangle(*args, **kwargs)
        # end if
    # end def

    def create_text(self, *args, **kwargs):
        """Create text with coordinates x1, y1.
        See tk.Canvas.create_text() besides the additional functionality added (see below).
        """

        if self._rotation != 0:
            angle = 0
            if "angle" in kwargs:
                angle = kwargs["angle"]
            # end if

            angle += self.rotation / math.pi * 180.
            kwargs["angle"] = angle

            # Global transformation
            args = self.transform_coords(args)
        # end if

        return super().create_text(*args, **kwargs)
    # end def

    @staticmethod
    def transformation_matrix_is_valid(transformation_matrix: np.ndarray) -> None:
        """Checks a given transformation matrix for validity. Raises different Exceptions messages for different errors.

        Parameters
        ----------
        transformation_matrix : np.ndarray
            Transformation matrix to check.

        Returns
        -------
        valid: bool
            Indicates if the matrix is valid.
        """

        if transformation_matrix.shape != (3, 3):
            raise ValueError(f"The transformation matrix does not have the correct shape"
                             f"({transformation_matrix.shape} instead of (3, 3)).")

    # end def

    def transform_point(self, x: float, y: float, inv: Optional[bool] = False) -> Tuple[float, float]:
        """Transforms a given point from custom space -> pixel space by applying the current transformations.
        If the parameter inv is set, the direction inverts.

        Parameters
        ----------
        x : float
            Point's x-coordinate.
        y : float
            Point's y-coordinate.
        inv : bool, default False
            Inverse conversion direction to pixel space -> custom space.

        Returns
        -------
        p_trans : (float, float)
            The x- and y-coordinate of the scaled point.
        """

        p = self._transform_point(p=np.asarray([x, y], dtype=np.float64), inv=inv)

        return tuple(p.tolist())
    # end def

    def transform_coords(self, coords, inv: Optional[bool] = False, matrix: Optional[np.ndarray] = None) -> List[float]:
        """Transforms a list of coordinates x1, y1, ..., xn, yn from custom space -> pixel space.
        If no arguments are given, it behaves like a normal tk.Canvas.

        Parameters
        ----------
        *coords
            List of arguments to convert.
        inv : bool, default False
            Inverse conversion direction to pixel space -> custom space.
        matrix : np.ndarray, default None
            Transformation matrix. If not set, the internal matrix is used.
        """

        if len(coords) % 2 != 0:
            raise ValueError(f"Number of arguments ({len(coords)}) is not a multiple of two.")
        # end if

        # Get point tuples
        pos = zip(coords[0::2], coords[1::2])

        # Transform points
        m = matrix if matrix is not None else self.transformation_matrix if not inv else self.transformation_matrix_inv
        pos_trans = [(m @ np.append(p, 1)).tolist()[:2] for p in pos]

        # Return flattened list
        return [coord for pos in pos_trans for coord in pos]
    # end def

    def zoom_in(self) -> None:
        """Zooms in to make objects appear larger. The zoom center is the current mouse cursor position or the
        center of the canvas if the cursor is outside the canvas."""

        self._zoom(TransformCanvas.ZoomDir.IN)
    # end def

    def zoom_out(self) -> None:
        """Zooms out to make objects appear smaller. The zoom center is the current mouse cursor position or the
        center of the canvas if the cursor is outside the canvas."""

        self._zoom(TransformCanvas.ZoomDir.OUT)
    # end def

    def update(self):
        """Updates the transformation matrix and draws the transformed scene to the canvas."""

        if self._is_init:
            self._update_canvas_dimensions()
            self._update_transformation_matrix()

            if self._cb_draw and not self._omit_draw:
                self._cb_draw()
            # end if
        # end if
    # end def

    def bind_class(self, class_name, sequence=None, func=None, add=None):
        """See tk.Canvas.bind_class() documentation.
        Also handles the private callbacks necessary for this class.
        """

        funcid = super().bind_class(class_name, sequence, func, add)
        self._rebind_private_cbs()

        return funcid
    # end def

    def unbind(self, sequence, funcid=None):
        """See tk.Canvas.unbind() documentation.
        Also handles the private callbacks necessary for this class.
        This is a fix, due to the still unfixed error in tkinter.Misc.unbind().
        """

        if not funcid:
            self.tk.call('bind', self._w, sequence, '')
            return
        # end if

        func_callbacks = self.tk.call('bind', self._w, sequence, None).split('\n')
        new_callbacks = [cb for cb in func_callbacks if cb[6:6 + len(funcid)] != funcid]
        self.tk.call('bind', self._w, sequence, '\n'.join(new_callbacks))
        self.deletecommand(funcid)

        self._rebind_private_cbs()
    # end def

    def unbind_all(self, sequence):
        """See tk.Canvas.unbind_all() documentation.
        Also handles the private callbacks necessary for this class.
        """

        super().unbind_all(sequence)
        self._rebind_private_cbs()
    # end def

    def unbind_class(self, class_name, sequence):
        """See tk.Canvas.unbind_class() documentation.
        Also handles the private callbacks necessary for this class.
        """

        super().unbind_class(class_name, sequence)
        self._rebind_private_cbs()
    # end def

    def _get_origin_vector(self, origin: str) -> np.ndarray:
        """Returns the vector defining the coordinate system's origin.

        Parameters
        ----------
        origin : str
            Origin of the canvas. A value of tk.NE e.g. means the top left corner (0, 0).
            Allowed values are tk.N, tk, NE, tk.E, tk.SE, tk.S,
            tk.SW, tk.W, tk.NW and tk.CENTER.

        Returns
        -------
        v_origin : np.ndarray
            Origin vector.
        """

        valid_origins = (tk.N, tk.NE, tk.E, tk.SE, tk.S, tk.SW, tk.W, tk.NW, tk.CENTER)
        if origin not in valid_origins:
            raise ValueError(f"Parameter origin ({origin}) not in {valid_origins}")
        # end if

        x, y = None, None

        if origin == tk.N:
            x, y = int(self.width / 2), 0

        elif origin == tk.NE:
            x, y = self.width, 0

        elif origin == tk.E:
            x, y = self.width, int(self.height / 2)

        elif origin == tk.SE:
            x, y = self.width, self.height

        elif origin == tk.S:
            x, y = int(self.width / 2), self.height

        elif origin == tk.SW:
            x, y = 0, self.height

        elif origin == tk.W:
            x, y = 0, int(self.height / 2)

        elif origin == tk.NW:
            x, y = 0, 0

        elif origin == tk.CENTER:
            x, y = int(self.width / 2), int(self.height / 2)
        # end if

        return np.asarray([x, y], dtype=np.float64)
    # end def

    @staticmethod
    def _get_direction_vector(direction: str) -> np.ndarray:
        """Returns the vector defining the direction of positive x- and y-values.
        A value of tk.SE e.g. means that the x value increases when going to the right
        and the y value when going down.

        Parameters
        ----------
        direction : str
            Direction. Allowed values are tk.NE, tk.SE, tk.SW and tk.NW.

        Returns
        -------
        v_direction : np.ndarray
            Direction vector.
        """

        valid_directions = (tk.NE, tk.SE, tk.SW, tk.NW)
        if direction not in valid_directions:
            raise ValueError(f"Parameter direction ({direction}) not in {valid_directions}")
        # end if

        x = None
        y = None

        if direction == tk.NE:
            x, y = 1, -1

        elif direction == tk.SE:
            x, y = 1, 1

        elif direction == tk.SW:
            x, y = -1, 1

        elif direction == tk.NW:
            x, y = -1, -1
        # end if

        return np.asarray([x, y], dtype=np.float64)
    # end def

    def _zoom(self, zoom_dir: ZoomDir) -> None:
        """Zooms in/out to make objects appear larger/smaller. The zoom center is the current mouse cursor position
        or the center of the canvas if the cursor is outside the canvas.

        ZoCreates an oval shape (by using a polygon).

        Parameters
        ----------
        zoom_dir : ZoomDir
            Zoom direction (in or out).
        """

        self.omit_draw = True

        # Zoom
        zoom_factor_update = self._zoom_factor if zoom_dir is TransformCanvas.ZoomDir.IN else 1. / self._zoom_factor
        self.zoom *= zoom_factor_update
        zoom_factor_diff = abs(zoom_factor_update - 1)

        # Zoom center around the canvas origin if cursor is outside of the canvas.
        # This can happen, if the cursor is outside the widget and the zoom is triggered e.g. by keyboard.
        pointer_x, pointer_y = self.pointer

        if not 0 <= pointer_x < self.width or not 0 <= pointer_y < self.height:
            pointer_x = self.width / 2.
            pointer_y = self.height / 2.
        # end if

        pointer = np.asarray([pointer_x, pointer_y], dtype=np.float64)
        origin = self._get_origin_vector(self._origin)

        # Adapt the offset
        _zoom_dir = -1. if zoom_dir is TransformCanvas.ZoomDir.IN else 1.
        self.offset += (pointer - (self._offset + origin)) * zoom_factor_diff * _zoom_dir

        self._omit_draw = False
        self.update()
    # end def

    def _v_scale(self) -> np.ndarray:
        """Calculates the current scaling vector.

        Returns
        -------
        v_scale : np.ndarray
            Scaling vector.
        """

        v = np.ones(2, dtype=np.float64)

        # Scale base
        v *= self.scale_base

        # Scale ratio
        v *= self.scale_ratio

        # Zoom
        v *= self.zoom

        # Direction
        v *= self._get_direction_vector(self.direction)

        return v
    # end def

    def _v_translate(self) -> np.ndarray:
        """Calculates the current translation vector.

        Returns
        -------
        v_translate : np.ndarray
            Translation vector.
        """

        v = np.zeros(2, dtype=np.float64)

        # Origin
        v += self._get_origin_vector(origin=self.origin)

        # Offset
        v += self.offset

        return v
    # end def

    def _m_scale(self) -> np.ndarray:
        """Calculates the current scaling matrix.

        Returns
        -------
        m_scale : np.ndarray
            Scaling matrix.
        """

        v = self._v_scale()

        m = np.eye(3, dtype=np.float64)
        m[0, 0] = v[0]
        m[1, 1] = v[1]

        return m
    # end def

    def _m_rotate(self) -> np.ndarray:
        """Calculates the current rotation matrix.

        Returns
        -------
        m_rotate : np.ndarray
            Rotation matrix.
        """

        # Negate the rotation value to rotate in mathematical sense
        m = np.asarray([[np.cos(-self._rotation), -np.sin(-self._rotation), 0],
                        [np.sin(-self._rotation), np.cos(-self._rotation), 0],
                        [0, 0, 1]], dtype=np.float64)

        return m
    # end def

    def _m_translate(self) -> np.ndarray:
        """Calculates the current translation matrix.

        Returns
        -------
        m_translate : np.ndarray
            Translation matrix.
        """

        v = self._v_translate()

        m = np.eye(3, dtype=np.float64)
        m[0, 2] = v[0]
        m[1, 2] = v[1]

        return m
    # end def

    def _update_transformation_matrix(self):
        """Recalculates the transformation matrix."""

        # The function is in reverse order due to the matrix calculation rules.
        self._transformation_matrix = self._m_translate() @ self._m_rotate() @ self._m_scale()  # S x R x T
        self._transformation_matrix_inv = np.linalg.inv(self._transformation_matrix)
    # end def

    def _transform_point(self, p: np.ndarray, inv: Optional[bool] = False) -> np.ndarray:
        """Transforms the given point from custom space -> pixel space
        using the current transformation matrices and vectors.

        Parameters
        ----------
        p : np.ndarray
            Point to transform
        inv : bool, default False
            Inverse conversion direction to pixel space -> custom space.

        Returns
        -------
        p_trans : np.ndarray
            Transformed point.
        """

        p = np.append(p, 1)  # Add a 1 to make the vector of length 3 to match with the matrix size.

        if not inv:
            # Without rotation it would be like the following command
            # p -= self._v_translate()
            # p /= self._v_scale()
            p = self.transformation_matrix_inv @ p
        else:
            p = self.transformation_matrix @ p
        # end if

        return p[:2]
    # end def

    def _create(self, item_type, args, kwargs) -> int:
        """Applies current transformations after using the tk.Canvas._create() function
        to transform the object's points.

        Parameters
        ----------
        *args
            Arguments passed to tk.Canvas._create().
        **kwargs
            Keyword arguments passed to tk.Canvas._create().

        Returns
        -------
        object_id : int
            The handle of the created object.
        """

        trans = not kwargs.pop("no_trans", False)
        x = super()._create(item_type, args, kwargs)

        # Don't apply transformation when explicitly disabled.
        if trans:
            # Transform object - used if there's no rotation, to use the original function
            if self._rotation == 0:
                self.scale(x, 0, 0, *self._v_scale().tolist())
                self.move(x, *self._v_translate().tolist())
            # end if
        # end if

        return x
    # end def

    def _rebind_private_cbs(self):
        """Unbinds and bins anew the private event callbacks necessary."""

        if self._rebinding_private_cbs:
            return

        self._rebinding_private_cbs = True

        self.unbind("<Motion>", self._funcid_motion)
        self._funcid_motion = self.bind("<Motion>", self._cb_motion, add="+")
        self.unbind("<Configure>", self._funcid_configure)
        self._funcid_configure = self.bind("<Configure>", self._cb_configure, add="+")

        self._rebinding_private_cbs = False
    # end def

    def _bind(self, what, sequence, func, add, needcleanup=1):
        """See tk.Canvas._bind() documentation.
        Also handles the private callbacks necessary for this class.
        """

        funcid = super()._bind(what, sequence, func, add, needcleanup)
        self._rebind_private_cbs()

        return funcid
    # end def

    def _update_canvas_dimensions(self):
        """Updates the canvas' dimensions."""

        self._width = self.winfo_width()
        self._height = self.winfo_height()
    # end def

    def _cb_configure(self, _event: tk.Event) -> None:
        """Callback that handles the configure event and stores the canvas' current dimensions.

        Parameters
        ----------
        _event : tk.Event
            The event information. Not used.
        """

        self._update_canvas_dimensions()
        self.update()
    # end def

    def _cb_motion(self, event: tk.Event) -> None:
        """Callback that handles the mouse move event, transforms the coordinates and call the user defined callback
        with these scales coordinates.

        Parameters
        ----------
        event : tk.Event
            The event information.
        """

        x, y = self.transform_point(getattr(event, "x"), getattr(event, "y"))

        # Unfortunately we cannot modify event, so we need to create a minimalistic new one
        e = {
            'x': x,
            'y': y
        }

        # We only need to update x and y, since all other values of event are automatically generated.
        # It's not possible to add new key-names
        self.event_generate("<<MotionScaled>>", **e)
    # end def
# end class


class Matrix(np.ndarray):
    """A transformation matrix used to transform the points of the objects created on TransformCanvas.
    This is essentially a np.ndarray with some additional functions to modify the matrix.
    In its standard form its an identity matrix. The modification functions can be concatenated like this:
    Matrix().translate(5, 7).rotate(math.pi).
    """

    def __new__(cls):
        return np.eye(3, dtype=np.float64).view(cls)
    # end def

    def translate(self, x: float, y: float) -> Matrix:
        """Translates (moves) the object by the given amount on each axis.

        Parameters
        ----------
        x : float
            Translation on x axis.
        y : float
            Translation on y axis.

        Returns
        -------
        self: Matrix
            The Matrix itself after applying the translation.
        """

        m = np.eye(3, dtype=np.float64)
        m[0, 2] = x
        m[1, 2] = y

        return self @ m
    # end def

    def scale(self, x: float, y: float, origin: Optional[Tuple[float, float]] = None) -> Matrix:
        """Scales the object by the given factor each dimension.

        Parameters
        ----------
        x : float
            Scaling factor on x axis.
        y : float
            Scaling factor on y axis.
        origin : np.ndarray, optional
            If provided, the scaling happens around 'origin' instead of (0, 0).

        Returns
        -------
        self: Matrix
            The Matrix itself after applying the scaling.
        """

        m = np.eye(3, dtype=np.float64)
        m[0, 0] = x
        m[1, 1] = y

        if origin:
            origin = np.asarray(origin)
            m = Matrix().translate(*origin) @ m @ Matrix().translate(*(-origin))
        # end if

        return self @ m
    # end def

    def rotate(self, angle: float, origin: Optional[Tuple[float, float]] = None) -> Matrix:
        """Rotates the object by the given angle counterclockwise (= in the mathematical sense).

        Parameters
        ----------
        angle : float
            Angle (in degrees) to rotate.
        origin : np.ndarray, optional
            If provided, the rotation happens around 'origin' instead of (0, 0).

        Returns
        -------
        self: Matrix
            The Matrix itself after applying the scaling.
        """
        m = np.asarray([[np.cos(angle), -np.sin(angle), 0],
                        [np.sin(angle), np.cos(angle), 0],
                        [0, 0, 1]], dtype=np.float64)

        if origin:
            origin = np.asarray(origin)
            m = Matrix().translate(*origin) @ m @ Matrix().translate(*(-origin))
        # end if

        return self @ m
    # end def

    def skew(self, angle_x: float = 0, angle_y: float = 0) -> Matrix:
        """Skews the object by the given angles along each axis.

        Parameters
        ----------
        angle_x : float
            Angle (in degrees) to skew along the x axis.
        angle_y : float
            Angle (in degrees) to skew along the y axis.

        Returns
        -------
        self: Matrix
            The Matrix itself after applying the translation.
        """

        m = np.eye(3, dtype=np.float64)
        m[0, 1] = np.tan(angle_x / 180. * np.pi)
        m[1, 0] = np.tan(angle_y / 180. * np.pi)

        return self @ m
    # end def
# end class