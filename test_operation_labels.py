"""Validate displayed operations against independently reconstructed matrices."""
from fractions import Fraction
import math
import re
import unittest

import numpy as np

from core import _build_table, get_table, payload
from i18n import LANGUAGES, group_notes, tr
from math_display import symbol_tex


def matrix_from_label(label):
    if label == 'E':
        return np.eye(3)
    if label == 'i':
        return -np.eye(3)
    rotation = re.fullmatch(r'([CS])(\d+)(?:\^(\d+))?', label)
    if rotation:
        kind, order, power = rotation.groups()
        theta = 2 * math.pi * int(power or 1) / int(order)
        c, s = math.cos(theta), math.sin(theta)
        return np.array([[c, -s, 0], [s, c, 0],
                         [0, 0, -1 if kind == 'S' else 1]])
    if label == 'sigma_h(xy)':
        return np.diag([1, 1, -1])
    match = re.fullmatch(r"(C2'{0,2}|sigma_[vd])\((.*)\)", label)
    kind, orientation = match.groups()
    if orientation in ('x', 'xz'):
        angle = Fraction(0)
    elif orientation in ('y', 'yz'):
        angle = Fraction(1, 2)
    else:
        azimuth = re.fullmatch(r'phi=(?:(\d+)\*)?pi/(\d+)', orientation)
        angle = Fraction(int(azimuth[1] or 1), int(azimuth[2]))
    phi = math.pi * float(angle)
    axis = np.array([math.cos(phi), math.sin(phi), 0])
    if kind.startswith('C'):
        return 2 * np.outer(axis, axis) - np.eye(3)
    normal = np.array([-math.sin(phi), math.cos(phi), 0])
    return np.eye(3) - 2 * np.outer(normal, normal)


class OperationLabelTests(unittest.TestCase):
    def test_c2v_uses_two_explicit_vertical_planes(self):
        table = get_table('C2v')
        self.assertEqual(table.classes,
                         ['E', 'C2', 'sigma_v(xz)', 'sigma_v(yz)'])
        np.testing.assert_allclose(table.reps[3], np.diag([-1, 1, 1]), atol=1e-14)
        self.assertEqual(table.decomposition(table.reduce([5, 1, 1, 1])),
                         'Γ = 2A1 + A2 + B1 + B2')

    def test_known_classes_keep_their_coordinate_meaning(self):
        expected = {
            'C4v': ['E', 'C4', 'C2', 'sigma_v(xz)', 'sigma_d(phi=pi/4)'],
            'D2': ['E', 'C2', 'C2(x)', 'C2(y)'],
            'C2h': ['E', 'C2', 'i', 'sigma_h(xy)'],
            'S6': ['E', 'S6', 'C3', 'i', 'C3^2', 'S6^5'],
        }
        for group, classes in expected.items():
            self.assertEqual(get_table(group).classes, classes, group)
        table = get_table('D6h')
        self.assertEqual(table.classes[-2:],
                         ['sigma_d(yz)', 'sigma_v(phi=2*pi/3)'])

    def test_axial_labels_reconstruct_the_actual_operations(self):
        groups = ['C1', 'Cs', 'Ci']
        groups += [f'{family}{n}{suffix}' for n in range(2, 31)
                   for family, suffix in [('C', ''), ('C', 'v'), ('C', 'h'),
                                          ('D', ''), ('D', 'h'), ('D', 'd')]]
        groups += [f'S{2*n}' for n in range(2, 31)]
        for group in groups:
            table = get_table(group)
            self.assertEqual(len(set(table.classes)), len(table.classes), group)
            for label, matrix in zip(table.classes, table.reps):
                with self.subTest(group=group, operation=label):
                    np.testing.assert_allclose(matrix_from_label(label), matrix,
                                               atol=2e-13)

    def test_names_preserve_class_order_and_character_data(self):
        for group in ('C2v', 'D6h', 'D4d', 'C7h', 'S10', 'Th', 'Oh', 'Ih'):
            before, after = _build_table(group), get_table(group)
            np.testing.assert_array_equal(after.X, before.X)
            np.testing.assert_array_equal(after.W, before.W)
            np.testing.assert_array_equal(after.reps, before.reps)
            self.assertEqual(after.irreps, before.irreps)
            self.assertEqual(after.symbolic_rows(), before.symbolic_rows())
            self.assertEqual(after.h, before.h)
            self.assertFalse(any('·' in label for label in after.classes))
            self.assertEqual(payload(after)['classes'], after.classes)

    def test_polyhedral_labels_preserve_angle_and_parity(self):
        for group in ('Th', 'Oh', 'Ih'):
            table = get_table(group)
            half = len(table.classes) // 2
            for label, representative in zip(table.classes[half:], table.reps[half:]):
                matrix = (np.diag([1, 1, -1]) if label.startswith('sigma')
                          else matrix_from_label(label))
                self.assertAlmostEqual(np.trace(matrix), np.trace(representative), places=12)
                self.assertAlmostEqual(np.linalg.det(matrix), np.linalg.det(representative), places=12)

    def test_axis_conventions_are_available_in_all_languages(self):
        for language in LANGUAGES:
            for group in ('C3', 'C6v', 'D6h', 'D4d', 'S8'):
                self.assertIn(tr('axis_convention', language),
                              group_notes(get_table(group), language))
            for group in ('C1', 'Cs', 'Ci'):
                self.assertNotIn(tr('axis_convention', language),
                                 group_notes(get_table(group), language))
            for group in ('T', 'Th', 'Td', 'O', 'Oh', 'I', 'Ih'):
                self.assertIn(tr('polyhedral_note', language),
                              group_notes(get_table(group), language))

    def test_exact_azimuth_and_plain_mirror_render_as_math(self):
        self.assertEqual(symbol_tex('sigma'), r'\sigma')
        self.assertEqual(symbol_tex('sigma_d(phi=pi/4)'),
                         r'\sigma_{d}\,(\varphi=\frac{\pi}{4})')
        self.assertEqual(symbol_tex("C2''(phi=2*pi/5)"),
                         r"C_{2}^{''}\,(\varphi=\frac{2\pi}{5})")


if __name__ == '__main__':
    unittest.main()
