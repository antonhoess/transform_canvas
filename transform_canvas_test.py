from typing import Optional
import tkinter as tk
import tkinter.messagebox
import math
import numpy as np
from PIL import Image, ImageTk

from transform_canvas import TransformCanvas, Matrix

"""This module provides an example on how to use the TransformCanvas."""

__author__ = "Anton Höß"
__copyright__ = "Copyright 2021"


class ColorHelper:
    @staticmethod
    def float_to_hex(r: float, g: float, b: float):
        return "#" + ''.join(["%02x" % int(e * 255.) for e in [r, g, b]])
    # end def

    @staticmethod
    def hex_to_float(hex: str):
        r = float.fromhex(hex[1:3])
        g = float.fromhex(hex[3:5])
        b = float.fromhex(hex[5:7])

        return r, g, b
    # end def

    @staticmethod
    def blend_hex(hex_a: str, hex_b: str, weight: float):
        rgb_a = ColorHelper.hex_to_float(hex_a)
        rgb_b = ColorHelper.hex_to_float(hex_b)

        return ColorHelper.float_to_hex(
            r=(rgb_a[0] * weight + rgb_b[0] * (1 - weight)),
            g=(rgb_a[1] * weight + rgb_b[1] * (1 - weight)),
            b=(rgb_a[2] * weight + rgb_b[2] * (1 - weight)))
    # end def

    @staticmethod
    def blend_rgb(rgb_a, rgb_b, weight: float):
        return rgb_a[0] * weight + rgb_b[0] * (1 - weight),\
               rgb_a[1] * weight + rgb_b[1] * (1 - weight),\
               rgb_a[2] * weight + rgb_b[2] * (1 - weight)
    # end def
