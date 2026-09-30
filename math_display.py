"""TeX notation and offline MathText rendering; no external LaTeX process."""
import base64
from functools import lru_cache
from io import BytesIO
import os
import re
import tempfile
import tkinter as tk

# Use a writable private cache even in a frozen app or read-only workspace.
os.environ.setdefault('MPLCONFIGDIR', os.path.join(tempfile.gettempdir(), 'pointgroup-mathtext'))
import matplotlib
matplotlib.use('Agg')
from matplotlib.font_manager import FontProperties
from matplotlib.mathtext import math_to_image
from core import fmt

FORMULA = r'\mathbf{a}=\frac{1}{h}X^{*}W\mathbf{c}'


def symbol_tex(label):
    """Convert canonical program labels without changing their mathematical meaning."""
    if '·' in label:
        return r'\,\cdot\,'.join(symbol_tex(x) for x in label.split('·'))
    if label.startswith('(') and label.endswith(')'):
        return '(' + symbol_tex(label[1:-1]) + ')'
    if label.startswith('sigma_'):
        match = re.fullmatch(r'sigma_([a-z]+)(.*)', label)
        return r'\sigma_{' + match[1] + '}' + qualifier_tex(match[2])
    # C3(+)/C3(-) distinguish conjugacy classes, not powers.
    match = re.fullmatch(r'([A-Z])([0-9]*)([+-]?)(\'*)([a-z]*)(\^\d+)?(\(.*\))?', label)
    if match:
        letter, digits, sign, primes, suffix, power, qualifier = match.groups()
        sub = digits + suffix
        superscript = (power[1:] if power else '') + sign + primes
        result = letter + ('_{' + sub + '}' if sub else '')
        result += ('^{' + superscript + '}' if superscript else '')
        return result + qualifier_tex(qualifier or '')
    if label == 'i':
        return 'i'
    return r'\mathrm{' + label.replace('_', r'\_') + '}'


def qualifier_tex(text):
    if not text:
        return ''
    if text in ('(+)', '(-)'):
        return text
    return r'\,\mathrm{' + text + '}'


def number_tex(z, digits=12):
    return re.sub(r'([-+]?(?:\d+(?:\.\d*)?|\.\d+))e([-+]?\d+)',
                  lambda m: m[1] + r'\times 10^{' + str(int(m[2])) + '}', fmt(z, digits))


def decomposition_terms(table, result):
    return [(str(int(n)) if int(n) != 1 else '') + symbol_tex(label)
            for label, n in zip(table.irreps, result['integer_a']) if int(n)]


def decomposition_tex(table, result):
    if not result['valid']:
        return ''
    return r'\Gamma = ' + (' + '.join(decomposition_terms(table, result)) or '0')


def result_latex(table, result):
    """Copyable full LaTeX, rather than the rendered bitmap or rounded integers."""
    def vector(values):
        return r'\begin{pmatrix}' + r' \\ '.join(number_tex(z, 15) for z in values) + r'\end{pmatrix}'
    lines = [r'\[', FORMULA, r'\]', r'\[', r'\mathbf{c}=' + vector(result['c']),
             r',\qquad \mathbf{a}=' + vector(result['a']), r'\]']
    if result['valid']:
        lines.extend([r'\[', decomposition_tex(table, result), r'\]'])
    return '\n'.join(lines)


@lru_cache(maxsize=1024)
def render_png(tex, size=12, dpi=110):
    buffer = BytesIO()
    with matplotlib.rc_context({'mathtext.fontset': 'stix', 'text.usetex': False}):
        math_to_image('$' + tex + '$', buffer, prop=FontProperties(size=size), dpi=dpi, format='png')
    return buffer.getvalue()


class MathImages:
    """PhotoImages belong to one Tk interpreter and must stay alive while displayed."""
    def __init__(self, root):
        self.root = root
        self.dpi = max(96, min(192, round(float(root.winfo_fpixels('1i')))))
        self.images = {}

    def image(self, tex, size=12):
        key = (tex, size)
        if key not in self.images:
            self.images[key] = tk.PhotoImage(master=self.root, data=base64.b64encode(render_png(tex, size, self.dpi)))
        return self.images[key]

    def label(self, parent, tex, size=12):
        from tkinter import ttk
        return ttk.Label(parent, image=self.image(tex, size))
