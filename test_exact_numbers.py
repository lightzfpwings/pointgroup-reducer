"""Exact display provenance and independent numerical equivalence checks."""
import csv
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest
import numpy as np
import sympy as s
from core import get_table, number, parse_vector, fmt, payload
from exact_numbers import expression, result_values
from gui import parse_fields
from math_display import number_tex, result_latex, render_png


class ExactDisplayTests(unittest.TestCase):
    def test_table_families_match_numeric_characters(self):
        groups = ['C1','Cs','Ci','T','Th','Td','O','Oh','I','Ih']
        groups += [f'{f}{n}{suffix}' for n in (2,3,5,7,8,12,13)
                   for f,suffix in [('C',''),('C','v'),('C','h'),('D',''),('D','h'),('D','d'),('S','')]]
        for group in groups:
            t = get_table(group)
            exact = t.symbolic_rows()
            with self.subTest(group=group):
                np.testing.assert_allclose([[complex(z.evalf()) for z in row] for row in exact], t.X, atol=1e-12)
                self.assertFalse(any(z.has(s.Float) for row in exact for z in row))

    def test_radicals_trig_and_complex_parts(self):
        self.assertEqual(get_table('D8').symbolic(4,1), s.sqrt(2))
        self.assertEqual(get_table('C3').symbolic(1,1), -s.Rational(1,2)+s.sqrt(3)*s.I/2)
        self.assertEqual(get_table('Ih').symbolic(1,1), (1+s.sqrt(5))/2)
        self.assertIn('cos', fmt(get_table('D7').symbolic(2,1)))
        self.assertIn('√2', fmt(get_table('D8').symbolic(4,1)))
        self.assertNotIn('1.414', fmt(get_table('D8').symbolic(4,1)))

    def test_safe_parser_preserves_input_not_decimal_guesses(self):
        samples = ['sqrt(2)','cos(2*pi/7)','exp(2*pi*i/3)', 'sqrt(2)+sqrt(3)*i/2', '1/3', '0x10']
        for text in samples:
            z = number(text)
            self.assertEqual(s.simplify(expression(number(fmt(z)))-expression(z)), 0)
            self.assertAlmostEqual(complex(expression(z).evalf()), complex(z))
        self.assertEqual(expression(number('1.414')), s.Rational(707,500))
        for text in ["__import__('os')", 'sqrt(x)', 'sin(1,2)', '(1).__class__']:
            with self.assertRaises(ValueError): number(text)

    def test_vectors_and_near_integer_coefficients_stay_exact(self):
        t = get_table('C1')
        for values in (parse_vector('sqrt(2)'), parse_fields(t,['sqrt(2)'])):
            r = t.reduce(values)
            self.assertEqual(result_values(t,r,'a'), [s.sqrt(2)])
            self.assertIn(r'\sqrt{2}', result_latex(t,r))
        r = t.reduce(parse_vector('0.99999999'))
        self.assertTrue(r['valid'])
        self.assertEqual(result_values(t,r,'a'), [s.Rational(99999999,100000000)])

    def test_orbital_examples_keep_exact_values(self):
        for name in ('C3','C7','C8','D4d','D6h','S8','Th','Ih','Cs','Ci'):
            t = get_table(name)
            for l in (0,1,2,3):
                values = t.orbital_exact(l)
                np.testing.assert_allclose([complex(expression(z).evalf()) for z in values], t.orbital(l), atol=1e-11)
                self.assertFalse(any(expression(z).has(s.Float) for z in values))
        t=get_table('C3')
        r=t.reduce(parse_vector('1,exp(2*pi*i/3),exp(-2*pi*i/3)'))
        self.assertEqual(result_values(t,r,'a'),[0,1,0])

    def test_tex_and_json_keep_symbolic_forms(self):
        for text in ('sqrt(2)','cos(2*pi/7)','sqrt(2)+sqrt(3)*i/2','exp(2*pi*i/3)'):
            tex=number_tex(number(text))
            self.assertTrue(render_png(tex).startswith(b'\x89PNG'))
        t=get_table('C1'); r=t.reduce(parse_vector('sqrt(2)+sqrt(3)*i/2'))
        data=json.loads(json.dumps(payload(t,r)))
        self.assertIn('√2',data['result']['symbolic']['c'][0])
        self.assertIn('im',data['result']['c'][0])
        self.assertIn('√2',payload(get_table('D8'))['X_symbolic'][4][1])

    def test_cli_and_csv_show_symbols(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'table.csv'
            proc=subprocess.run([sys.executable,'pointgroup.py','D8','--table','--csv',str(target)], capture_output=True,text=True,check=True)
            self.assertIn('√2',proc.stdout)
            self.assertNotIn('1.414',proc.stdout)
            self.assertIn('√2',target.read_text(encoding='utf-8-sig'))


if __name__ == '__main__': unittest.main()
