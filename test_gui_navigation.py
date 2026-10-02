"""Test navigation and input feedback without claiming native rendering QA."""
import unittest
from unittest.mock import Mock
import numpy as np
from core import get_table
from gui import App, STAGES, parse_fields


class GuiNavigationTests(unittest.TestCase):
    def app(self):
        app = App.__new__(App)
        for name in ['homepage', 'workspace', 'root', 'controls', 'tableframe', 'inputframe',
                     'bulkframe', 'selectbar', 'inputbar', 'resultbar', 'output', 'statuslabel',
                     'steptext', 'instruction', 'status', 'page_motion', 'body_motion',
                     'selectpage', 'inputpage', 'resultpage']:
            setattr(app, name, Mock())
        app.fields = [Mock() for _ in range(4)]
        for field, value in zip(app.fields, ['5', '1', '1', '1']):
            field.get.return_value = value
        app.entries = [Mock() for _ in range(4)]
        app.table = get_table('C2v')
        app.group = Mock()
        app.group.get.return_value = 'C2v'
        app.bulk = Mock()
        app.bulk.get.return_value = ''
        app.result = app.table.reduce([5, 1, 1, 1])
        app.stage = 'home'
        return app

    def test_back_preserves_draft_and_result(self):
        app = self.app()
        fields, result = app.fields, app.result
        for current, previous in [('result', 'input'), ('input', 'select'), ('select', 'home'), ('home', 'home')]:
            app.show_stage(current)
            app.back()
            self.assertEqual(app.stage, previous)
            self.assertIs(app.fields, fields)
            self.assertIs(app.result, result)

    def test_each_stage_has_its_own_instruction(self):
        app = self.app()
        for stage, (_, instruction) in STAGES.items():
            app.show_stage(stage)
            app.instruction.set.assert_called_with(instruction)
        app.home()
        self.assertEqual(app.stage, 'home')

    def test_example_fills_only_and_stays_on_input_page(self):
        app = self.app()
        app.stage = 'input'
        app.calculate = Mock()
        app.example()
        app.calculate.assert_not_called()
        self.assertEqual(app.stage, 'input')
        for field, expected in zip(app.fields, ['5', '1', '1', '1']):
            field.set.assert_called_once_with(expected)
        self.assertIn('点击“计算”', app.status.set.call_args.args[0])

    def test_missing_value_identifies_class_and_stays(self):
        app = self.app()
        app.stage = 'input'
        app.fields[2].get.return_value = ''
        app.calculate()
        self.assertEqual(app.stage, 'input')
        self.assertIn(app.table.classes[2], app.status.set.call_args.args[0])
        app.statuslabel.configure.assert_called_with(style='Error.TLabel')

    def test_unapplied_paste_is_not_ignored(self):
        app = self.app()
        app.stage = 'input'
        app.bulk.get.return_value = '1,2'
        app.calculate()
        self.assertEqual(app.stage, 'input')
        self.assertIn('需要 4 个值', app.status.set.call_args.args[0])

    def test_same_group_does_not_clear_draft(self):
        app = self.app()
        app.load()
        self.assertIsNotNone(app.result)
        for field in app.fields:
            field.set.assert_not_called()
        app.bulk.delete.assert_not_called()

    def test_invalid_group_does_not_advance(self):
        app = self.app()
        app.stage = 'select'
        app.group.get.return_value = 'madeup'
        app.next_input()
        self.assertEqual(app.stage, 'select')
        self.assertIn('无法载入点群', app.status.set.call_args.args[0])

    def test_parse_feedback_and_zero(self):
        table = get_table('C2v')
        np.testing.assert_allclose(parse_fields(table, ['0', '0', '0', '0']), [0, 0, 0, 0])
        with self.assertRaisesRegex(ValueError, table.classes[1]):
            parse_fields(table, ['5', 'bad', '1', '1'])
        with self.assertRaises(ValueError):
            parse_fields(table, ['5'])


if __name__ == '__main__':
    unittest.main()

