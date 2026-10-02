"""Interruptible page transitions driven by Tk's event loop, never by sleep."""
from time import monotonic


def ease_out_cubic(progress):
    return 1 - (1 - min(1, max(0, progress))) ** 3


class SlideStack:
    """Keep live pages mounted; move them in a clipped parent viewport.

    Positions are fractions of the current viewport width, so resizing during
    an animation needs no screenshot, rerender, or competing geometry tween.
    A new destination cancels the timer, retaining the exact current positions.
    """
    def __init__(self, host, duration=.22, clock=monotonic):
        self.host, self.duration, self.clock = host, duration, clock
        self.current = None
        self.positions = {}
        self.enabled = True
        self.timer = None
        self.generation = 0
        host.bind('<Destroy>', self._destroy, add='+')

    def _destroy(self, event):
        if event.widget is self.host:
            self._cancel()

    def _cancel(self):
        self.generation += 1
        if self.timer is not None:
            self.host.after_cancel(self.timer)
            self.timer = None

    def finish(self):
        self._cancel()
        for page in tuple(self.positions):
            if page is not self.current:
                page.place_forget()
        self.positions = {}
        if self.current is not None:
            self._place(self.current, 0)

    def set_enabled(self, enabled):
        self.enabled = enabled
        if not enabled:
            self.finish()

    def _place(self, page, position):
        self.positions[page] = position
        page.place(relx=position, y=0, relwidth=1, relheight=1)

    def show(self, page, direction=1, animate=True):
        if page is self.current:
            return
        previous = self.current
        self._cancel()
        self.current = page
        if (previous is None or not animate or not self.enabled
                or not self.host.winfo_viewable() or self.host.winfo_width() <= 1):
            self.finish()
            return
        if page not in self.positions:
            self._place(page, direction)
        page.lift()
        starts = dict(self.positions)
        started = self.clock()
        generation = self.generation

        def frame():
            if generation != self.generation:
                return
            self.timer = None
            progress = (self.clock() - started) / self.duration
            if progress >= 1:
                self.finish()
                return
            weight = ease_out_cubic(progress)
            for widget, start in starts.items():
                end = 0 if widget is page else -direction
                self._place(widget, start + (end - start) * weight)
            self.timer = self.host.after(16, frame)

        frame()
