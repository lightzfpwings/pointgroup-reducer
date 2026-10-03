"""Localized desktop wizard with offline mathematical typesetting."""
import json
import sys
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk, filedialog
from tkinter.scrolledtext import ScrolledText
from core import COMMON, fmt, get_table, number, parse_vector, payload
from i18n import LANGUAGES, tr, error_text, group_notes, UIError
from preferences import load_language, save_language
from motion import SlideStack
from exact_numbers import input_text, result_values
from math_display import MathImages, FORMULA, symbol_tex, decomposition_terms, result_latex, number_tex

STAGES = {name: (tr(name + '_title'), tr(name + '_instruction')) for name in ('select', 'input', 'result')}


def parse_fields(table, values, language='zh-Hans'):
    if len(values) != len(table.classes):
        raise UIError('need_count', language, count=len(table.classes))
    parsed = []
    for label, text in zip(table.classes, values):
        if not text.strip():
            raise UIError('missing_class', language, label=label)
        try:
            parsed.append(number(text))
        except ValueError as error:
            raise UIError('bad_class', language, label=label, value=text, reason=str(error)) from error
    return parsed


class App:
    def __init__(self, root, group='C2v', language=None):
        self.root = root
        self.language = language if language in LANGUAGES else load_language()
        self.localized_widgets = []
        self.help_windows = []
        self.table = self.result = None
        self.fields, self.entries = [], []
        self.stage = 'home'
        self.status_key, self.status_values, self.status_flags = None, {}, {}
        self.math = MathImages(root)
        width = min(1160, max(880, root.winfo_screenwidth() - 100))
        height = min(800, max(620, root.winfo_screenheight() - 120))
        root.geometry(f'{width}x{height}')
        root.minsize(880, 620)
        family = tkfont.nametofont('TkDefaultFont').actual('family')
        candidates = ['Microsoft YaHei UI', 'Microsoft JhengHei UI'] if sys.platform == 'win32' else ['PingFang SC', 'PingFang TC'] if sys.platform == 'darwin' else ['Noto Sans CJK SC', 'Noto Sans CJK TC']
        for preferred in candidates:
            if preferred in tkfont.families(root):
                family = preferred
                for name in ('TkDefaultFont', 'TkTextFont', 'TkMenuFont', 'TkHeadingFont', 'TkCaptionFont'):
                    tkfont.nametofont(name).configure(family=family)
                break
        self.family = family
        style = ttk.Style(root)
        # A consistent theme allows image headings on Windows and both Mac architectures.
        if 'clam' in style.theme_names():
            style.theme_use('clam')
        style.configure('TButton', padding=(10, 7))
        style.configure('Title.TLabel', font=(family, 18, 'bold'))
        style.configure('Error.TLabel', foreground='#ac2020')
        style.configure('Success.TLabel', foreground='#236b3d')
        style.configure('Hint.TLabel', foreground='#4d5661')
        style.configure('Treeview', rowheight=max(32, round(self.math.dpi * .27)))
        style.configure('Treeview.Heading', padding=(6, 6))

        language_bar = ttk.Frame(root, padding=(20, 8))
        language_bar.pack(fill='x')
        self.label(language_bar, 'language').pack(side='right', padx=8)
        self.motion_enabled = tk.BooleanVar(value=True)
        self.widget(ttk.Checkbutton, language_bar, 'smooth_motion',
                    variable=self.motion_enabled, command=self.toggle_motion).pack(side='left')
        self.language_value = tk.StringVar(value=LANGUAGES[self.language])
        self.language_combo = ttk.Combobox(language_bar, textvariable=self.language_value,
                                          values=list(LANGUAGES.values()), state='readonly', width=14)
        self.language_combo.pack(side='right')
        self.language_combo.bind('<<ComboboxSelected>>', lambda _: self.set_language(
            next(key for key, value in LANGUAGES.items() if value == self.language_value.get())))
        self.host = ttk.Frame(root)
        self.host.pack(fill='both', expand=True)
        self.page_motion = SlideStack(self.host)
        self.homepage = ttk.Frame(self.host, padding=36)
        self.label(self.homepage, 'app_title', style='Title.TLabel').pack(anchor='w', pady=(26, 16))
        self.label(self.homepage, 'home_description', wraplength=960).pack(anchor='w', pady=6)
        self.math.label(self.homepage, FORMULA, 19).pack(anchor='w', pady=18)
        self.label(self.homepage, 'home_steps').pack(anchor='w', pady=16)
        self.button(self.homepage, 'start', lambda: self.show_stage('select')).pack(anchor='w', pady=8)
        self.button(self.homepage, 'help', self.help).pack(anchor='w', pady=6)
        self.button(self.homepage, 'exit_program', root.destroy).pack(anchor='w', pady=6)
        self.label(self.homepage, 'keep_input', style='Hint.TLabel').pack(anchor='w', pady=16)

        self.workspace = ttk.Frame(self.host, padding=20)
        self.workspace.columnconfigure(0, weight=1)
        self.workspace.rowconfigure(4, weight=1)
        nav = ttk.Frame(self.workspace)
        nav.grid(row=0, column=0, sticky='ew', pady=(0, 12))
        self.button(nav, 'back', self.back).pack(side='left')
        self.button(nav, 'home', self.home).pack(side='left', padx=8)
        self.button(nav, 'exit', root.destroy).pack(side='right')
        self.button(nav, 'help', self.help).pack(side='right', padx=8)
        self.steptext, self.instruction = tk.StringVar(), tk.StringVar()
        ttk.Label(self.workspace, textvariable=self.steptext, style='Title.TLabel').grid(row=1, column=0, sticky='w')
        ttk.Label(self.workspace, textvariable=self.instruction, wraplength=1050).grid(row=2, column=0, sticky='w', pady=(8, 12))
        infoframe = ttk.Frame(self.workspace)
        infoframe.grid(row=3, column=0, sticky='w', pady=(0, 10))
        self.group_image = ttk.Label(infoframe)
        self.group_image.pack(side='left', padx=(0, 14))
        self.info = tk.StringVar()
        ttk.Label(infoframe, textvariable=self.info, style='Hint.TLabel').pack(side='left')
        self.content = ttk.Frame(self.workspace)
        self.content.grid(row=4, column=0, sticky='nsew')
        self.body_motion = SlideStack(self.content)
        self.selectpage = ttk.Frame(self.content)
        self.inputpage = ttk.Frame(self.content)
        self.resultpage = ttk.Frame(self.content)
        for page in (self.selectpage, self.inputpage):
            page.columnconfigure(0, weight=1)
            page.rowconfigure(1, weight=1)
        self.controls = ttk.Frame(self.selectpage)
        self.label(self.controls, 'group_name').pack(side='left')
        self.group = tk.StringVar(value=group)
        self.combo = ttk.Combobox(self.controls, textvariable=self.group, values=COMMON, width=18)
        self.combo.pack(side='left', padx=10)
        self.combo.bind('<<ComboboxSelected>>', lambda _: self.load())
        self.combo.bind('<Return>', lambda _: self.load())
        self.button(self.controls, 'view_table', self.load).pack(side='left')
        self.label(self.controls, 'group_examples', style='Hint.TLabel').pack(side='left', padx=16)

        self.tableframe, self.tree = self.make_table(self.selectpage)
        self.inputtableframe, self.inputtree = self.make_table(self.inputpage)
        self.table_views = [(self.tree, None), (self.inputtree, None)]
        self.controls.grid(row=0, column=0, sticky='ew', pady=(0, 12))
        self.tableframe.grid(row=1, column=0, sticky='nsew')
        self.inputtableframe.grid(row=1, column=0, sticky='nsew')

        self.inputframe = self.widget(ttk.LabelFrame, self.inputpage, 'input_box', padding=10)
        self.canvas = tk.Canvas(self.inputframe, height=88, highlightthickness=0)
        self.inputs = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inputs, anchor='nw')
        self._input_geometry = None
        self.inputs.bind('<Configure>', self.resize_inputs)
        sb = ttk.Scrollbar(self.inputframe, orient='horizontal', command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=sb.set)
        self.canvas.pack(fill='x')
        sb.pack(fill='x')
        self.label(self.inputframe, 'input_hint', style='Hint.TLabel').pack(anchor='w', pady=(8, 0))
        self.bulkframe = ttk.Frame(self.inputpage)
        self.label(self.bulkframe, 'paste_label').pack(side='left')
        self.bulk = ttk.Entry(self.bulkframe)
        self.bulk.pack(side='left', fill='x', expand=True, padx=10)
        self.bulk.bind('<Return>', lambda _: self.fill_bulk())
        self.apply_button = self.button(self.bulkframe, 'apply', self.fill_bulk)
        self.apply_button.pack(side='left')
        self.label(self.bulkframe, 'paste_hint', style='Hint.TLabel').pack(side='left', padx=10)
        self.inputframe.grid(row=2, column=0, sticky='ew', pady=(12, 10))
        self.bulkframe.grid(row=3, column=0, sticky='ew')
        self.output = ScrolledText(self.resultpage, height=12, wrap='word', font=(family, 11))
        self.output.configure(state='disabled')
        self.output.pack(fill='both', expand=True)
        self.actions = ttk.Frame(self.workspace)
        self.actions.grid(row=5, column=0, sticky='ew', pady=(14, 8))
        self.selectbar = ttk.Frame(self.actions)
        self.button(self.selectbar, 'next', self.next_input).pack(side='left')
        self.button(self.selectbar, 'export_table', self.export).pack(side='left', padx=10)
        self.inputbar = ttk.Frame(self.actions)
        self.button(self.inputbar, 'calculate', self.calculate).pack(side='left')
        self.button(self.inputbar, 'example', self.example).pack(side='left', padx=10)
        self.button(self.inputbar, 'clear', self.clear).pack(side='left')
        self.resultbar = ttk.Frame(self.actions)
        self.button(self.resultbar, 'edit', lambda: self.show_stage('input')).pack(side='left')
        self.button(self.resultbar, 'copy_text', lambda: self.copy_result(False)).pack(side='left', padx=6)
        self.button(self.resultbar, 'copy_latex', lambda: self.copy_result(True)).pack(side='left')
        self.button(self.resultbar, 'export_result', self.export).pack(side='left', padx=6)
        self.button(self.resultbar, 'change_group', lambda: self.show_stage('select')).pack(side='left')
        self.status = tk.StringVar()
        self.statuslabel = ttk.Label(self.workspace, textvariable=self.status, wraplength=1050)
        self.statuslabel.grid(row=6, column=0, sticky='w')
        root.title(self.t('app_title'))
        self.load()
        self.show_stage('home')
        self._shortcuts()

    def t(self, key, **values):
        if 'reason' in values:
            values['reason'] = error_text(values['reason'], getattr(self, 'language', 'zh-Hans'))
        return tr(key, getattr(self, 'language', 'zh-Hans'), **values)

    def widget(self, cls, parent, key, **kwargs):
        widget = cls(parent, text=self.t(key), **kwargs)
        self.localized_widgets.append((widget, key))
        return widget

    def label(self, parent, key, **kwargs):
        return self.widget(ttk.Label, parent, key, **kwargs)

    def button(self, parent, key, command):
        return self.widget(ttk.Button, parent, key, command=command)

    def set_language(self, language, persist=True):
        if language not in LANGUAGES:
            raise ValueError('Unsupported language')
        self.language = language
        self.language_value.set(LANGUAGES[language])
        self.root.title(self.t('app_title'))
        alive = []
        for widget, key in self.localized_widgets:
            if widget.winfo_exists():
                widget.configure(text=self.t(key))
                alive.append((widget, key))
        self.localized_widgets = alive
        self._menu()
        if self.stage != 'home':
            self.steptext.set(self.t(self.stage + '_title'))
            self.instruction.set(self.t(self.stage + '_instruction'))
        self.refresh_info()
        if self.table is not None:
            for tree, weight_row in self.table_views:
                tree.heading('#0', text=self.t('irrep'))
                tree.item(weight_row, text=self.t('class_size'))
        if self.result is not None:
            self.render_result()
        for window, text in list(self.help_windows):
            if window.winfo_exists():
                window.title(self.t('help'))
                self.render_help(text)
            else:
                self.help_windows.remove((window, text))
        if self.status_key:
            self.message(self.status_key, **self.status_values, **self.status_flags)
        elif self.stage == 'result' and self.result is not None:
            self._result_status()
        else:
            self.set_status()
        if persist and not save_language(language):
            self.message('language_not_saved')

    def _menu(self):
        menu = tk.Menu(self.root)
        navigation = tk.Menu(menu, tearoff=False)
        navigation.add_command(label=self.t('back'), command=self.back, accelerator='Esc')
        navigation.add_command(label=self.t('home'), command=self.home, accelerator='Command+Shift+H' if sys.platform == 'darwin' else 'Ctrl+Home')
        navigation.add_separator()
        navigation.add_command(label=self.t('exit'), command=self.root.destroy, accelerator='Command+Q' if sys.platform == 'darwin' else 'Ctrl+Q')
        menu.add_cascade(label=self.t('navigation'), menu=navigation)
        languages = tk.Menu(menu, tearoff=False)
        for code, name in LANGUAGES.items():
            languages.add_radiobutton(label=name, variable=self.language_value, value=name,
                                     command=lambda code=code: self.set_language(code))
        menu.add_cascade(label=self.t('language'), menu=languages)
        old = getattr(self, 'menu', None)
        self.root.config(menu=menu)
        self.menu = menu
        if old is not None:
            old.destroy()

    def _shortcuts(self):
        self.root.bind('<Escape>', lambda _: self.back())
        self.root.bind('<Control-Home>', lambda _: self.home())
        for key in ('<Control-q>', '<Control-Q>'):
            self.root.bind(key, lambda _: self.root.destroy())
        self.root.bind('<Key-q>', lambda _: self.root.destroy() if self.stage == 'home' else None)
        self.root.protocol('WM_DELETE_WINDOW', self.root.destroy)
        if sys.platform == 'darwin':
            self.root.bind('<Command-q>', lambda _: self.root.destroy())
            self.root.bind('<Command-Shift-h>', lambda _: self.home())
            self.root.bind('<Command-Shift-H>', lambda _: self.home())
            self.root.createcommand('tk::mac::Quit', self.root.destroy)
        self._menu()

    def set_status(self, text='', error=False, success=False):
        self.status_key = None
        self.status.set(text)
        self.statuslabel.configure(style='Error.TLabel' if error else 'Success.TLabel' if success else 'Hint.TLabel')

    def message(self, key, error=False, success=False, **values):
        self.set_status(self.t(key, **values), error=error, success=success)
        self.status_key, self.status_values = key, values
        self.status_flags = {'error': error, 'success': success}

    def handle_error(self, error):
        if isinstance(error, UIError):
            self.message(error.key, error=True, **error.values)
        else:
            self.message('core_error', error=True, reason=str(error))

    def show_stage(self, stage):
        previous = self.stage
        order = ('home', 'select', 'input', 'result')
        direction = 1 if order.index(stage) > order.index(previous) else -1
        self.stage = stage
        self.set_status()
        if stage == 'home':
            self.page_motion.show(self.homepage, direction)
            self.root.focus_set()
            return
        self.steptext.set(self.t(stage + '_title'))
        self.instruction.set(self.t(stage + '_instruction'))
        for widget in (self.selectbar, self.inputbar, self.resultbar):
            widget.pack_forget()
        page = {'select': self.selectpage, 'input': self.inputpage, 'result': self.resultpage}[stage]
        # Do not stack two animations on entering the workspace from Home.
        self.body_motion.show(page, direction, animate=previous != 'home')
        self.page_motion.show(self.workspace, direction)
        {'select': self.selectbar, 'input': self.inputbar, 'result': self.resultbar}[stage].pack(fill='x')
        if stage == 'result' and self.result is not None:
            self._result_status()

    def toggle_motion(self):
        for controller in (self.page_motion, self.body_motion):
            controller.set_enabled(self.motion_enabled.get())

    def make_table(self, parent):
        frame = ttk.Frame(parent)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        tree = ttk.Treeview(frame, show='tree headings', height=8)
        tree.column('#0', width=190, stretch=False, anchor='center')
        sx = ttk.Scrollbar(frame, orient='horizontal', command=tree.xview)
        sy = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        tree.configure(xscrollcommand=sx.set, yscrollcommand=sy.set)
        tree.grid(row=0, column=0, sticky='nsew')
        sx.grid(row=1, column=0, sticky='ew')
        sy.grid(row=0, column=1, sticky='ns')
        return frame, tree

    def resize_inputs(self, _event=None):
        geometry = (self.inputs.winfo_reqwidth(), self.inputs.winfo_reqheight())
        if geometry != self._input_geometry:
            self._input_geometry = geometry
            self.canvas.configure(scrollregion=(0, 0, *geometry), height=geometry[1])

    def back(self):
        self.show_stage({'home': 'home', 'select': 'home', 'input': 'select', 'result': 'input'}[self.stage])

    def home(self):
        self.show_stage('home')

    def current(self):
        if self.table is None:
            raise UIError('valid_group_first', self.language)
        if get_table(self.group.get()) is not self.table:
            raise UIError('group_changed', self.language)

    def next_input(self):
        if self.load():
            self.show_stage('input')
            if self.entries:
                self.entries[0].focus_set()

    def write(self, text):
        self.output.configure(state='normal')
        self.output.delete('1.0', 'end')
        self.output.insert('end', text)
        self.output.configure(state='disabled')

    def refresh_info(self):
        if self.table is not None:
            self.info.set(self.t('group_info', h=self.table.h, count=len(self.table.classes)))
            self.group_image.configure(image=self.math.image(symbol_tex(self.table.name), 16))

    def load(self):
        try:
            table = get_table(self.group.get())
        except ValueError as error:
            self.message('load_error', reason=str(error), error=True)
            return False
        if table is self.table:
            self.message('ready')
            return True
        self.table, self.result = table, None
        columns = [str(j) for j in range(len(table.classes))]
        headings = [self.math.image(symbol_tex(label)) for label in table.classes]
        row_images = [self.math.image(symbol_tex(label)) for label in table.irreps]
        values = [[fmt(z) for z in row] for row in table.symbolic_rows()]
        ttk.Style(self.root).configure('Treeview', rowheight=max(
            32, round(self.math.dpi * .27), max(image.height() for image in row_images) + 8))
        self.table_views = []
        for tree in (self.tree, self.inputtree):
            tree.delete(*tree.get_children())
            tree.configure(columns=columns)
            tree.heading('#0', text=self.t('irrep'))
            cell_font = tkfont.nametofont('TkDefaultFont')
            for j, (column, image) in enumerate(zip(columns, headings)):
                tree.heading(column, text='', image=image)
                tree.column(column, width=max(110, image.width() + 18, max(cell_font.measure(row[j]) for row in values) + 24), stretch=False, anchor='center')
            weight_row = tree.insert('', 'end', text=self.t('class_size'), values=table.sizes.tolist())
            self.table_views.append((tree, weight_row))
            for image, row in zip(row_images, values):
                tree.insert('', 'end', image=image, values=row)
        self.weight_row = self.table_views[0][1]
        for widget in self.inputs.winfo_children():
            widget.destroy()
        self.fields, self.entries = [], []
        for j, label in enumerate(table.classes):
            self.math.label(self.inputs, symbol_tex(label)).grid(row=0, column=j, padx=8, sticky='w')
            value = tk.StringVar()
            entry = ttk.Entry(self.inputs, textvariable=value, width=16)
            entry.grid(row=1, column=j, padx=8, pady=8)
            entry.bind('<Return>', lambda _: self.calculate())
            value.trace_add('write', self.invalidate)
            self.fields.append(value)
            self.entries.append(entry)
        self.bulk.delete(0, 'end')
        self.canvas.xview_moveto(0)
        self.refresh_info()
        self.write('')
        self.message('ready')
        for window, text in self.help_windows:
            if window.winfo_exists():
                self.render_help(text)
        return True

    def invalidate(self, *_):
        had_result = self.result is not None
        self.result = None
        self.write('')
        if had_result:
            self.message('input_changed')
        else:
            self.set_status()

    def clear(self):
        for value in self.fields:
            value.set('')
        self.bulk.delete(0, 'end')
        self.message('cleared')

    def fill_bulk(self):
        try:
            self.current()
            text = self.bulk.get().strip()
            if not text:
                self.message('paste_first', error=True)
                return False
            c = parse_vector(text)
            if len(c) != len(self.fields):
                self.message('paste_count', expected=len(self.fields), actual=len(c),
                             columns=', '.join(self.table.classes), error=True)
                self.bulk.focus_set()
                return False
            for value, z in zip(self.fields, c):
                value.set(input_text(z))
            self.bulk.delete(0, 'end')
            self.message('filled')
            return True
        except ValueError as error:
            self.handle_error(error)
            self.bulk.focus_set()
            return False

    def example(self):
        try:
            self.current()
            for value, z in zip(self.fields, self.table.orbital_exact(2)):
                value.set(input_text(z))
            self.bulk.delete(0, 'end')
            self.message('example_filled')
        except ValueError as error:
            self.handle_error(error)

    def _result_status(self):
        self.message('valid_result' if self.result['valid'] else 'invalid_result',
                     success=self.result['valid'], error=not self.result['valid'])

    def result_text(self):
        result = self.result
        lines = [self.table.name, '', self.t('input_characters')]
        lines.extend(f'  {name}: {fmt(z)}' for name, z in zip(self.table.classes, result_values(self.table,result,'c')))
        lines.extend(['', self.t('multiplicities')])
        lines.extend(f'  {name}: {fmt(z)}' for name, z in zip(self.table.irreps, result_values(self.table,result,'a')))
        lines.extend(['', self.table.decomposition(result) if result['valid'] else self.t('invalid_decomposition'),
                      '', self.t('dimension') + f' χ(E) = {fmt(result_values(self.table,result,"c")[0])}',
                      self.t('residual', value=f'{result["residual"]:.3g}')])
        return '\n'.join(lines)

    def mathline(self, widget, tex, size=13):
        widget.image_create('end', image=self.math.image(tex, size), padx=4, pady=4)
        widget.insert('end', '\n')

    def render_result(self):
        result = self.result
        self.output.configure(state='normal')
        self.output.delete('1.0', 'end')
        self.mathline(self.output, FORMULA, 16)
        if result['valid']:
            # Split long decompositions into readable rendered lines.
            line, length, first = [], 0, True
            for term in decomposition_terms(self.table, result):
                if line and length + len(term) > 80:
                    self.mathline(self.output, (r'\Gamma = ' if first else '+ ') + ' + '.join(line), 17)
                    line, length, first = [], 0, False
                line.append(term)
                length += len(term) + 3
            self.mathline(self.output, (r'\Gamma = ' if first else '+ ') + (' + '.join(line) or '0'), 17)
        else:
            self.output.insert('end', self.t('invalid_decomposition') + '\n')
        self.output.insert('end', '\n' + self.t('input_characters') + '\n')
        for label, z in zip(self.table.classes, result_values(self.table,result,'c')):
            self.mathline(self.output, symbol_tex(label) + ' = ' + number_tex(z))
        self.output.insert('end', '\n' + self.t('multiplicities') + '\n')
        for label, z in zip(self.table.irreps, result_values(self.table,result,'a')):
            self.mathline(self.output, 'a_{' + symbol_tex(label) + '} = ' + number_tex(z))
        self.output.insert('end', '\n' + self.t('dimension') + '\n')
        self.mathline(self.output, r'\chi_{\Gamma}(E)=' + number_tex(result_values(self.table,result,'c')[0]))
        self.output.insert('end', self.t('residual', value=f'{result["residual"]:.3g}'))
        self.output.configure(state='disabled')
        self.output.yview_moveto(0)

    def calculate(self):
        try:
            self.current()
            if self.bulk.get().strip() and not self.fill_bulk():
                return
            c = parse_fields(self.table, [value.get() for value in self.fields], getattr(self, 'language', 'zh-Hans'))
            self.result = self.table.reduce(c)
            self.render_result()
            self.show_stage('result')
        except ValueError as error:
            self.handle_error(error)

    def copy_result(self, latex=False):
        if self.result is None:
            self.message('calculate_first', error=True)
            return
        try:
            text = result_latex(self.table, self.result) if latex else self.result_text()
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.message('copied', success=True)
        except tk.TclError as error:
            self.message('copy_error', reason=str(error), error=True)

    def export(self):
        try:
            self.current()
            if self.stage == 'select':
                data, initialfile = payload(self.table), f'{self.table.name}_table.json'
            elif self.result is not None:
                data, initialfile = payload(self.table, self.result), f'{self.table.name}_reduction.json'
            else:
                self.message('calculate_first', error=True)
                return
            path = filedialog.asksaveasfilename(parent=self.root, title=self.t('export_table' if self.stage == 'select' else 'export_result'),
                defaultextension='.json', initialfile=initialfile, filetypes=[(self.t('json_file'), '*.json')])
            if path:
                with open(path, 'w', encoding='utf-8') as handle:
                    json.dump(data, handle, ensure_ascii=False, indent=2)
                self.message('saved', path=path, success=True)
        except (ValueError, OSError) as error:
            self.message('export_error', reason=error_text(error, self.language), error=True)

    def render_help(self, text):
        text.configure(state='normal')
        text.delete('1.0', 'end')
        for section in ('steps', 'input', 'nav', 'symbols', 'scope'):
            text.insert('end', self.t('guide_' + section + '_title') + '\n', 'heading')
            if section == 'symbols':
                self.mathline(text, FORMULA, 17)
                for sample in ('D6h', 'A1g', 'C6^2', "A''", 'E1+g'):
                    self.mathline(text, symbol_tex(sample))
            values = {'home': 'Command+Shift+H' if sys.platform == 'darwin' else 'Ctrl+Home',
                      'quit': 'Command+Q' if sys.platform == 'darwin' else 'Ctrl+Q'} if section == 'nav' else {}
            text.insert('end', self.t('guide_' + section, **values) + '\n\n')
        if self.table:
            text.insert('end', self.t('current_note') + '\n', 'heading')
            text.insert('end', group_notes(self.table, self.language))
        text.configure(state='disabled')

    def help(self):
        window = tk.Toplevel(self.root)
        window.title(self.t('help'))
        window.geometry('800x640')
        outer = ttk.Frame(window, padding=18)
        outer.pack(fill='both', expand=True)
        text = ScrolledText(outer, wrap='word', font=tkfont.nametofont('TkDefaultFont'))
        text.tag_configure('heading', font=(self.family, 12, 'bold'))
        text.pack(fill='both', expand=True)
        self.help_windows.append((window, text))
        self.render_help(text)
        self.button(outer, 'close_help', window.destroy).pack(anchor='e', pady=(12, 0))
        window.bind('<Escape>', lambda _: window.destroy())
        window.transient(self.root)


def launch(group='C2v', language=None):
    root = tk.Tk()
    App(root, group, language)
    root.mainloop()


if __name__ == '__main__':
    launch()
