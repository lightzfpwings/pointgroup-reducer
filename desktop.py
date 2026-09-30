"""Windowed application entry point, no console window required."""
import sys
import traceback


def main():
    try:
        if '--smoke-test' in sys.argv[1:]:
            from gui_smoke import run
            run()
            return 0
        from gui import launch
        launch()
    except Exception:
        details=traceback.format_exc()
        try:
            import os
            from pathlib import Path
            folder=(Path.home()/'Library'/'Logs'/'PointGroupReducer' if sys.platform == 'darwin' else Path(os.environ.get('LOCALAPPDATA',str(Path.home())))/'PointGroupReducer')
            folder.mkdir(parents=True,exist_ok=True)
            (folder/'startup-error.log').write_text(details,encoding='utf-8')
            details+='\n错误日志：'+str(folder/'startup-error.log')
        except OSError:pass
        try:
            import tkinter as tk
            from tkinter import messagebox
            root=tk.Tk();root.withdraw()
            messagebox.showerror('Point Group Reducer — 启动失败',details)
            root.destroy()
        except Exception:
            if sys.platform=='win32':
                import ctypes
                ctypes.windll.user32.MessageBoxW(None,details,'Point Group Reducer — 启动失败',16)
            elif sys.platform=='darwin':
                import subprocess
                subprocess.run(['/usr/bin/osascript','-e',
                    'on run argv\n display alert "Point Group Reducer — 启动失败" message (item 1 of argv) as critical\nend run',
                    details],check=False)
            elif sys.stderr:sys.stderr.write(details)
        return 1
    return 0


if __name__=='__main__':raise SystemExit(main())
