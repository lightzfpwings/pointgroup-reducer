"""Real native Tk checks for typesetting, language switching and navigation."""
import json
import os
from pathlib import Path
import tempfile
from unittest.mock import patch
import tkinter as tk
from gui import App
from i18n import LANGUAGES, tr
from math_display import decomposition_tex, symbol_tex


def run():
    with tempfile.TemporaryDirectory(prefix='pointgroup-qa-') as temp:
        with patch.dict(os.environ, {'POINTGROUP_SETTINGS_PATH': str(Path(temp) / 'settings.json')}):
            root = tk.Tk()
            root.withdraw()
            callback_errors = []
            root.report_callback_exception = lambda *error: callback_errors.append(error)
            try:
                app = App(root, language='zh-Hans')
                for language in LANGUAGES:
                    app.set_language(language)
                    app.show_stage('select')
                    app.next_input()
                    app.example()
                    assert app.stage == 'input'
                    draft = [value.get() for value in app.fields]
                    app.bulk.insert(0, '5,1,1,1')
                    app.set_language(language)
                    assert [value.get() for value in app.fields] == draft
                    assert app.bulk.get() == '5,1,1,1'
                    app.calculate()
                    result = app.result
                    assert result['valid'] and app.stage == 'result'
                    assert decomposition_tex(app.table, result) == r'\Gamma = 2A_{1} + A_{2} + B_{1} + B_{2}'
                    assert len(app.output.image_names()) >= 11
                    app.copy_result(True)
                    assert r'\Gamma = 2A_{1}' in root.clipboard_get()
                    app.copy_result(False)
                    assert '2A1 + A2 + B1 + B2' in root.clipboard_get()
                    app.set_language(language)
                    assert app.result is result
                    assert app.instruction.get() == tr('result_instruction', language)
                    app.back()
                    assert [value.get() for value in app.fields] == draft
                    app.fields[1].set('bad')
                    app.calculate()
                    assert app.stage == 'input' and app.table.classes[1] in app.status.get()
                    app.set_language('en')
                    assert 'Cannot parse' in app.status.get() and 'Use numbers' in app.status.get()
                    app.set_language('zh-Hant')
                    assert '欄的輸入無法解析' in app.status.get()
                    app.example()
                    app.calculate()
                    target = Path(temp) / 'result.json'
                    with patch('gui.filedialog.asksaveasfilename', return_value=str(target)):
                        app.export()
                    assert json.loads(target.read_text(encoding='utf-8'))['result']['valid']
                    app.help()
                    window, text = app.help_windows[-1]
                    app.set_language('en')
                    assert 'Workflow' in text.get('1.0', 'end') and len(text.image_names()) >= 6
                    app.set_language('zh-Hant')
                    assert '操作步驟' in text.get('1.0', 'end')
                    window.destroy()
                    app.home()
                    assert app.stage == 'home'
                for group in ('D6h', 'Cs', 'C3', 'Th', 'Ih'):
                    app.group.set(group)
                    app.next_input()
                    root.deiconify()
                    settled = tk.BooleanVar(root, False)
                    root.after(350, lambda: settled.set(True))
                    root.wait_variable(settled)
                    root.update_idletasks()
                    # Check actual allocated geometry, not just requested sizes.
                    group_image = app.math.image(symbol_tex(group), 16)
                    assert group_image.transparency_get(0, 0)
                    assert app.group_image.winfo_height() >= group_image.height(), (
                        group, app.group_image.winfo_geometry(), group_image.height(),
                        app.group_image.winfo_reqheight(), root.state(), root.winfo_geometry(),
                        app.host.winfo_geometry(), app.workspace.winfo_geometry(),
                        app.page_motion.positions)
                    assert app.canvas.winfo_height() >= app.inputs.winfo_reqheight()
                    from tkinter import ttk
                    rowheight = int(ttk.Style(root).lookup('Treeview', 'rowheight'))
                    for label in app.table.irreps:
                        image = app.math.image(symbol_tex(label))
                        assert image.transparency_get(0, 0)
                        assert rowheight >= image.height() + 8
                    app.example()
                    app.calculate()
                    assert app.result['valid'], group
                    assert len(app.output.image_names()) > 0
                    root.update()
                # Navigate rapidly, resize mid-transition, then let the last request settle.
                draft = [value.get() for value in app.fields]
                app.show_stage('input')
                app.show_stage('select')
                app.show_stage('result')
                root.geometry('1050x760')
                root.after(30, lambda: root.geometry('1200x840'))
                settled = tk.BooleanVar(root, False)
                root.after(400, lambda: settled.set(True))
                root.wait_variable(settled)
                assert app.body_motion.current is app.resultpage
                assert app.body_motion.timer is None and app.page_motion.timer is None
                assert app.resultpage.winfo_x() == 0
                assert abs(app.resultpage.winfo_width() - app.content.winfo_width()) <= 1
                assert [value.get() for value in app.fields] == draft
                assert app.selectpage.winfo_manager() == ''
                assert app.inputpage.winfo_manager() == ''
                app.show_stage('input')
                app.motion_enabled.set(False)
                app.toggle_motion()
                assert app.body_motion.timer is None
                assert app.body_motion.current is app.inputpage
                app.home()
                assert app.page_motion.timer is None
                app.group.set('C1')
                app.next_input()
                app.fields[0].set('1/2')
                app.calculate()
                assert not app.result['valid'] and 'Gamma' not in app.output.get('1.0', 'end')
                app.fields[0].set('0')
                app.calculate()
                assert app.result['valid'] and decomposition_tex(app.table, app.result) == r'\Gamma = 0'
                root.update()
                app.motion_enabled.set(True)
                app.toggle_motion()
                app.home()
                root.update_idletasks()
                app.show_stage('select')
            finally:
                root.destroy()
            assert not callback_errors, callback_errors


if __name__ == '__main__':
    run()
