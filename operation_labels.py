"""Direct names for operations, without changing class order or characters.

Axial matrices share a real coordinate frame, with the principal axis z.
Polyhedral matrices encode angle/parity only: use explicit class names there.
"""
from fractions import Fraction
import math
import re

import numpy as np


def _power(symbol, order, exponent):
    return f'{symbol}{order}' + (f'^{exponent}' if exponent != 1 else '')


def _orientation(angle, plane=False):
    if angle == 0:
        return '(xz)' if plane else '(x)'
    if angle == Fraction(1, 2):
        return '(yz)' if plane else '(y)'
    numerator = '' if angle.numerator == 1 else str(angle.numerator) + '*'
    return f'(phi={numerator}pi/{angle.denominator})'


def axial_label(matrix, name, order):
    """Name a representative using its matrix, including the exact azimuth."""
    family = re.fullmatch(r'([CDS])(\d+)([vhd]?)', name)
    n = int(family[2]) if family else 1
    suffix = family[3] if family else ''
    block = matrix[:2, :2]
    if np.linalg.det(block) > 0:
        turn = Fraction(math.atan2(matrix[1, 0], matrix[0, 0]) /
                        (2 * math.pi)).limit_denominator(2 * order) % 1
        if matrix[2, 2] > 0:
            return 'E' if turn == 0 else _power('C', turn.denominator, turn.numerator)
        if turn == 0:
            return 'sigma_h(xy)'
        if turn == Fraction(1, 2):
            return 'i'
        # An improper power must be odd to retain reflection. When the
        # reduced numerator is even, its denominator is necessarily odd.
        exponent = turn.numerator
        if exponent % 2 == 0:
            exponent += turn.denominator
        return _power('S', turn.denominator, exponent)

    azimuth = Fraction(math.atan2(matrix[1, 0], matrix[0, 0]) /
                       (2 * math.pi)).limit_denominator(2 * order) % 1
    if matrix[2, 2] < 0:
        primes = '' if n == 2 else ("'" if azimuth == 0 else "''")
        return 'C2' + primes + _orientation(azimuth)
    diagonal = suffix == 'd' or (n > 2 and n % 2 == 0 and
                                (azimuth * n).denominator == 1 and
                                (azimuth * n).numerator % 2 == 1)
    return ('sigma_d' if diagonal else 'sigma_v') + _orientation(azimuth, plane=True)


def direct_labels(table):
    if table.name.startswith(('T', 'O', 'I')):
        # Match the original central-product column order. Powers preserve
        # the actual representative, particularly the two distinct Th C3s.
        reflected = {
            'Th': ['i', 'S6^5', 'S6', 'sigma_h'],
            'Oh': ['i', 'S6^5', 'sigma_h', 'S4^3', 'sigma_d'],
            'Ih': ['i', 'S10^7', 'S10^9', 'S6^5', 'sigma'],
        }
        if table.name in reflected:
            half = len(table.classes) // 2
            return table.classes[:half] + reflected[table.name]
        return table.classes
    return [axial_label(matrix, table.name, table.h) for matrix in table.reps]
