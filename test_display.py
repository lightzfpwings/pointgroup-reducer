"""Independent notation, localization and preference regressions."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from core import get_table
from gui import parse_fields
from i18n import LANGUAGES, MESSAGES, ERRORS, tr, error_text, group_notes
from math_display import symbol_tex, decomposition_tex, FORMULA, result_latex, render_png
from preferences import load_language, save_language
from matplotlib.mathtext import MathTextParser


class DisplayTests(unittest.TestCase):
    def test_math_background_is_transparent_and_glyphs_have_clear_margins(self):
        from io import BytesIO
        from PIL import Image
        import numpy as np
        for dpi in (96, 110, 144, 192):
            for tex in (symbol_tex('D6h'), symbol_tex('C6^2'), symbol_tex("A''"),
                        symbol_tex('E1+g'), FORMULA):
                with self.subTest(tex=tex, dpi=dpi):
                    image = Image.open(BytesIO(render_png(tex, 16, dpi))).convert('RGBA')
                    alpha = np.array(image)[:, :, 3]
                    self.assertGreater(alpha.max(), 0)
                    # Real transparent padding, not white pixels that clash with ttk.
                    self.assertFalse(alpha[:3, :].any())
                    self.assertFalse(alpha[-3:, :].any())
                    self.assertFalse(alpha[:, :3].any())
                    self.assertFalse(alpha[:, -3:].any())
                    self.assertTrue(((alpha > 0) & (alpha < 255)).any())

    def test_notation_preserves_parity_signs_powers_and_primes(self):
        cases = {'D6h': 'D_{6h}', 'A1g': 'A_{1g}', 'C6^2': 'C_{6}^{2}',
                 'E1+g': 'E_{1g}^{+}', "A''": "A^{''}", 'sigma_h': r'\sigma_{h}',
                 'i·(C6^2)': r'i\,\cdot\,(C_{6}^{2})'}
        for label, expected in cases.items():
            self.assertEqual(symbol_tex(label), expected)

    def test_generated_labels_are_renderable(self):
        parser = MathTextParser('path')
        groups = ['C1', 'Cs', 'Ci', 'T', 'Th', 'Td', 'O', 'Oh', 'I', 'Ih']
        groups += [f'{family}{n}{suffix}' for n in range(2, 13)
                   for family, suffix in [('C',''), ('C','v'), ('C','h'), ('D',''), ('D','h'), ('D','d'), ('S','')]]
        expressions = {FORMULA}
        for name in groups:
            table = get_table(name)
            expressions.update(symbol_tex(x) for x in [table.name] + table.classes + table.irreps)
            result = table.reduce(table.orbital(2))
            expressions.add(decomposition_tex(table, result))
        for expr in expressions:
            with self.subTest(tex=expr):
                parser.parse('$' + expr + '$', dpi=96)
        self.assertTrue(render_png(FORMULA).startswith(b'\x89PNG'))

    def test_copy_latex_uses_full_vectors_and_valid_decomposition(self):
        table = get_table('D4h')
        result = table.reduce(table.orbital(2))
        tex = result_latex(table, result)
        self.assertIn(r'A_{1g} + B_{1g} + B_{2g} + E_{g}', tex)
        self.assertIn(r'\begin{pmatrix}', tex)
        table = get_table('C1')
        self.assertNotIn(r'\Gamma', result_latex(table, table.reduce([.5])))
        self.assertIn(r'\Gamma = 0', result_latex(table, table.reduce([0])))

    def test_catalog_complete_and_placeholders_match(self):
        from string import Formatter
        for key, texts in MESSAGES.items():
            self.assertEqual(len(texts), 3, key)
            fields = [{field for _, field, _, _ in Formatter().parse(text) if field is not None} for text in texts]
            self.assertEqual(fields[0], fields[1], key)
            self.assertEqual(fields[0], fields[2], key)
            self.assertTrue(all(text.strip() for text in texts), key)

    def test_errors_and_group_notes_localized(self):
        for source in ERRORS:
            self.assertFalse(any('\u4e00' <= char <= '\u9fff' for char in error_text(source, 'en')))
        for group in ('D6h','C3','Th'):
            self.assertFalse(any('\u4e00' <= char <= '\u9fff' for char in group_notes(get_table(group), 'en')))
        for language in LANGUAGES:
            with self.assertRaisesRegex(ValueError, 'C2'):
                parse_fields(get_table('C2v'), ['5','bad','1','1'], language)

    def test_cli_all_languages_and_switch_keeps_calculation(self):
        import subprocess
        import sys
        from interactive import run
        for language in LANGUAGES:
            completed = subprocess.run([sys.executable, 'pointgroup.py', 'C2v', '--c', '5,1,1,1', '--lang', language],
                                       capture_output=True, encoding='utf-8', check=True)
            self.assertIn('2A1 + A2 + B1 + B2', completed.stdout)
            self.assertIn(tr('dimension', language), completed.stdout)
            help_result = subprocess.run([sys.executable, 'pointgroup.py', '--help', '--lang', language],
                                        capture_output=True, encoding='utf-8', check=True)
            self.assertIn(tr('arg_gui', language), help_result.stdout)
        with tempfile.TemporaryDirectory() as temp:
            with patch.dict(os.environ, {'POINTGROUP_SETTINGS_PATH': str(Path(temp) / 'settings.json')}):
                commands = iter(['C2v', 'd', 'lang', 'en', 'lang', 'zh-Hant', 'q'])
                output=[]
                run(read=lambda _: next(commands), write=output.append)
                text='\n'.join(output)
                self.assertIn('Representation dimension', text)
                self.assertIn('表示維度', text)
                self.assertEqual(text.count('Γ = 2A1 + A2 + B1 + B2'), 3)

    def test_cli_invalid_counts_and_conflicting_options(self):
        import subprocess
        import sys
        for language in LANGUAGES:
            for arguments, expected in [(['--c', '5,1,1,1', '--shell', '2'], tr('arg_conflict', language)),
                                        (['--c', '5,1'], tr('need_count', language, count=4))]:
                completed = subprocess.run([sys.executable, 'pointgroup.py', 'C2v', '--lang', language] + arguments,
                                           capture_output=True, encoding='utf-8')
                self.assertEqual(completed.returncode, 1)
                self.assertIn(expected, completed.stderr)
                self.assertNotIn('Traceback', completed.stderr)

    def test_preferences_persist_and_handle_corrupt_file(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'settings.json'
            with patch.dict(os.environ, {'POINTGROUP_SETTINGS_PATH': str(path)}):
                self.assertEqual(load_language(), 'zh-Hans')
                for language in LANGUAGES:
                    self.assertTrue(save_language(language))
                    self.assertEqual(load_language(), language)
                for contents in ('invalid', '[]', 'null', '{"language":"unknown"}'):
                    path.write_text(contents)
                    self.assertEqual(load_language(), 'zh-Hans')
