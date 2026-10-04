"""Read-only mathematical table with measured cells and a fixed header.

Canvas items use their actual image dimensions, avoiding native Treeview
heading elements whose requested height differs across Tk platforms.
Only visible cells are drawn so scrolling does not allocate a full canvas
item matrix for large point groups.
"""
from bisect import bisect_right
import sys
import tkinter as tk
from tkinter import ttk

from core import fmt
from math_display import number_tex, symbol_tex


class MathTable(ttk.Frame):
    padding = 12

    def __init__(self, parent, math):
        super().__init__(parent)
        self.math = math
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        style = ttk.Style(self)
        self.header_background = style.lookup('Treeview.Heading', 'background') or '#dcdad5'
        self.background = style.lookup('Treeview', 'background') or '#ffffff'
        self.border = '#bdc2c7'
        self.header = tk.Canvas(self, height=1, highlightthickness=0,
                                background=self.header_background)
        self.body = tk.Canvas(self, highlightthickness=0, background=self.background)
        self.sx = ttk.Scrollbar(self, orient='horizontal', command=self.xview)
        self.sy = ttk.Scrollbar(self, orient='vertical', command=self.yview)
        self.body.configure(xscrollcommand=self._xscroll, yscrollcommand=self._yscroll)
        self.header.grid(row=0, column=0, sticky='ew')
        self.body.grid(row=1, column=0, sticky='nsew')
        self.sx.grid(row=2, column=0, sticky='ew')
        self.sy.grid(row=1, column=1, sticky='ns')
        self.table = None
        self._redraw_timer = None
        self.header_cells = {}
        self.body_cells = {}
        for canvas in (self.header, self.body):
            canvas.bind('<Configure>', self._schedule_draw)
            canvas.bind('<MouseWheel>', self._wheel)
            canvas.bind('<Button-4>', lambda e: self.yview('scroll', -1, 'units'))
            canvas.bind('<Button-5>', lambda e: self.yview('scroll', 1, 'units'))
        self.bind('<Destroy>', self._destroy, add='+')

    def _destroy(self, event):
        if event.widget is self and self._redraw_timer is not None:
            self.after_cancel(self._redraw_timer)
            self._redraw_timer = None

    def set_table(self, table):
        self.table = table
        symbols = table.symbolic_rows()
        self.plain_rows = [[fmt(z) for z in row] for row in symbols]
        self.tex_rows = [[number_tex(z) for z in row] for row in symbols]
        self.heading_images = [None] + [self.math.image(symbol_tex(label)) for label in table.classes]
        self.row_images = [self.math.image(symbol_tex(label)) for label in table.irreps]
        # Render each unique expression once; MathImages holds references.
        self.value_images = {tex: self.math.image(tex) for row in self.tex_rows for tex in row}
        margin = 2 * self.padding
        self.header_height = max(image.height() for image in self.heading_images[1:]) + margin
        self.row_height = max(image.height() for image in
                              [*self.row_images, *self.value_images.values()]) + margin
        widths = [max(90, max(image.width() for image in self.row_images) + margin)]
        for j, heading in enumerate(self.heading_images[1:]):
            widths.append(max(90, heading.width() + margin,
                              max(self.value_images[row[j]].width() for row in self.tex_rows) + margin))
        self.edges = [0]
        for width in widths:
            self.edges.append(self.edges[-1] + width)
        self.header.configure(height=self.header_height,
                              scrollregion=(0, 0, self.edges[-1], self.header_height))
        self.rowconfigure(0, minsize=self.header_height)
        self.body.configure(scrollregion=(0, 0, self.edges[-1], len(self.row_images) * self.row_height),
                            yscrollincrement=self.row_height)
        self.body.xview_moveto(0)
        self.body.yview_moveto(0)
        self._schedule_draw()

    def xview(self, *args):
        result = self.body.xview(*args)
        if args:
            self._schedule_draw()
        return result

    def yview(self, *args):
        result = self.body.yview(*args)
        if args:
            self._schedule_draw()
        return result

    def _xscroll(self, first, last):
        self.sx.set(first, last)
        self.header.xview_moveto(float(first))
        self._schedule_draw()

    def _yscroll(self, first, last):
        self.sy.set(first, last)
        self._schedule_draw()

    def _wheel(self, event):
        if not event.delta:
            return 'break'
        amount = -int(event.delta) if sys.platform == 'darwin' else (-1 if event.delta > 0 else 1) * max(1, abs(int(event.delta)) // 120)
        if event.state & 1:
            self.xview('scroll', amount, 'units')
        else:
            self.yview('scroll', amount, 'units')
        return 'break'

    def _schedule_draw(self, _event=None):
        if self._redraw_timer is None:
            self._redraw_timer = self.after_idle(self._draw)

    def _cell(self, canvas, bounds, image, background):
        x0, y0, x1, y1 = bounds
        canvas.create_rectangle(*bounds, fill=background, outline=self.border, tags='cells')
        if image is None:
            return None
        return canvas.create_image((x0 + x1) / 2, (y0 + y1) / 2,
                                   image=image, anchor='center', tags='cells')

    def _draw(self):
        self._redraw_timer = None
        if self.table is None:
            return
        self.header.delete('cells')
        self.body.delete('cells')
        self.header_cells.clear()
        self.body_cells.clear()
        first_col = max(0, bisect_right(self.edges, self.body.canvasx(0)) - 1)
        last_col = min(len(self.heading_images), bisect_right(self.edges, self.body.canvasx(self.body.winfo_width())))
        for c in range(first_col, last_col):
            bounds = (self.edges[c], 0, self.edges[c + 1], self.header_height)
            item = self._cell(self.header, bounds, self.heading_images[c], self.header_background)
            self.header_cells[c] = (item, bounds)
        first_row = max(0, int(self.body.canvasy(0) // self.row_height))
        last_row = min(len(self.row_images), int(self.body.canvasy(self.body.winfo_height()) // self.row_height) + 1)
        for r in range(first_row, last_row):
            for c in range(first_col, last_col):
                image = self.row_images[r] if c == 0 else self.value_images[self.tex_rows[r][c - 1]]
                bounds = (self.edges[c], r * self.row_height, self.edges[c + 1], (r + 1) * self.row_height)
                item = self._cell(self.body, bounds, image, self.background)
                self.body_cells[r, c] = (item, bounds)

    def validate_geometry(self):
        """Check allocated header height and each drawn image's real Tk bounds."""
        assert self.header.winfo_height() >= self.header_height
        for canvas, cells in ((self.header, self.header_cells), (self.body, self.body_cells)):
            for item, bounds in cells.values():
                if item is None:
                    continue
                actual = canvas.bbox(item)
                assert actual is not None
                x0, y0, x1, y1 = bounds
                a0, b0, a1, b1 = actual
                assert a0 >= x0 + self.padding - 1 and a1 <= x1 - self.padding + 1, (bounds, actual)
                assert b0 >= y0 + self.padding - 1 and b1 <= y1 - self.padding + 1, (bounds, actual)
                assert abs((a0 + a1) / 2 - (x0 + x1) / 2) <= 1
                assert abs((b0 + b1) / 2 - (y0 + y1) / 2) <= 1
        # Compare real pixel origins; native Tk may format normalized view
        # fractions differently even when cell borders are aligned.
        assert abs(self.header.canvasx(0) - self.body.canvasx(0)) <= 1, (
            self.header.canvasx(0), self.body.canvasx(0),
            self.header.xview(), self.body.xview(),
            self.header.winfo_width(), self.body.winfo_width())
