"""Navigation timing tests use a deterministic event loop, not wall-clock sleeps."""
import unittest
from motion import SlideStack, ease_out_cubic


class Host:
    def __init__(self):
        self.time = 0
        self.pending = {}
        self.serial = 0

    def bind(self, *args, **kwargs):
        pass

    def winfo_viewable(self):
        return True

    def winfo_width(self):
        return 1000

    def after(self, milliseconds, callback):
        self.serial += 1
        self.pending[self.serial] = callback
        return self.serial

    def after_cancel(self, identifier):
        self.pending.pop(identifier, None)

    def advance(self, seconds):
        self.time += seconds
        callbacks = list(self.pending.values())
        self.pending.clear()
        for callback in callbacks:
            callback()


class Page:
    def __init__(self):
        self.x = None

    def place(self, **options):
        self.x = options['relx']

    def place_forget(self):
        self.x = None

    def lift(self):
        pass


class MotionTests(unittest.TestCase):
    def setUp(self):
        self.host = Host()
        self.motion = SlideStack(self.host, clock=lambda: self.host.time)
        self.a, self.b, self.c = Page(), Page(), Page()
        self.motion.show(self.a)

    def test_easing_is_monotonic_and_decelerates(self):
        values = [ease_out_cubic(n / 10) for n in range(11)]
        self.assertEqual((values[0], values[-1]), (0, 1))
        increments = [b - a for a, b in zip(values, values[1:])]
        self.assertTrue(all(step > 0 for step in increments))
        self.assertEqual(increments, sorted(increments, reverse=True))

    def test_return_reverses_without_position_jump_or_queued_animations(self):
        self.motion.show(self.b)
        self.host.advance(.08)
        positions = self.a.x, self.b.x
        self.motion.show(self.a, direction=-1)
        self.assertEqual((self.a.x, self.b.x), positions)
        self.assertEqual(len(self.host.pending), 1)
        self.host.advance(.3)
        self.assertEqual(self.a.x, 0)
        self.assertIsNone(self.b.x)
        self.assertFalse(self.host.pending)

    def test_rapid_navigation_finishes_only_at_latest_destination(self):
        for page in (self.b, self.c, self.a, self.b):
            self.motion.show(page)
            self.host.advance(.03)
        self.host.advance(.3)
        self.assertEqual(self.b.x, 0)
        self.assertIsNone(self.a.x)
        self.assertIsNone(self.c.x)
        self.assertFalse(self.host.pending)

    def test_late_frame_catches_up_instead_of_extending_animation(self):
        self.motion.show(self.b)
        self.host.advance(1)
        self.assertEqual(self.b.x, 0)
        self.assertFalse(self.host.pending)

    def test_disable_mid_transition_finishes_and_stops_callbacks(self):
        self.motion.show(self.b)
        self.host.advance(.05)
        self.motion.set_enabled(False)
        self.assertEqual(self.b.x, 0)
        self.assertFalse(self.host.pending)
        self.motion.show(self.c)
        self.assertEqual(self.c.x, 0)
        self.assertFalse(self.host.pending)