# end class


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

        self.tk_image_handles = list()  # Handles for the images to prevent them from being disposed by the GC

        parents = list()

        def parent():
            return parents[-1]

        w_text = 12

        # Main window
        self._root = tk.Tk()
        self._root.title("TransformCanvas Test")
        parents.append(self._root)

        # ... Control frame
        self._frm_controls = tk.Frame(parent(), width=350)  # Set fixed width.
        self._frm_controls.pack_propagate(0)  # Disables the child widgets define the size.
        self._frm_controls.pack(expand=False, fill=tk.BOTH, side=tk.LEFT)
        parents.append(self._frm_controls)

        # .../... Window information frame
        self._frm_window = tk.LabelFrame(parent(), text="Window Information")
        self._frm_window.pack(expand=False, fill=tk.BOTH, side=tk.TOP, padx=5, pady=5)
        parents.append(self._frm_window)

        # .../.../... Widget size
        self._lbl_window_size_text = tk.Label(parent(), text="Canvas Size:", anchor=tk.W)
        self._lbl_window_size_text.grid(row=0, column=0, sticky=tk.W)
        self._lbl_window_size_width = tk.Label(parent(), width=w_text, anchor=tk.W)
        self._lbl_window_size_width.grid(row=0, column=1, sticky=tk.W)
        self._lbl_window_size_height = tk.Label(parent(), width=w_text, anchor=tk.W)
        self._lbl_window_size_height.grid(row=0, column=2, sticky=tk.W)

        # .../.../... Cursor position(s)
        self._lbl_cursor_pos_ori_text = tk.Label(parent(), text="Cursor Pos. (ori.):", anchor=tk.W)
        self._lbl_cursor_pos_ori_text.grid(row=1, column=0, sticky=tk.W)
        self._lbl_cursor_pos_ori_x = tk.Label(parent(), anchor=tk.W)
        self._lbl_cursor_pos_ori_x.grid(row=1, column=1, sticky=tk.W)
        self._lbl_cursor_pos_ori_y = tk.Label(parent(), anchor=tk.W)
        self._lbl_cursor_pos_ori_y.grid(row=1, column=2, sticky=tk.W)

        self._lbl_cursor_pos_retrans_text = tk.Label(parent(), text="Cursor Pos. (retrans.):")
        self._lbl_cursor_pos_retrans_text.grid(row=2, column=0, sticky=tk.W)
        self._lbl_cursor_pos_retrans_x = tk.Label(parent())
        self._lbl_cursor_pos_retrans_x.grid(row=2, column=1, sticky=tk.W)
        self._lbl_cursor_pos_retrans_y = tk.Label(parent())
        self._lbl_cursor_pos_retrans_y.grid(row=2, column=2, sticky=tk.W)

        self._lbl_cursor_pos_trans_text = tk.Label(parent(), text="Cursor Pos. (trans.):")
        self._lbl_cursor_pos_trans_text.grid(row=3, column=0, sticky=tk.W)
        self._lbl_cursor_pos_trans_x = tk.Label(parent())
        self._lbl_cursor_pos_trans_x.grid(row=3, column=1, sticky=tk.W)
        self._lbl_cursor_pos_trans_y = tk.Label(parent())
        self._lbl_cursor_pos_trans_y.grid(row=3, column=2, sticky=tk.W)

        del parents[-1]

        # .../... Vectors frame
        self._frm_vectors = tk.LabelFrame(parent(), text="Vectors (Resulting Values)")
        self._frm_vectors.pack(expand=False, fill=tk.BOTH, side=tk.TOP, padx=5, pady=5)
        parents.append(self._frm_vectors)

        # .../.../... Translation vector
        self._lbl_vector_translate_text = tk.Label(parent(), text="Translation Vector:", anchor=tk.W)
        self._lbl_vector_translate_text.grid(row=0, column=0, sticky=tk.W)
        self._lbl_vector_translate_x = tk.Label(parent(), width=w_text, anchor=tk.W)
        self._lbl_vector_translate_x.grid(row=0, column=1, sticky=tk.W)
        self._lbl_vector_translate_y = tk.Label(parent(), width=w_text, anchor=tk.W)
        self._lbl_vector_translate_y.grid(row=0, column=2, sticky=tk.W)

        # .../.../... Scaling vector
        self._lbl_vector_scaling_text = tk.Label(parent(), text="Scaling Vector:", anchor=tk.W)
        self._lbl_vector_scaling_text.grid(row=1, column=0, sticky=tk.W)
        self._lbl_vector_scaling_x = tk.Label(parent(), width=w_text, anchor=tk.W)
        self._lbl_vector_scaling_x.grid(row=1, column=1, sticky=tk.W)
        self._lbl_vector_scaling_y = tk.Label(parent(), width=w_text, anchor=tk.W)
        self._lbl_vector_scaling_y.grid(row=1, column=2, sticky=tk.W)

        del parents[-1]

        # .../... Transformation matrix frame
        self._frm_trans_matrix = tk.LabelFrame(parent(), text="Transformation Matrix (Resulting Values)")
        self._frm_trans_matrix.pack(expand=False, fill=tk.X, side=tk.TOP, padx=5, pady=5)
        parents.append(self._frm_trans_matrix)

        # .../.../... Transformation matrix
        self._ent_trans_matrix = list()
        self._var_trans_matrix = list()
        self._var_trans_matrix_text = list()
        for row in range(3):
            self._var_trans_matrix.append(list())
            self._var_trans_matrix_text.append(list())
            self._ent_trans_matrix.append(list())

            for column in range(3):
                if row == 0:
                    parent().columnconfigure(column, weight=1)
                # end if

                self._var_trans_matrix[-1].append(tk.DoubleVar())
                self._var_trans_matrix_text[-1].append(tk.StringVar())
                self._ent_trans_matrix[-1].append(None)
                self._ent_trans_matrix[row][column] = tk.Entry(parent(), text="?",
                                                               textvariable=self._var_trans_matrix_text[row][column],
                                                               state=tk.NORMAL if row < 2 else tk.DISABLED)
                self._ent_trans_matrix[row][column].grid(row=row, column=column, padx=5, pady=2)
                self._ent_trans_matrix[row][column].bind("<Return>",
                                                         lambda e, _row=row, _column=column:
                                                         self._cb_ent_trans_matrix_return(e, row=_row, column=_column))
            # end for
        # end for

        del parents[-1]

        # .../... Translation frame
        self._frm_translation = tk.LabelFrame(parent(), text="Translation")
        self._frm_translation.pack(expand=False, fill=tk.X, side=tk.TOP, padx=5, pady=5)
        parents.append(self._frm_translation)

        # .../.../... Offset sub-frame (to align the widgets horizontally)
        self._frm_offset = tk.Frame(parent())
        self._frm_offset.pack(expand=False, fill=tk.BOTH, side=tk.TOP)
        parents.append(self._frm_offset)

        # .../.../.../... Offset label
        self._lbl_offset = tk.Label(parent(), text="Offset:")
        self._lbl_offset.pack(expand=False, fill=tk.NONE, side=tk.LEFT, padx=(0, 5))

        # .../.../.../... Offset x label
        self._lbl_offset_x = tk.Label(parent(), text="x = ")
        self._lbl_offset_x.pack(expand=False, fill=tk.NONE, side=tk.LEFT)

        # .../.../.../... Offset x entry
        self._var_offset_x = tk.DoubleVar()
        self._var_offset_x_text = tk.StringVar()
        self._ent_offset_x = tk.Entry(parent(), text="?", textvariable=self._var_offset_x_text)
        self._ent_offset_x.pack(expand=False, fill=tk.X, side=tk.LEFT, padx=(0, 5))
        self._ent_offset_x.bind("<Return>", self._cb_ent_offset_x_return)

        # .../.../.../... Offset y label
        self._lbl_offset_y = tk.Label(parent(), text="y = ")
        self._lbl_offset_y.pack(expand=False, fill=tk.NONE, side=tk.LEFT)

        # .../.../.../... Offset y entry
        self._var_offset_y = tk.DoubleVar()
        self._var_offset_y_text = tk.StringVar()
        self._ent_offset_y = tk.Entry(parent(), text="?", textvariable=self._var_offset_y_text)
        self._ent_offset_y.pack(expand=False, fill=tk.X, side=tk.LEFT, padx=(0, 5))
        self._ent_offset_y.bind("<Return>", self._cb_ent_offset_y_return)

        del parents[-1]

        # .../.../... Horizontal separator
        sep_hor = tk.Frame(parent(), height=2, bd=1, relief=tk.SUNKEN)
        sep_hor.pack(expand=False, fill=tk.X, side=tk.TOP, pady=5)

        # .../.../... Origin sub-frame (to align the widgets horizontally)
        self._frm_origin = tk.Frame(parent())
        self._frm_origin.pack(expand=False, fill=tk.BOTH, side=tk.TOP)
        parents.append(self._frm_origin)

        # .../.../.../... Origin label
        self._lbl_origin = tk.Label(parent(), text="Origin:")
        self._lbl_origin.pack(expand=False, fill=tk.NONE, side=tk.LEFT, padx=(0, 5))

        # .../.../.../.../... Origin sub-sub-frame (to align the widgets in a grid)
        self._frm_origin_select = tk.Frame(parent())
        self._frm_origin_select.pack(expand=False, fill=tk.BOTH, side=tk.TOP)
        parents.append(self._frm_origin_select)

        # .../.../.../.../.../... Origin radio buttons
        self._var_origin = tk.StringVar()
        hor = (tk.W, "", tk.E)
        ver = (tk.N, "", tk.S)
        for column in range(3):
            parent().columnconfigure(column, weight=1)

            for row in range(3):
                origin_str = ver[row] + hor[column] if column != 1 or row != 1 else tk.CENTER
                self._var_direction_hor = tk.StringVar()
                self._rad_origin = tk.Radiobutton(parent(), text=origin_str.upper(), value=origin_str,
                                                  variable=self._var_origin, command=self._cb_rad_origin_select)
                self._rad_origin.grid(row=row, column=column, sticky=tk.W)
            # end for
        # end for

        del parents[-1]
        del parents[-1]
        del parents[-1]

        # .../... Scaling frame
        self._frm_scaling = tk.LabelFrame(parent(), text="Scaling")
        self._frm_scaling.pack(expand=False, fill=tk.X, side=tk.TOP, padx=5, pady=5)
        parents.append(self._frm_scaling)

        # .../.../... Scale base sub-frame (to align the widgets horizontally)
        self._frm_scale_base = tk.Frame(parent())
        self._frm_scale_base.pack(expand=False, fill=tk.BOTH, side=tk.TOP)
        parents.append(self._frm_scale_base)

        # .../.../.../... Scale base label
        self._lbl_scale_base = tk.Label(parent(), text="Base Scaling:")
        self._lbl_scale_base.pack(expand=False, fill=tk.NONE, side=tk.LEFT, padx=(0, 5))

        # .../.../.../... Scale base entry
        self._var_scale_base_text = tk.StringVar()
        self._ent_scale_base = tk.Entry(parent(), text="?", textvariable=self._var_scale_base_text)
        self._ent_scale_base.pack(expand=True, fill=tk.X, side=tk.LEFT)
        self._ent_scale_base.bind("<Return>", self._cb_ent_scale_base_return)

        del parents[-1]

        # .../.../... Scale base scale
        self._var_scale_base = tk.DoubleVar()
        self._scl_scale_base_from = .01
        self._scl_scale_base_to = 10.
        self._scl_scale_base_neutral = 1.
        self._scl_scale_base = tk.Scale(parent(), orient=tk.HORIZONTAL, showvalue=False,
                                        from_=self._scl_scale_base_from, to=self._scl_scale_base_to,
                                        resolution=0.01, variable=self._var_scale_base,
                                        command=self._cb_scl_scale_base_tick)
        self._scl_scale_base.pack(expand=False, fill=tk.X, side=tk.TOP)

        # .../.../... Horizontal separator
        sep_hor = tk.Frame(parent(), height=2, bd=1, relief=tk.SUNKEN)
        sep_hor.pack(expand=False, fill=tk.X, side=tk.TOP, pady=5)

        # .../.../... Scale ratio sub-frame (to align the widgets horizontally)
        self._frm_scale_ratio = tk.Frame(parent())
        self._frm_scale_ratio.pack(expand=False, fill=tk.BOTH, side=tk.TOP)
        parents.append(self._frm_scale_ratio)

        # .../.../.../... Scale ratio label
        self._lbl_scale_ratio = tk.Label(parent(), text="Scale Ratio:")
        self._lbl_scale_ratio.pack(expand=False, fill=tk.NONE, side=tk.LEFT, padx=(0, 5))

        # .../.../.../... Scale ratio entry
        self._var_scale_ratio_text = tk.StringVar()
        self._ent_scale_ratio = tk.Entry(parent(), text="?", textvariable=self._var_scale_ratio_text)
        self._ent_scale_ratio.pack(expand=True, fill=tk.X, side=tk.LEFT)
        self._ent_scale_ratio.bind("<Return>", self._cb_ent_scale_ratio_return)

        # .../.../.../... Scale ratio checkbutton
        self._var_scale_ratio_chk = tk.IntVar()
        self._chk_scale_ratio = tk.Checkbutton(parent(), text=None, variable=self._var_scale_ratio_chk,
                                               command=self._cb_chk_scale_ratio_toggle)
        self._chk_scale_ratio.pack(expand=False, fill=tk.X, side=tk.LEFT)

        del parents[-1]

        # .../.../... Scale ratio scale
        self._var_scale_ratio = tk.DoubleVar()
        self._scl_scale_ratio_from = .01
        self._scl_scale_ratio_to = 10.
        self._scl_scale_ratio_neutral = 1.
        self._scl_scale_ratio = tk.Scale(parent(), orient=tk.HORIZONTAL, showvalue=False,
                                         from_=self._scl_scale_ratio_from, to=self._scl_scale_ratio_to,
                                         resolution=0.01, variable=self._var_scale_ratio,
                                         command=self._cb_scl_scale_ratio_tick)
        self._scl_scale_ratio.pack(expand=False, fill=tk.X, side=tk.TOP)

        # .../.../... Horizontal separator
        sep_hor = tk.Frame(parent(), height=2, bd=1, relief=tk.SUNKEN)
        sep_hor.pack(expand=False, fill=tk.X, side=tk.TOP, pady=5)

        # .../.../... Zoom factor sub-frame (to align the widgets horizontally)
        self._frm_zoom_factor = tk.Frame(parent())
        self._frm_zoom_factor.pack(expand=False, fill=tk.BOTH, side=tk.TOP)
        parents.append(self._frm_zoom_factor)

        # .../.../.../... Zoom factor label
        self._lbl_zoom_factor = tk.Label(parent(), text="Zoom factor:")
        self._lbl_zoom_factor.pack(expand=False, fill=tk.NONE, side=tk.LEFT, padx=(0, 5))

        # .../.../.../... Zoom factor entry
        self._var_zoom_factor_text = tk.StringVar()
        self._ent_zoom_factor = tk.Entry(parent(), text="?", textvariable=self._var_zoom_factor_text)
        self._ent_zoom_factor.pack(expand=True, fill=tk.X, side=tk.LEFT)
        self._ent_zoom_factor.bind("<Return>", self._cb_ent_zoom_factor_return)

        del parents[-1]

        # .../.../... Zoom factor scale
        self._var_zoom_factor = tk.DoubleVar()
        self._scl_zoom_factor_from = .01
        self._scl_zoom_factor_to = 10.
        self._scl_zoom_factor_neutral = 1.
        self._scl_zoom_factor = tk.Scale(parent(), orient=tk.HORIZONTAL, showvalue=False,
                                         from_=self._scl_zoom_factor_from, to=self._scl_zoom_factor_to,
                                         resolution=0.01, variable=self._var_zoom_factor,
                                         command=self._cb_scl_zoom_factor_tick)
        self._scl_zoom_factor.pack(expand=False, fill=tk.X, side=tk.TOP)

        # .../.../... Horizontal separator
        sep_hor = tk.Frame(parent(), height=2, bd=1, relief=tk.SUNKEN)
        sep_hor.pack(expand=False, fill=tk.X, side=tk.TOP, pady=5)

        # .../.../... Zoom sub-frame (to align the widgets horizontally)
        self._frm_zoom = tk.Frame(parent())
        self._frm_zoom.pack(expand=False, fill=tk.BOTH, side=tk.TOP)
        parents.append(self._frm_zoom)

        # .../.../.../... Zoom label
        self._lbl_zoom = tk.Label(parent(), text="Zoom:")
        self._lbl_zoom.pack(expand=False, fill=tk.NONE, side=tk.LEFT, padx=(0, 5))

        # .../.../.../... Zoom entry
        self._var_zoom_text = tk.StringVar()
        self._ent_zoom = tk.Entry(parent(), text="?", textvariable=self._var_zoom_text)
        self._ent_zoom.pack(expand=True, fill=tk.X, side=tk.LEFT)
        self._ent_zoom.bind("<Return>", self._cb_ent_zoom_return)

        del parents[-1]

        # .../.../... Zoom scale
        self._var_zoom = tk.DoubleVar()
        self._scl_zoom_from = .01
        self._scl_zoom_to = 10.
        self._scl_zoom_neutral = 1.
        self._scl_zoom = tk.Scale(parent(), orient=tk.HORIZONTAL, showvalue=False, from_=self._scl_zoom_from,
                                  to=self._scl_zoom_to, resolution=0.01, variable=self._var_zoom,
                                  command=self._cb_scl_zoom_tick)
        self._scl_zoom.pack(expand=False, fill=tk.X, side=tk.TOP)

        # .../.../... Horizontal separator
        sep_hor = tk.Frame(parent(), height=2, bd=1, relief=tk.SUNKEN)
        sep_hor.pack(expand=False, fill=tk.X, side=tk.TOP, pady=5)

        # .../.../... Direction sub-frame (to align the widgets horizontally)
        self._frm_direction = tk.Frame(parent())
        self._frm_direction.pack(expand=False, fill=tk.BOTH, side=tk.TOP)
        parents.append(self._frm_direction)

        # .../.../.../... Direction label
        self._lbl_direction = tk.Label(parent(), text="Direction:")
        self._lbl_direction.pack(expand=False, fill=tk.NONE, side=tk.LEFT, padx=(0, 5))

        # .../.../.../... Direction sub-sub-frame horizontal (for radio buttons)
        self._frm_direction_hor = tk.Frame(parent())
        self._frm_direction_hor.pack(expand=True, fill=tk.BOTH, side=tk.LEFT)
        parents.append(self._frm_direction_hor)

        # .../.../.../.../... Direction option horizontal
        self._var_direction_hor = tk.StringVar()
        self._rad_direction_west = tk.Radiobutton(parent(), text="W", value=tk.W, variable=self._var_direction_hor,
                                                  command=self._cb_rad_direction_select)
        self._rad_direction_west.pack(expand=True, fill=tk.X, side=tk.LEFT)

        self._rad_direction_east = tk.Radiobutton(parent(), text="E", value=tk.E, variable=self._var_direction_hor,
                                                  command=self._cb_rad_direction_select)
        self._rad_direction_east.pack(expand=True, fill=tk.X, side=tk.LEFT)
        del parents[-1]

        # .../... Vertical separator
        sep_ver = tk.Frame(parent(), width=2, bd=1, relief=tk.SUNKEN)
        sep_ver.pack(expand=True, fill=tk.Y, side=tk.LEFT, pady=5)

        # .../.../.../... Direction sub-sub-frame vertical (for radio buttons)
        self._frm_direction_ver = tk.Frame(parent())
        self._frm_direction_ver.pack(expand=True, fill=tk.BOTH, side=tk.LEFT)
        parents.append(self._frm_direction_ver)

        # .../.../.../.../... Direction option vertical
        self._var_direction_ver = tk.StringVar()
        self._rad_direction_north = tk.Radiobutton(parent(), text="N", value=tk.N, variable=self._var_direction_ver,
                                                   command=self._cb_rad_direction_select)
        self._rad_direction_north.pack(expand=True, fill=tk.X, side=tk.LEFT)

        self._rad_direction_south = tk.Radiobutton(parent(), text="S", value=tk.S, variable=self._var_direction_ver,
                                                   command=self._cb_rad_direction_select)
        self._rad_direction_south.pack(expand=True, fill=tk.X, side=tk.LEFT)

        del parents[-1]
        del parents[-1]
        del parents[-1]

        # .../... Rotation frame
        self._frm_rotation = tk.LabelFrame(parent(), text="Rotation")
        self._frm_rotation.pack(expand=False, fill=tk.X, side=tk.TOP, padx=5, pady=5)
        parents.append(self._frm_rotation)

        # .../.../... Rotation angle sub-frame (to align the widgets horizontally)
        self._frm_rotation_angle = tk.Frame(parent())
        self._frm_rotation_angle.pack(expand=False, fill=tk.BOTH, side=tk.TOP)
        parents.append(self._frm_rotation_angle)

        # .../.../.../... Rotation angle label
        self._lbl_rotation_angle = tk.Label(parent(), text="Rotation Angle:")
        self._lbl_rotation_angle.pack(expand=False, fill=tk.NONE, side=tk.LEFT, padx=(0, 5))

        # .../.../.../... Rotation angle entry
        self._var_rotation_angle_text = tk.StringVar()
        self._ent_rotation_angle = tk.Entry(parent(), text="?", textvariable=self._var_rotation_angle_text)
        self._ent_rotation_angle.pack(expand=True, fill=tk.X, side=tk.LEFT)
        self._ent_rotation_angle.bind("<Return>", self._cb_ent_rotation_angle_return)

        del parents[-1]

        # .../.../... Rotation angle scale
        self._var_rotation_angle = tk.DoubleVar()
        self._scl_rotation_angle_from = -180.
        self._scl_rotation_angle_to = 180.
        self._scl_rotation_angle_neutral = 0.
        self._scl_rotation_angle = tk.Scale(parent(), orient=tk.HORIZONTAL, showvalue=False,
                                            from_=self._scl_rotation_angle_from, to=self._scl_rotation_angle_to,
                                            resolution=0.0001, variable=self._var_rotation_angle,
                                            command=self._cb_scl_rotation_angle_tick)
        self._scl_rotation_angle.pack(expand=False, fill=tk.X, side=tk.TOP)

        del parents[-1]
        del parents[-1]

        # .../... Vertical separator
        sep_ver = tk.Frame(parent(), width=2, bd=1, relief=tk.SUNKEN)
        sep_ver.pack(expand=False, fill=tk.Y, side=tk.LEFT, pady=5)

        # ... Canvas
        self._canvas = TransformCanvas(parent(), width=width, height=height, scale_base=2., scale_ratio=None,
                                       zoom_factor=1.1, direction=tk.NE, origin=tk.CENTER, offset=(150, -200),
                                       rotation=math.pi*2+.0001, ignore_intermediate_updates=False)
        self._canvas.cb_draw = self._draw
        self._canvas.pack(expand=True, fill=tk.BOTH, side=tk.LEFT)
        self._canvas.bind('<Configure>', self._cb_configure)
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

        # Set some initial values on the widgets
        omit_draw_ori = self._canvas.omit_draw
        self._canvas.omit_draw = True

        # Origin
        self._var_origin.set(self._canvas.origin)

        # Offset
        self._var_offset_x.set(self._canvas.offset[0])
        self._var_offset_x_text.set(self._canvas.offset[0])
        self._var_offset_y.set(self._canvas.offset[1])
        self._var_offset_y_text.set(self._canvas.offset[1])

        # Scale base
        self._scl_scale_base.set(self._canvas.scale_base)

        # Scale ratio
        if self._canvas.scale_ratio is None:
            self._var_scale_ratio.set(1.)
            self._cb_scl_scale_ratio_tick()  # Without this command, there will be no text in the disabled entry
            self._cb_chk_scale_ratio_toggle()
        else:
            self._scl_scale_ratio.set(self._canvas.scale_ratio)
            self._var_scale_ratio_chk.set(tk.TRUE)
        # end if

        # Zoom factor
        self._scl_zoom_factor.set(self._canvas.zoom_factor)
        self._cb_scl_zoom_factor_tick()

        # Zoom
        self._scl_zoom.set(self._canvas.zoom)
        self._cb_scl_zoom_tick()

        # Direction - first component (=letter) is vertical (north/south), second component ist horizontal (east/west)
        self._var_direction_ver.set(self._canvas.direction[0])
        self._var_direction_hor.set(self._canvas.direction[1])

        # Rotation
        self._scl_rotation_angle.set(TransformCanvas.rad2deg(self._canvas.rotation))
        self._cb_scl_rotation_angle_tick()

        self._canvas.omit_draw = omit_draw_ori
        self._canvas.update()

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

    @staticmethod
    def _get_color_by_value(value: float, min_value: float, max_value: float,
                            neutral_value: Optional[float] = None) -> str:
        """Calculates the color based on a value and its value range. Green for low values and red for high values.

        Parameters
        ----------
        value : float
            The given value.
        min_value : float
            The value's min. range border.
        max_value : float
            The value's max. range border.
        neutral_value : float, optional
            The value's range neutral value. If not set, it gets set to the mean of the range's min. and max. value.

        Returns
        -------
        color : str
            The color string.
        """

        # Calculate neutral value as mean if not set
        if neutral_value is None:
            neutral_value = (max_value - min_value) / 2
        # end if

        # Limit the values to the min-max-range (only for calculating the color)
        value = max(min(value, max_value), min_value)

        if value >= neutral_value:
            weight = (value - neutral_value) / (max_value - neutral_value)
            return ColorHelper.float_to_hex(*ColorHelper.blend_rgb(rgb_a=(1, 0, 0), rgb_b=(1, 1, 1), weight=weight))
        else:
            weight = (value - neutral_value) / (min_value - neutral_value)
            return ColorHelper.float_to_hex(*ColorHelper.blend_rgb(rgb_a=(0, 1, 0), rgb_b=(1, 1, 1), weight=weight))
        # end if
    # end def

    def _draw(self):
        """Draws the scene."""

        # Update labels
        ###############

        # Vectors
        translation_vector = self._canvas.translation_vector
        self._lbl_vector_translate_x.configure(text=f"x = {translation_vector[0]:.02f}")
        self._lbl_vector_translate_y.configure(text=f"y = {translation_vector[1]:.02f}")

        scaling_vector = self._canvas.scaling_vector
        self._lbl_vector_scaling_x.configure(text=f"x = {scaling_vector[0]:.02f}")
        self._lbl_vector_scaling_y.configure(text=f"y = {scaling_vector[1]:.02f}")

        # Transformation matrix - set here since it is the easiest place instead of updating it in so many places
        matrix = self._canvas.transformation_matrix
        for row in range(3):
            for column in range(3):
                self._var_trans_matrix_text[row][column].set(f"{matrix[row][column]:.02f}")
            # end for
        # end for

        self._canvas.delete("all")

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

        if x1 is not None and x2 is not None:  # This check is necessary in case the zoom is very very high
            self._canvas.base.create_line(x1[0], x1[1], x2[0], x2[1], dash=(5, 8), width=1, trans=False)
        # end if

        # Calculate and draw y axis
        x1 = self._seg_intersect(np.asarray([ox, oy]), np.asarray([ox - math.sin(r), oy - math.cos(r)]),
                                 *top_border)

        x2 = self._seg_intersect(np.asarray([ox, oy]), np.asarray([ox - math.sin(r), oy - math.cos(r)]),
                                 *bottom_border)

        if x1 is not None and x2 is not None:  # This check is necessary in case the zoom is very very high
            self._canvas.base.create_line(x1[0], x1[1], x2[0], x2[1], dash=(3, 5), trans=False)
        # end if

        # Draw some test objects
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
                                 rotate(angle=.1), n_segments=8)
        self._canvas.create_line(0, 0, 20, 10, width=2, fill="blue")
        self._canvas.create_line(0, 0, 20, 0)
        self._canvas.create_text(50, 50, text="This is a rotation test", font=('Arial', 8, 'bold'), angle=10.,
                                 scale_font_size=False, anchor=tk.NW)
        self._canvas.create_arc(-200, -250, 0, 0, dash=(3, 5), start=10, extent=290, fill="light blue", outline="black",
                                style=tk.CHORD, n_segments=12)
        self._canvas.base.create_arc(200, 200, 250, 300, dash=(3, 5), trans=False, start=90, extent=190,
                                     fill="light green", style=tk.ARC)
        self._canvas.base.create_arc(10, 10, 200, 200, dash=(3, 5), start=10, extent=180, fill="light blue",
                                     outline="black", style=tk.PIESLICE, trans=False)

        # Images
        # Since this drawing function will get called again and again the images will accumulate, but we don't need
        # the old ones anymore
        self.tk_image_handles.clear()
        self._canvas.clear_tk_image_handles()

        # Static image - (C) Webber (assumed, based on copyright claims), Creative Commons (Wikipedia)
        image_fn = "test_images/pattern_test_webber_wikipedia_cc.jpg"
        image = Image.open(image_fn)
        image = ImageTk.PhotoImage(image)
        # The handle is kept in this program space
        self.tk_image_handles.append(image)
        self._canvas.base.create_image(50, 500, image=image, trans=False)

        # Transformed image - (C) Eukaryogurt, Creative Commons (Wikipedia)
        image_fn = "test_images/wikipedia_transparent_logo_eukaryogurt_wikipedia_cc.png"
        image = Image.open(image_fn)
        # The handle is kept inside TransformCanvas
        self._canvas.create_image(100, 100, image=image, local_scaling_factor=.05)

        # Transformed image with reference kept in here
        image_fn = "test_images/wikipedia_transparent_logo_eukaryogurt_wikipedia_cc.png"
        image = Image.open(image_fn)
        image = image.resize((int(image.size[0] * .01), int(image.size[1] * .01)), Image.LANCZOS)
        image = ImageTk.PhotoImage(image)
        self.tk_image_handles.append(image)
        # The handle is kept here
        self._canvas.create_image(-30, -30, image=image)
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

        self._var_zoom.set(self._canvas.zoom)
        # Makes problems when zooming in more than the max. allowed (by the Scale widget's variable) zoom.
        # self._cb_scl_zoom_tick()
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

    def _cb_configure(self, event: tk.Event):
        """Callback that handles the resize event of the canvas.

        Parameters
        ----------
        event : tk.Event, optional
            Event information.
        """

        self._lbl_window_size_width.configure(text=f"w = {self._canvas.winfo_width()}")
        self._lbl_window_size_height.configure(text=f"h = {self._canvas.winfo_height()}")
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

            self._var_offset_x.set(self._canvas.offset[0])
            self._var_offset_x_text.set(f"{self._canvas.offset[0]:.02f}")
            self._var_offset_y.set(self._canvas.offset[1])
            self._var_offset_y_text.set(f"{self._canvas.offset[1]:.02f}")
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

            self._var_rotation_angle.set(TransformCanvas.rad2deg(self._canvas.rotation))
            self._cb_scl_rotation_angle_tick()
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

        self._lbl_cursor_pos_ori_x.configure(text=f"x = {getattr(event, 'x'):.2f}")
        self._lbl_cursor_pos_ori_y.configure(text=f"y = {getattr(event, 'y'):.2f}")
    # end def

    def _cb_motion_scaled(self, event: tk.Event):
        """Callback that updates the (scaled) cursor position label.

        Parameters
        ----------
        event : tk.Event
            Event information.
        """

        p = self._canvas.transform_point(getattr(event, "x"), getattr(event, "y"), inv=True)

        self._lbl_cursor_pos_retrans_x.configure(text=f"x = {p[0]:.2f}")
        self._lbl_cursor_pos_retrans_y.configure(text=f"y = {p[0]:.2f}")

        self._lbl_cursor_pos_trans_x.configure(text=f"x = {getattr(event, 'x'):.2f}")
        self._lbl_cursor_pos_trans_y.configure(text=f"y = {getattr(event, 'y'):.2f}")
    # end def

    def _cb_ent_trans_matrix_return(self, _event: tk.Event, row: int, column: int):
        """Callback that updates the transformation matrix cell with the value entered in the tk.Entry.

        Parameters
        ----------
        _event : tk.Event
            Event information. Not used.
        row : int
            The row index ot the matrix cell.
        column : int
            The column index ot the matrix cell.
        """

        value_old_str = self._var_trans_matrix[row][column].get()  # To restore old value (string) or error
        value_str = self._var_trans_matrix_text[row][column].get()

        try:
            value = float(value_str)

            try:
                transformation_matrix = self._canvas.transformation_matrix
                transformation_matrix[row, column] = value
                self._canvas.transformation_matrix = transformation_matrix
                self._var_trans_matrix[row][column].set(value)
                self._var_trans_matrix_text[row][column].set(value_str)
            except ValueError as e:
                tkinter.messagebox.showerror(title="Invalid entry", message=e)
                self._var_scale_base_text.set(value_old_str)
            # end try

        except ValueError:
            tkinter.messagebox.showerror(title="Invalid entry", message="The value entered is not a valid float value.")
            self._var_trans_matrix_text[row][column].set(value_old_str)
        # end try
    # end def

    def _cb_ent_offset_x_return(self, _event: Optional[tk.Event] = None):
        """Callback that updates the offset x value with the value entered in the tk.Entry.

        Parameters
        ----------
        _event : tk.Event, optional
            Event information. Not used.
        """

        value_old_str = self._var_offset_x.get()  # To restore old value (string) or error
        value_str = self._var_offset_x_text.get()

        try:
            value = float(value_str)

            try:
                self._canvas.offset = (value, None)
                self._var_offset_x.set(value)
                self._var_offset_x_text.set(value_str)
            except ValueError as e:
                tkinter.messagebox.showerror(title="Invalid entry", message=e)
                self._var_scale_base_text.set(value_old_str)
            # end try

        except ValueError:
            tkinter.messagebox.showerror(title="Invalid entry", message="The value entered is not a valid float value.")
            self._var_scale_base_text.set(value_old_str)
        # end try
    # end def

    def _cb_ent_offset_y_return(self, _event: tk.Event):
        """Callback that updates the offset y value with the value entered in the tk.Entry.

        Parameters
        ----------
        _event : tk.Event, optional
            Event information. Not used.
        """

        value_old_str = self._var_offset_y.get()  # To restore old value (string) or error
        value_str = self._var_offset_y_text.get()

        try:
            value = float(value_str)

            try:
                self._canvas.offset = (None, value)
                self._var_offset_y.set(value)
                self._var_offset_y_text.set(value_str)
            except ValueError as e:
                tkinter.messagebox.showerror(title="Invalid entry", message=e)
                self._var_scale_base_text.set(value_old_str)
            # end try

        except ValueError:
            tkinter.messagebox.showerror(title="Invalid entry", message="The value entered is not a valid float value.")
            self._var_scale_base_text.set(value_old_str)
        # end try
    # end def

    def _cb_rad_origin_select(self, _event: Optional[tk.Event] = None):
        """Callback that updates the origin value.

        Parameters
        ----------
        _event : tk.Event, optional
            Event information. Not used.
        """

        self._canvas.origin = self._var_origin.get()
    # end def

    def _cb_ent_scale_base_return(self, _event: tk.Event):
        """Callback that updates the scale base value with the value entered in the tk.Entry.

        Parameters
        ----------
        _event : tk.Event, optional
            Event information. Not used.
        """

        value_old_str = self._var_scale_base.get()  # To restore old value (string) or error
        value_str = self._var_scale_base_text.get()

        try:
            value = float(value_str)

            try:
                self._canvas.scale_base = value
                self._var_scale_base.set(value)
                self._var_scale_base_text.set(value_str)
            except ValueError as e:
                tkinter.messagebox.showerror(title="Invalid entry", message=e)
                self._var_scale_base_text.set(value_old_str)
            # end try

        except ValueError:
            tkinter.messagebox.showerror(title="Invalid entry", message="The value entered is not a valid float value.")
            self._var_scale_base_text.set(value_old_str)
        # end try
    # end def

    def _cb_scl_scale_base_tick(self, _event: Optional[tk.Event] = None, update_text: bool = True):
        """Callback that updates the scale base value.

        Parameters
        ----------
        _event : tk.Event
            Event information. Not used.
        update_text : bool, default True
            Indicates if the entry text shall be updated.
        """

        if update_text:
            self._ent_scale_base.delete(0, tk.END)
            self._ent_scale_base.insert(0, f"{self._var_scale_base.get():.2f}")
        # end if

        self._canvas.scale_base = self._var_scale_base.get()
        self._scl_scale_base.configure(
            troughcolor=self._get_color_by_value(value=self._scl_scale_base.get(),
                                                 min_value=self._scl_scale_base_from,
                                                 max_value=self._scl_scale_base_to,
                                                 neutral_value=self._scl_scale_base_neutral))
    # end def

    def _cb_ent_scale_ratio_return(self, _event: tk.Event):
        """Callback that updates the scale ratio value with the value entered in the tk.Entry.

        Parameters
        ----------
        _event : tk.Event, optional
            Event information. Not used.
        """

        value_old_str = self._var_scale_ratio.get()  # To restore old value (string) or error
        value_str = self._var_scale_ratio_text.get()

        try:
            value = float(value_str)

            try:
                self._canvas.scale_ratio = value
                self._var_scale_ratio.set(value)
                self._var_scale_ratio_text.set(value_str)
            except ValueError as e:
                tkinter.messagebox.showerror(title="Invalid entry", message=e)
                self._var_scale_ratio_text.set(value_old_str)
            # end try

        except ValueError:
            tkinter.messagebox.showerror(title="Invalid entry", message="The value entered is not a valid float value.")
            self._var_scale_ratio_text.set(value_old_str)
        # end try
    # end def

    def _cb_chk_scale_ratio_toggle(self):
        """Callback that toggles the scale ratio between None and a float value and
        disables and enables all corresponding widgets."""

        if self._var_scale_ratio_chk.get():
            self._canvas.scale_ratio = self._var_scale_ratio.get()
            self._lbl_scale_ratio.configure(state=tk.NORMAL)
            self._ent_scale_ratio.configure(state=tk.NORMAL)
            self._scl_scale_ratio.configure(state=tk.NORMAL)
        else:
            self._canvas.scale_ratio = None
            self._lbl_scale_ratio.configure(state=tk.DISABLED)
            self._ent_scale_ratio.configure(state=tk.DISABLED)
            self._scl_scale_ratio.configure(state=tk.DISABLED)
        # end if
    # end def

    def _cb_scl_scale_ratio_tick(self, _event: Optional[tk.Event] = None, update_text: bool = True):
        """Callback that updates the scale ratio value.

        Parameters
        ----------
        _event : tk.Event, default None
            Event information. Not used.
        update_text : bool, default True
            Indicates if the entry text shall be updated.
        """

        if update_text:
            self._ent_scale_ratio.delete(0, tk.END)
            self._ent_scale_ratio.insert(0, f"{self._var_scale_ratio.get():.2f}")
        # end if

        self._canvas.scale_ratio = self._var_scale_ratio.get()
        self._scl_scale_ratio.configure(
            troughcolor=self._get_color_by_value(value=self._scl_scale_ratio.get(),
                                                 min_value=self._scl_scale_ratio_from,
                                                 max_value=self._scl_scale_ratio_to,
                                                 neutral_value=self._scl_scale_ratio_neutral))
    # end def

    def _cb_ent_zoom_factor_return(self, _event: tk.Event):
        """Callback that updates the zoom factor value with the value entered in the tk.Entry.

        Parameters
        ----------
        _event : tk.Event, optional
            Event information. Not used.
        """

        value_old_str = self._var_zoom_factor.get()  # To restore old value (string) or error
        value_str = self._var_zoom_factor_text.get()

        try:
            value = float(value_str)

            try:
                self._canvas.zoom_factor = value
                self._var_zoom_factor.set(value)
                self._var_zoom_factor_text.set(value_str)
            except ValueError as e:
                tkinter.messagebox.showerror(title="Invalid entry", message=e)
                self._var_zoom_factor_text.set(value_old_str)
            # end try

        except ValueError:
            tkinter.messagebox.showerror(title="Invalid entry", message="The value entered is not a valid float value.")
            self._var_zoom_factor_text.set(value_old_str)
        # end try
    # end def

    def _cb_scl_zoom_factor_tick(self, _event: Optional[tk.Event] = None, update_text: bool = True):
        """Callback that updates the zoom factor value.

        Parameters
        ----------
        _event : tk.Event, optional
            Event information. Not used.
        update_text : bool, default True
            Indicates if the entry text shall be updated.
        """

        if update_text:
            self._ent_zoom_factor.delete(0, tk.END)
            self._ent_zoom_factor.insert(0, f"{self._var_zoom_factor.get():.2f}")
        # end if

        self._canvas.zoom_factor = self._var_zoom_factor.get()
        self._scl_zoom_factor.configure(
            troughcolor=self._get_color_by_value(value=self._scl_zoom_factor.get(),
                                                 min_value=self._scl_zoom_factor_from,
                                                 max_value=self._scl_zoom_factor_to,
                                                 neutral_value=self._scl_zoom_factor_neutral))
    # end def

    def _cb_ent_zoom_return(self, _event: tk.Event):
        """Callback that updates the zoom value with the value entered in the tk.Entry.

        Parameters
        ----------
        _event : tk.Event, optional
            Event information. Not used.
        """

        value_old_str = self._var_zoom.get()  # To restore old value (string) or error
        value_str = self._var_zoom_text.get()

        try:
            value = float(value_str)

            try:
                self._canvas.zoom = value
                self._var_zoom.set(value)
                self._var_zoom_text.set(value_str)
            except ValueError as e:
                tkinter.messagebox.showerror(title="Invalid entry", message=e)
                self._var_zoom_text.set(value_old_str)
            # end try

        except ValueError:
            tkinter.messagebox.showerror(title="Invalid entry", message="The value entered is not a valid float value.")
            self._var_zoom_text.set(value_old_str)
        # end try
    # end def

    def _cb_scl_zoom_tick(self, _event: Optional[tk.Event] = None, update_text: bool = True):
        """Callback that updates the zoom value.

        Parameters
        ----------
        _event : tk.Event, optional
            Event information. Not used.
        update_text : bool, default True
            Indicates if the entry text shall be updated.
        """

        if update_text:
            self._ent_zoom.delete(0, tk.END)
            self._ent_zoom.insert(0, f"{self._var_zoom.get():.2f}")
        # end if

        self._canvas.zoom = self._var_zoom.get()
        self._scl_zoom.configure(
            troughcolor=self._get_color_by_value(value=self._scl_zoom.get(),
                                                 min_value=self._scl_zoom_from,
                                                 max_value=self._scl_zoom_to,
                                                 neutral_value=self._scl_zoom_neutral))
    # end def

    def _cb_rad_direction_select(self, _event: Optional[tk.Event] = None):
        """Callback that updates the direction value.

        Parameters
        ----------
        _event : tk.Event, optional
            Event information. Not used.
        """

        self._canvas.direction = self._var_direction_ver.get() + self._var_direction_hor.get()
    # end def

    def _cb_ent_rotation_angle_return(self, _event: tk.Event):
        """Callback that updates the rotation angle with the value entered in the tk.Entry.

        Parameters
        ----------
        _event : tk.Event, optional
            Event information. Not used.
        """

        value_old_str = self._var_rotation_angle.get()  # To restore old value (string) or error
        value_str = self._var_rotation_angle_text.get()

        try:
            value = float(value_str)

            try:
                self._canvas.rotation = TransformCanvas.deg2rad(value)
                self._var_rotation_angle.set(TransformCanvas.deg2rad(value))
                self._var_rotation_angle_text.set(value_str)
            except ValueError as e:
                tkinter.messagebox.showerror(title="Invalid entry", message=e)
                self._var_rotation_angle_text.set(value_old_str)
            # end try

        except ValueError:
            tkinter.messagebox.showerror(title="Invalid entry", message="The value entered is not a valid float value.")
            self._var_rotation_angle_text.set(value_old_str)
        # end try
    # end def

    def _cb_scl_rotation_angle_tick(self, _event: Optional[tk.Event] = None, update_text: bool = True):
        """Callback that updates the rotation angle.

        Parameters
        ----------
        _event : tk.Event
            Event information. Not used.
        update_text : bool, default True
            Indicates if the entry text shall be updated.
        """

        if update_text:
            self._ent_rotation_angle.delete(0, tk.END)
            self._ent_rotation_angle.insert(0, f"{self._var_rotation_angle.get():.6f}")
        # end if

        self._canvas.rotation = TransformCanvas.deg2rad(self._var_rotation_angle.get())
        self._scl_rotation_angle.configure(
            troughcolor=self._get_color_by_value(value=self._scl_rotation_angle.get(),
                                                 min_value=self._scl_rotation_angle_from,
                                                 max_value=self._scl_rotation_angle_to,
                                                 neutral_value=self._scl_rotation_angle_neutral))
    # end def
# end class


def main():
    """The main function running the program."""

    TransformCanvasTest(width=1000, height=1000)
# end def


if __name__ == "__main__":
    main()
# end if
