from typing import Optional
import tkinter as tk
import math
import numpy as np

from transform_canvas import TransformCanvas, Matrix

"""This module provides an example on how to use the TransformCanvas."""

__author__ = "Anton Höß"
__copyright__ = "Copyright 2021"


class TransformCanvasTest:
    """Test class for TransformCanvas. Draws some objects of the canvas ans allows to transform the canvas.

    Parameters
    ----------
    width : int
        Initial width of the canvas in pixels.
    height : int
        Initial height of the canvas in pixels.
    """

    def __init__(self, width: int, height: int):
        # For shift the objects on the canvas
        self._move_origin = [-1, -1]
        self._move_origin_canvas = [-1, -1]
        self._move_mode = False

        # For scaling the objects on the canvas
        self._zoom_origin = None
        self._zoom_canvas = None
        self._zoom_mode = False

        # For rotating the objects on the canvas
        self._rotation = None
        self._rotation_canvas = None
        self._rotation_mode = False

        # Main window
        self._root = tk.Tk()
        self._root.title("TransformCanvas Test")

        # Canvas
        self._canvas = TransformCanvas(self._root, width=width, height=height, scale_base=2., scale_ratio=None,
                                       zoom_factor=1.1, direction=tk.NE, origin=tk.CENTER, offset=(150, -200),
                                       rotation=math.pi*2)
        self._canvas.cb_draw = self._draw
        self._canvas.pack(expand=True, fill=tk.BOTH)
        self._canvas.bind('<MouseWheel>', self._cb_mouse_wheel)  # With Windows OS
        self._canvas.bind('<Button-4>', self._cb_mouse_wheel)  # With Linux OS
        self._canvas.bind('<Button-5>', self._cb_mouse_wheel)  # "
        self._canvas.bind('<Motion>', self._cb_motion)
        self._canvas.bind('<<MotionScaled>>', self._cb_motion_scaled)
        self._canvas.bind('<Shift-Button-1>', self._cb_shift_left_click)
        self._canvas.bind('<B1-Shift-Motion>', self._cb_shift_motion)
        self._canvas.bind('<Control-Button-1>', self._cb_control_left_click)
        self._canvas.bind('<B1-Control-Motion>', self._cb_control_motion)
        self._canvas.bind('<Alt-Button-1>', self._cb_alt_left_click)
        self._canvas.bind('<B1-Alt-Motion>', self._cb_alt_motion)
        self._canvas.bind('<ButtonRelease-1>', self._cb_left_click_release)
        self._canvas.bind_all('<Control-plus>', lambda event: self._do_zoom(TransformCanvas.ZoomDir.IN))
        self._canvas.bind_all('<Control-minus>', lambda event: self._do_zoom(TransformCanvas.ZoomDir.OUT))
        self._canvas.bind_all('<Control-Left>', lambda event: self._do_move(TransformCanvas.MoveDir.LEFT))
        self._canvas.bind_all('<Control-Right>', lambda event: self._do_move(TransformCanvas.MoveDir.RIGHT))
        self._canvas.bind_all('<Control-Up>', lambda event: self._do_move(TransformCanvas.MoveDir.UP))
        self._canvas.bind_all('<Control-Down>', lambda event: self._do_move(TransformCanvas.MoveDir.DOWN))

        # Some elements showing interesting values
        self._lbl_cursor_pos_ori = tk.Label(self._root)
        self._lbl_cursor_pos_ori.pack(expand=False, fill=tk.NONE)

        self._lbl_cursor_pos_ori_retrans = tk.Label(self._root)
        self._lbl_cursor_pos_ori_retrans.pack(expand=False, fill=tk.NONE)

        self._lbl_cursor_pos_trans = tk.Label(self._root)
        self._lbl_cursor_pos_trans.pack(expand=False, fill=tk.NONE)

        self._lbl_trans_matrix = tk.Label(self._root)
        self._lbl_trans_matrix.pack(expand=False, fill=tk.NONE)

        self._lbl_trans_rotation = tk.Label(self._root)
        self._lbl_trans_rotation.pack(expand=False, fill=tk.NONE)

        # Main loop
        self._root.mainloop()
    # end def

    @staticmethod
    def _seg_intersect(a1: np.ndarray, a2: np.ndarray, b1: np.ndarray, b2: np.ndarray) -> Optional[np.ndarray]:
        """Calculate line segment intersection using vectors.
        Line segment a given by endpoints a1, a2.
        Line segment b given by endpoints b1, b2.

        Parameters
        ----------
        a1 : np.ndarray
            Point a1.
        a2 : np.ndarray
            Point a2.
        b1 : np.ndarray
            Point b1.
        b2 : np.ndarray
            Point b2.
        """

        def perpendicular(a):
            """ Returns a perpendicular version of the given vector."""

            b = np.empty_like(a)
            b[0] = -a[1]
            b[1] = a[0]

            return b
        # end def

        da = a2 - a1
        db = b2 - b1
        dp = a1 - b1
        dap = perpendicular(da)
        denominator = np.dot(dap, db)

        if denominator == 0:
            return None
        else:
            num = np.dot(dap, dp)
            return (num / denominator.astype(float)) * db + b1
        # end if
    # end def

    def _draw(self):
        """Draws the scene."""

        self._lbl_trans_matrix["text"] = str(self._canvas.transformation_matrix)
        self._lbl_trans_rotation["text"] = f"{self._canvas.rotation:.02f} " \
                                           f"({self._canvas.rotation / math.pi * 180.:.02f})"

        self._canvas.delete("all")

        matrix = np.asarray(
            [[2, 1, 0],
             [0, 2, 0],
             [0, 0, 2]])

        matrix = Matrix().translate(5, 7).rotate(1 * math.pi)
        matrix = Matrix().translate(25, 15).rotate(math.pi / 4).translate(-25, -15)
        matrix = Matrix().translate(-25, -15)
        matrix = Matrix().rotate(angle=math.pi / 4, origin=(25, 15))
        matrix = Matrix().scale(5, 5, origin=(25, 15))
        matrix = Matrix()
        matrix = Matrix().skew(0, 30)
        self._canvas.create_rectangle(10, 10, 40, 20, fill="light gray", outline="gray", transformation_matrix=matrix)
        self._canvas.create_polygon(-10, -10, -15, 20, 10, -30, fill="red", outline="dark red")
        self._canvas.create_oval(-10, -10, 200, 20, fill="black", outline="blue", transformation_matrix=Matrix().
                                 rotate(angle=.1), n_segments=50)
        self._canvas.create_line(0, 0, 20, 10, width=2, fill="blue")
        self._canvas.create_line(0, 0, 20, 0)
        self._canvas.create_text(50, 50, text="This is a rotation test", angle=10.)

        # Draw a coordinate system cross. Since there is no intersection in case the border line and the axis line
        # are parallel, the border lines need to be swapped at a certain point (see below).

        # Prepare some shortcuts
        ti = lambda x, y: self._canvas.transform_point(x, y, inv=True)
        r = self._canvas.rotation
        ox, oy = ti(0, 0)  # Origin
        w, h = self._canvas.width, self._canvas.height

        # Prepare border lines
        left_border = np.asarray([0, 0]), np.asarray([0, h])
        right_border = np.asarray([w, 0]), np.asarray([w, h])
        top_border = np.asarray([0, 0]), np.asarray([w, 0])
        bottom_border = np.asarray([0, h]), np.asarray([w, h])

        # If the rotation angle is more than 45° away from the perpendicular state to the border lines,
        # switch the horizontal and vertical lines
        if not (-math.pi / 4 < r < math.pi / 4 or r > math.pi * 3 / 4 or r < -math.pi * 3 / 4):
            left_border, right_border, top_border, bottom_border = top_border, bottom_border, left_border, right_border
        # end if

        # Calculate and draw x axis
        x1 = self._seg_intersect(np.asarray([ox, oy]), np.asarray([ox + math.cos(r), oy - math.sin(r)]),
                                 *left_border)

        x2 = self._seg_intersect(np.asarray([ox, oy]), np.asarray([ox + math.cos(r), oy - math.sin(r)]),
                                 *right_border)

        self._canvas.base.create_line(x1[0], x1[1], x2[0], x2[1], dash=(5, 8), width=1, no_trans=True)

        # Calculate and draw y axis
        x1 = self._seg_intersect(np.asarray([ox, oy]), np.asarray([ox - math.sin(r), oy - math.cos(r)]),
                                 *top_border)

        x2 = self._seg_intersect(np.asarray([ox, oy]), np.asarray([ox - math.sin(r), oy - math.cos(r)]),
                                 *bottom_border)

        self._canvas.base.create_line(x1[0], x1[1], x2[0], x2[1], dash=(3, 5), no_trans=True)
    # end def

    def _do_zoom(self, zoom_dir: Optional[TransformCanvas.ZoomDir] = None):
        """Zooms the drawing canvas.

        Parameters
        ----------
        zoom_dir : Gui.ZoomDir
            Zoom direction.
        """

        if zoom_dir == TransformCanvas.ZoomDir.IN:
            self._canvas.zoom_in()
        else:
            self._canvas.zoom_out()
        # end if
    # end def

    def _do_move(self, direction: Optional[TransformCanvas.MoveDir] = None):
        """Callback that moves the canvas in the given direction.

        Parameters
        ----------
        direction : Gui.MoveDir
            Moving direction.
        """

        offset_x, offset_y = self._canvas.offset

        if direction == TransformCanvas.MoveDir.LEFT:
            self._canvas.offset = offset_x - self._canvas.width / 10., offset_y

        elif direction == TransformCanvas.MoveDir.RIGHT:
            self._canvas.offset = offset_x + self._canvas.width / 10., offset_y

        elif direction == TransformCanvas.MoveDir.UP:
            self._canvas.offset = offset_x, offset_y - self._canvas.height / 10.

        elif direction == TransformCanvas.MoveDir.DOWN:
            self._canvas.offset = offset_x, offset_y + self._canvas.height / 10.

        else:
            raise Exception("Invalid movement direction.")
        # end if
    # end def

    def _cb_mouse_wheel(self, event: tk.Event):
        """Callback that handles the mouse wheel event.

        Parameters
        ----------
        event : tk.Event, optional
            Event information.

        Returns
        -------
        str
            Indicates if the event shall be propagated further. "break" means not propagate it further.
        """

        # Respond to Linux or Windows wheel event
        if getattr(event, "num") == 4 or getattr(event, "delta") == 120:
            self._do_zoom(TransformCanvas.ZoomDir.IN)

        elif getattr(event, "num") == 5 or getattr(event, "delta") == -120:
            self._do_zoom(TransformCanvas.ZoomDir.OUT)
        # end if

        return "break"
    # end def

    def _cb_shift_left_click(self, event: tk.Event):
        """Callback that enters the move (translate) mode.

        Parameters
        ----------
        event : tk.Event, optional
            Event information.
        """

        self._move_origin = [getattr(event, "x"), getattr(event, "y")]
        self._move_origin_canvas = self._canvas.offset
        self._move_mode = True
    # end def

    def _cb_shift_motion(self, event: tk.Event):
        """Callback that moves (translates) in the move mode.

        Parameters
        ----------
        event : tk.Event, optional
            Event information.
        """

        if self._move_mode:
            self._canvas.offset = (self._move_origin_canvas[0] + (getattr(event, "x") - self._move_origin[0]),
                                   self._move_origin_canvas[1] + (getattr(event, "y") - self._move_origin[1]))
        # end if
    # end def

    def _cb_control_left_click(self, event: tk.Event):
        """Callback that enters the zoom (scaling) mode.

        Parameters
        ----------
        event : tk.Event, optional
            Event information.
        """

        self._zoom_origin = getattr(event, "x")
        self._zoom_canvas = self._canvas.zoom
        self._zoom_mode = True
    # end def

    def _cb_control_motion(self, event: tk.Event):
        """Callback that zooms (scales) in the zoom.

        Parameters
        ----------
        event : tk.Event, optional
            Event information.
        """

        if self._zoom_mode:
            diff = getattr(event, "x") - self._zoom_origin
            factor = 1 + diff / 100

            if factor != 0:
                self._canvas.zoom = self._zoom_canvas * factor
            # end if
        # end if
    # end def

    def _cb_alt_left_click(self, event: tk.Event):
        """Callback that enters the rotation mode.

        Parameters
        ----------
        event : tk.Event, optional
            Event information.
        """

        origin = self._canvas.transform_point(0, 0, inv=True)
        self._rotation = -math.atan2((getattr(event, "y") - origin[1]), (getattr(event, "x") - origin[0]))
        self._rotation_canvas = self._canvas.rotation
        self._rotation_mode = True
    # end def

    def _cb_alt_motion(self, event):
        """Callback that rotates in the rotation mode.

        Parameters
        ----------
        event : tk.Event, optional
            Event information.
        """

        if self._rotation_mode:
            origin = self._canvas.transform_point(0, 0, inv=True)
            rotation = -math.atan2((getattr(event, "y") - origin[1]), (getattr(event, "x") - origin[0]))
            self._canvas.rotation = (self._rotation_canvas + (rotation - self._rotation)) % (2 * math.pi)
        # end if
    # end def

    def _cb_left_click_release(self, _event: tk.Event):
        """Callback that leaves the move (translate) mode.

        Parameters
        ----------
        _event : tk.Event, optional
            Event information. Not used.
        """

        self._move_mode = False
        self._rotation_mode = False
    # end def

    def _cb_motion(self, event: tk.Event):
        """Callback that updates the (scaled) cursor position label.

        Parameters
        ----------
        event : tk.Event, optional
            Event information.
        """

        self._lbl_cursor_pos_ori["text"] = f"Cursor-Position (ori): " \
                                           f"x={getattr(event, 'x'):5.2f}; y={getattr(event, 'y'):5.2f}"
    # end def

    def _cb_motion_scaled(self, event: tk.Event):
        """Callback that updates the (scaled) cursor position label.

        Parameters
        ----------
        event : tk.Event, optional
            Event information.
        """

        p = self._canvas.transform_point(getattr(event, "x"), getattr(event, "y"), inv=True)
        self._lbl_cursor_pos_ori_retrans["text"] = f"Cursor-Position (retrans): x={p[0]:5.2f}; y={p[1]:5.2f}"

        self._lbl_cursor_pos_trans["text"] = f"Cursor-Position (trans): " \
                                             f"x={getattr(event, 'x'):5.2f}; y={getattr(event, 'y'):5.2f}"
    # end def
# end class


def main():
    """The main function running the program."""

    TransformCanvasTest(width=1000, height=1000)
# end def


if __name__ == "__main__":
    main()
# end if
