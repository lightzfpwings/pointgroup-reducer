"""Native GUI startup check used by the packaging workflow."""
import tkinter as tk
from gui import App


def run():
    root = tk.Tk()
    root.withdraw()
    try:
        app = App(root)
        app.show_stage('select')
        app.next_input()
        app.example()
        assert app.stage == 'input'
        app.calculate()
        assert app.result['valid'] and app.stage == 'result'
        assert '2A1 + A2 + B1 + B2' in app.output.get('1.0', 'end')
        app.back()
        assert [value.get() for value in app.fields] == ['5', '1', '1', '1']
        app.fields[1].set('bad')
        app.calculate()
        assert app.stage == 'input' and app.table.classes[1] in app.status.get()
        app.home()
        assert app.stage == 'home'
        root.update()
    finally:
        root.destroy()


if __name__ == '__main__':
    run()
