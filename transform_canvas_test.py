import tkinter as tk
from enum import Enum

from scale_trans_canvas import ScaleTransCanvas


root = tk.Tk()

canvas = ScaleTransCanvas(root, scale_factor=1., scale_ratio=None, invert_y=True, center_origin=True,
                          offset_x=0, offset_y=0, zoom_factor=1.1)
canvas.pack(expand=True, fill=tk.BOTH)


class ZoomDir(Enum):
    """Enumerates the zoom direction."""

    IN = 1
    OUT = 2
# end class


def draw():
    global canvas

    print("draw()")

    canvas.delete("all")

    canvas.create_oval(-10, -10, 10, 10, fill="black")
    canvas.create_line(0, 0, 20, 10)
    canvas.create_line(0, 0, 20, 0)
    canvas.create_oval_rotated(50, 50, 100, 50, 35, n_segments=20, fill="", width=3, outline="black")
# end def


def do_zoom(dir):
    """Zooms the drawing canvas.

    Parameters
    ----------
    dir : Gui.ZoomDir
        Zoom direction.
    """
    if dir == ZoomDir.IN:
        canvas.zoom_in()
    else:
        canvas.zoom_out()
    # end if

    draw()
# end def


def cb_mouse_wheel(event):
    """Callback that handles the mouse wheel event.

    Parameters
    ----------
    event optional
        Event information.

    Returns
    -------
    str
        Indicates if the event shall be propagated further. "break" means not propagate it further.
    """

    # Respond to Linux or Windows wheel event
    if event.num == 4 or event.delta == 120:
        do_zoom(ZoomDir.IN)

    elif event.num == 5 or event.delta == -120:
        do_zoom(ZoomDir.OUT)
    # end if

    return "break"
# end def


def on_resize(_event):
    draw()
# end def


def cb_motion_scaled(event):
    """Callback that updates the (scaled) cursor position label.

    Parameters
    ----------
    event optional
        Event information.
    """

    print(f"x={event.x:5.2f}; y={event.y:5.2f}")
# end def


canvas.bind('<MouseWheel>', cb_mouse_wheel)  # With Windows OS
canvas.bind('<Button-4>', cb_mouse_wheel)  # With Linux OS
canvas.bind('<Button-5>', cb_mouse_wheel)  # "
canvas.bind("<Configure>", on_resize)
canvas.bind('<<MotionScaled>>', cb_motion_scaled)

root.mainloop()
