"""Desktop wizard with concise, stage-specific Chinese instructions."""
import json
import sys
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk, filedialog
from tkinter.scrolledtext import ScrolledText
from core import COMMON, fmt, get_table, number, parse_vector, payload

STAGES = {
    'select': ('1 / 3 · 选择点群', '选择或输入点群名称，查看特征标表后点击“下一步”。'),
    'input': ('2 / 3 · 输入特征标 c', '按表中列顺序，每个共轭类填写一个特征标。填写后点击“计算”。'),
    'result': ('3 / 3 · 查看约化结果', 'a 表示各不可约表示出现的次数。可以返回修改输入，或导出结果。'),
}


def parse_fields(table, values):
    """Report the exact class with a missing or malformed character."""
    if len(values) != len(table.classes):
        raise ValueError(f'需要 {len(table.classes)} 个特征标。')
    parsed = []
    for label, text in zip(table.classes, values):
        if not text.strip():
            raise ValueError(f'请填写 {label} 列的特征标。')
        try:
            parsed.append(number(text))
        except ValueError as error:
            raise ValueError(f'{label} 列的输入无法解析：{text}。{error}') from error
    if len(parsed) != len(table.classes):
        raise ValueError(f'需要 {len(table.classes)} 个特征标。')
    return parsed


class App:
    def __init__(self, root, group='C2v'):
        self.root = root
        self.table = self.result = None
        self.fields, self.entries = [], []
        self.stage = 'home'
        root.title('Point Group Reducer · 点群特征标约化')
        width = min(1080, max(800, root.winfo_screenwidth() - 100))
        height = min(760, max(600, root.winfo_screenheight() - 120))
        root.geometry(f'{width}x{height}')
        root.minsize(800, 600)
        family = tkfont.nametofont('TkDefaultFont').actual('family')
        preferred = 'Microsoft YaHei UI' if sys.platform == 'win32' else 'PingFang SC' if sys.platform == 'darwin' else 'Noto Sans CJK SC'
        if preferred in tkfont.families(root):
            family = preferred
            for name in ('TkDefaultFont', 'TkTextFont', 'TkMenuFont', 'TkHeadingFont', 'TkCaptionFont'):
                tkfont.nametofont(name).configure(family=family)
        style = ttk.Style(root)
        if sys.platform != 'darwin' and 'clam' in style.theme_names():
            style.theme_use('clam')
        style.configure('TButton', padding=(12, 7))
        style.configure('Title.TLabel', font=(family, 18, 'bold'))
        style.configure('Step.TLabel', font=(family, 12, 'bold'))
        style.configure('Error.TLabel', foreground='#ac2020')
        style.configure('Success.TLabel', foreground='#236b3d')
        style.configure('Hint.TLabel', foreground='#4d5661')

        self.host = ttk.Frame(root)
        self.host.pack(fill='both', expand=True)
        self.homepage = ttk.Frame(self.host, padding=40)
        ttk.Label(self.homepage, text='点群特征标约化', style='Title.TLabel').pack(anchor='w', pady=(40, 16))
        ttk.Label(self.homepage, text='输入表示的特征标 c，得到约化系数 a 和不可约表示分解。').pack(anchor='w', pady=6)
        ttk.Label(self.homepage, text='1  选择点群      →      2  输入 c      →      3  查看结果', style='Step.TLabel').pack(anchor='w', pady=24)
        ttk.Button(self.homepage, text='开始计算', command=lambda: self.show_stage('select')).pack(anchor='w', pady=10)
        ttk.Button(self.homepage, text='使用说明', command=self.help).pack(anchor='w', pady=6)
        ttk.Button(self.homepage, text='退出程序', command=root.destroy).pack(anchor='w', pady=6)
        ttk.Label(self.homepage, text='返回操作会保留已填写的数据。', style='Hint.TLabel').pack(anchor='w', pady=20)

        self.workspace = ttk.Frame(self.host, padding=20)
        self.workspace.columnconfigure(0, weight=1)
        self.workspace.rowconfigure(4, weight=1)
        nav = ttk.Frame(self.workspace)
        nav.grid(row=0, column=0, sticky='ew', pady=(0, 18))
        ttk.Button(nav, text='上一步', command=self.back).pack(side='left')
        ttk.Button(nav, text='返回主页', command=self.home).pack(side='left', padx=8)
        ttk.Button(nav, text='退出', command=root.destroy).pack(side='right')
        ttk.Button(nav, text='使用说明', command=self.help).pack(side='right', padx=8)
        self.steptext, self.instruction = tk.StringVar(), tk.StringVar()
        ttk.Label(self.workspace, textvariable=self.steptext, style='Title.TLabel').grid(row=1, column=0, sticky='w')
        ttk.Label(self.workspace, textvariable=self.instruction, wraplength=980).grid(row=2, column=0, sticky='w', pady=(8, 12))
        self.info = tk.StringVar()
        ttk.Label(self.workspace, textvariable=self.info, style='Hint.TLabel', wraplength=980).grid(row=3, column=0, sticky='w', pady=(0, 10))

        self.content = ttk.Frame(self.workspace)
        self.content.grid(row=4, column=0, sticky='nsew')
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(1, weight=1)
        self.controls = ttk.Frame(self.content)
        ttk.Label(self.controls, text='点群名称').pack(side='left')
        self.group = tk.StringVar(value=group)
        self.combo = ttk.Combobox(self.controls, textvariable=self.group, values=COMMON, width=18)
        self.combo.pack(side='left', padx=10)
        self.combo.bind('<<ComboboxSelected>>', lambda _: self.load())
        self.combo.bind('<Return>', lambda _: self.load())
        ttk.Button(self.controls, text='查看特征标表', command=self.load).pack(side='left')
        ttk.Label(self.controls, text='例如 C2v、D4h、C17v', style='Hint.TLabel').pack(side='left', padx=16)

        self.tableframe = ttk.Frame(self.content)
        self.tableframe.columnconfigure(0, weight=1)
        self.tableframe.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(self.tableframe, show='headings', height=8)
        sx = ttk.Scrollbar(self.tableframe, orient='horizontal', command=self.tree.xview)
        sy = ttk.Scrollbar(self.tableframe, orient='vertical', command=self.tree.yview)
        self.tree.configure(xscrollcommand=sx.set, yscrollcommand=sy.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        sx.grid(row=1, column=0, sticky='ew')
        sy.grid(row=0, column=1, sticky='ns')

        self.inputframe = ttk.LabelFrame(self.content, text='输入特征标 c', padding=10)
        self.canvas = tk.Canvas(self.inputframe, height=76, highlightthickness=0)
        self.inputs = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inputs, anchor='nw')
        self.inputs.bind('<Configure>', lambda _: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        sb = ttk.Scrollbar(self.inputframe, orient='horizontal', command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=sb.set)
        self.canvas.pack(fill='x')
        sb.pack(fill='x')
        ttk.Label(self.inputframe, text='每格填一个数；不乘类内操作数。0 可直接输入。', style='Hint.TLabel').pack(anchor='w', pady=(8, 0))

        self.bulkframe = ttk.Frame(self.content)
        ttk.Label(self.bulkframe, text='整行粘贴（逗号分隔）').pack(side='left')
        self.bulk = ttk.Entry(self.bulkframe)
        self.bulk.pack(side='left', fill='x', expand=True, padx=10)
        self.bulk.bind('<Return>', lambda _: self.fill_bulk())
        self.apply_button = ttk.Button(self.bulkframe, text='填入各列', command=self.fill_bulk)
        self.apply_button.pack(side='left')
        ttk.Label(self.bulkframe, text='粘贴后请点“填入各列”', style='Hint.TLabel').pack(side='left', padx=10)

        self.output = ScrolledText(self.content, height=12, wrap='word', font=(family, 11))
        self.output.configure(state='disabled')
        self.actions = ttk.Frame(self.workspace)
        self.actions.grid(row=5, column=0, sticky='ew', pady=(14, 8))
        self.selectbar = ttk.Frame(self.actions)
        ttk.Button(self.selectbar, text='下一步：输入 c', command=self.next_input).pack(side='left')
        ttk.Button(self.selectbar, text='导出特征标表', command=self.export).pack(side='left', padx=10)
        self.inputbar = ttk.Frame(self.actions)
        ttk.Button(self.inputbar, text='计算', command=self.calculate).pack(side='left')
        ttk.Button(self.inputbar, text='填入五个 d 轨道示例', command=self.example).pack(side='left', padx=10)
        ttk.Button(self.inputbar, text='清空输入', command=self.clear).pack(side='left')
        self.resultbar = ttk.Frame(self.actions)
        ttk.Button(self.resultbar, text='修改输入 c', command=lambda: self.show_stage('input')).pack(side='left')
        ttk.Button(self.resultbar, text='导出结果（JSON）', command=self.export).pack(side='left', padx=10)
        ttk.Button(self.resultbar, text='更换点群', command=lambda: self.show_stage('select')).pack(side='left')
        self.status = tk.StringVar()
        self.statuslabel = ttk.Label(self.workspace, textvariable=self.status, wraplength=980)
        self.statuslabel.grid(row=6, column=0, sticky='w')
        self.load()
        self.show_stage('home')
        self._shortcuts()

    def _shortcuts(self):
        self.root.bind('<Escape>', lambda _: self.back())
        self.root.bind('<Control-Home>', lambda _: self.home())
        self.root.bind('<Control-q>', lambda _: self.root.destroy())
        self.root.bind('<Control-Q>', lambda _: self.root.destroy())
        self.root.bind('<Key-q>', lambda _: self.root.destroy() if self.stage == 'home' else None)
        self.root.protocol('WM_DELETE_WINDOW', self.root.destroy)
        if sys.platform == 'darwin':
            self.root.bind('<Command-q>', lambda _: self.root.destroy())
            self.root.bind('<Command-Shift-h>', lambda _: self.home())
            self.root.bind('<Command-Shift-H>', lambda _: self.home())
            self.root.createcommand('tk::mac::Quit', self.root.destroy)
        menu = tk.Menu(self.root)
        navigation = tk.Menu(menu, tearoff=False)
        navigation.add_command(label='上一步', command=self.back, accelerator='Esc')
        navigation.add_command(label='返回主页', command=self.home, accelerator='Command+Shift+H' if sys.platform == 'darwin' else 'Ctrl+Home')
        navigation.add_separator()
        navigation.add_command(label='退出', command=self.root.destroy, accelerator='Command+Q' if sys.platform == 'darwin' else 'Ctrl+Q')
        menu.add_cascade(label='导航', menu=navigation)
        self.root.config(menu=menu)

    def set_status(self, text='', error=False, success=False):
        self.status.set(text)
        self.statuslabel.configure(style='Error.TLabel' if error else 'Success.TLabel' if success else 'Hint.TLabel')

    def show_stage(self, stage):
        self.stage = stage
        self.homepage.pack_forget()
        self.workspace.pack_forget()
        self.set_status()
        if stage == 'home':
            self.homepage.pack(fill='both', expand=True)
            self.root.focus_set()
            return
        self.workspace.pack(fill='both', expand=True)
        title, instruction = STAGES[stage]
        self.steptext.set(title)
        self.instruction.set(instruction)
        for widget in (self.controls, self.tableframe, self.inputframe, self.bulkframe, self.output):
            widget.grid_remove()
        for widget in (self.selectbar, self.inputbar, self.resultbar):
            widget.pack_forget()
        if stage == 'select':
            self.controls.grid(row=0, column=0, sticky='ew', pady=(0, 12))
            self.tableframe.grid(row=1, column=0, sticky='nsew')
            self.selectbar.pack(fill='x')
        elif stage == 'input':
            self.tableframe.grid(row=1, column=0, sticky='nsew')
            self.inputframe.grid(row=2, column=0, sticky='ew', pady=(12, 10))
            self.bulkframe.grid(row=3, column=0, sticky='ew')
            self.inputbar.pack(fill='x')
        else:
            self.output.grid(row=0, column=0, rowspan=4, sticky='nsew')
            self.resultbar.pack(fill='x')
            if self.result is not None:
                self._result_status()

    def back(self):
        self.show_stage({'home': 'home', 'select': 'home', 'input': 'select', 'result': 'input'}[self.stage])

    def home(self):
        self.show_stage('home')

    def current(self):
        if self.table is None:
            raise ValueError('请先选择有效点群。')
        if get_table(self.group.get()) is not self.table:
            raise ValueError('点群名称已修改。请返回第一步并查看对应特征标表。')

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

    def load(self):
        try:
            table = get_table(self.group.get())
        except ValueError as error:
            self.set_status(f'无法载入点群：{error}', error=True)
            return False
        if table is self.table:
            self.set_status('特征标表已就绪。')
            return True
        self.table, self.result = table, None
        columns = ['irrep'] + [str(j) for j in range(len(table.classes))]
        self.tree.delete(*self.tree.get_children())
        self.tree.configure(columns=columns)
        for column, label in zip(columns, ['不可约表示'] + table.classes):
            self.tree.heading(column, text=label)
            self.tree.column(column, width=175 if column == 'irrep' else max(100, 10 * len(label)), stretch=False, anchor='center')
        self.tree.insert('', 'end', values=['类内操作数 n_j'] + table.sizes.tolist())
        for label, row in zip(table.irreps, table.X):
            self.tree.insert('', 'end', values=[label] + [fmt(z) for z in row])
        for widget in self.inputs.winfo_children():
            widget.destroy()
        self.fields, self.entries = [], []
        for j, label in enumerate(table.classes):
            ttk.Label(self.inputs, text=label).grid(row=0, column=j, padx=8, sticky='w')
            value = tk.StringVar()
            entry = ttk.Entry(self.inputs, textvariable=value, width=16)
            entry.grid(row=1, column=j, padx=8, pady=8)
            entry.bind('<Return>', lambda _: self.calculate())
            value.trace_add('write', self.invalidate)
            self.fields.append(value)
            self.entries.append(entry)
        self.bulk.delete(0, 'end')
        self.canvas.xview_moveto(0)
        self.info.set(f'当前点群：{table.name}    |    群阶 h = {table.h}    |    {len(table.classes)} 个共轭类')
        self.write('')
        self.set_status('特征标表已就绪。')
        return True

    def invalidate(self, *_):
        had_result = self.result is not None
        self.result = None
        self.write('')
        if had_result:
            self.set_status('输入已修改，请重新计算。')
        else:
            self.set_status()

    def clear(self):
        for value in self.fields:
            value.set('')
        self.bulk.delete(0, 'end')
        self.set_status('输入已清空。')

    def fill_bulk(self):
        try:
            self.current()
            text = self.bulk.get().strip()
            if not text:
                raise ValueError('请先粘贴特征标，用逗号分隔。')
            c = parse_vector(text)
            if len(c) != len(self.fields):
                raise ValueError(f'需要 {len(self.fields)} 个值，当前粘贴了 {len(c)} 个。列顺序：{", ".join(self.table.classes)}。')
            for value, z in zip(self.fields, c):
                value.set(fmt(z, 15))
            self.bulk.delete(0, 'end')
            self.set_status('已填入各列，请点击“计算”。')
            return True
        except ValueError as error:
            self.set_status(str(error), error=True)
            self.bulk.focus_set()
            return False

    def example(self):
        try:
            self.current()
            for value, z in zip(self.fields, self.table.orbital(2)):
                value.set(fmt(z, 15))
            self.bulk.delete(0, 'end')
            self.set_status('已填入五个 d 轨道的特征标。点击“计算”查看分解。')
        except ValueError as error:
            self.set_status(str(error), error=True)

    def _result_status(self):
        if self.result['valid']:
            self.set_status('约化成功：所有重数均为非负整数。', success=True)
        else:
            self.set_status('此 c 不能构成合法表示：重数必须为非负整数。请检查输入和列顺序。', error=True)

    def calculate(self):
        try:
            self.current()
            # Never silently ignore values left in the bulk paste field.
            if self.bulk.get().strip() and not self.fill_bulk():
                return
            c = parse_fields(self.table, [value.get() for value in self.fields])
            result = self.table.reduce(c)
            self.result = result
            lines = [self.table.name + ' · 约化结果', '', '输入特征标 c（按类顺序）：']
            lines.extend(f'  {name}：{fmt(z)}' for name, z in zip(self.table.classes, result['c']))
            lines.extend(['', '约化系数 a（各不可约表示出现的次数）：'])
            lines.extend(f'  {name}：{fmt(z)}' for name, z in zip(self.table.irreps, result['a']))
            if result['valid']:
                lines.extend(['', self.table.decomposition(result)])
            else:
                lines.extend(['', '未得到合法表示分解；以上为数学展开系数。'])
            lines.extend(['', f'表示维数 χ(E) = {fmt(result["dimension"])}', f'特征标重建误差 = {result["residual"]:.3g}'])
            self.write('\n'.join(lines))
            self.show_stage('result')
        except ValueError as error:
            self.set_status(str(error), error=True)

    def export(self):
        try:
            self.current()
            if self.stage == 'select':
                data, initialfile = payload(self.table), f'{self.table.name}_table.json'
            elif self.result is not None:
                data, initialfile = payload(self.table, self.result), f'{self.table.name}_reduction.json'
            else:
                raise ValueError('请先计算，再导出结果。')
            path = filedialog.asksaveasfilename(parent=self.root, defaultextension='.json', initialfile=initialfile, filetypes=[('JSON 文件', '*.json')])
            if path:
                with open(path, 'w', encoding='utf-8') as handle:
                    json.dump(data, handle, ensure_ascii=False, indent=2)
                self.set_status(f'已保存：{path}', success=True)
        except (ValueError, OSError) as error:
            self.set_status(f'导出失败：{error}', error=True)

    def help(self):
        window = tk.Toplevel(self.root)
        window.title('使用说明')
        window.geometry('760x580')
        outer = ttk.Frame(window, padding=18)
        outer.pack(fill='both', expand=True)
        text = ScrolledText(outer, wrap='word', font=tkfont.nametofont('TkDefaultFont'))
        text.pack(fill='both', expand=True)
        shortcuts = 'Command+Shift+H 返回主页；Command+Q 退出。' if sys.platform == 'darwin' else 'Ctrl+Home 返回主页；Ctrl+Q 退出。'
        details = [
            '操作步骤',
            '1. 选择点群，查看表的列顺序。\n2. 每类输入一个特征标 c，不乘类内操作数。\n3. 点击计算，读取系数 a 和表示分解。',
            '输入规则',
            '0 直接作为数值输入。支持 1/2、sqrt(5)、1+2i、exp(2*pi*i/3)。\n整行粘贴用逗号分隔；“填入各列”仅填入数据，“计算”也会应用尚未填入的粘贴内容。\n“填入五个 d 轨道示例”仅填入数据，不会自动跳到结果页。',
            '返回与退出',
            '窗口按钮随时可用；Esc 返回上一步；' + shortcuts + '\n返回和主页会保留输入。切换点群会清空旧输入。主页按 q 或关闭窗口均可退出。\n命令行导航：0 返回、home 主页、q 退出；单独输入数值零使用 =0。',
            '符号和公式',
            'c：特征标列向量；a：不可约表示的重数列向量；h：群阶。\nX：各不可约表示的特征标作为行；W：类内操作数的对角矩阵。\na = (1/h) X* W c，其中 X* 仅逐元素取复共轭。\n在合法表示中，a 必须为非负整数。c(E) 等于表示维数。',
            '范围与表的约定',
            '支持所有有限三维普通点群系列和多面体群，当前 n ≤ 2000。\n无限点群 C∞v、D∞h，以及双群、磁群、空间群不在此模式内。\nE+ / E− 为一维复共轭表示，不能分别当作二维 E。标签和列顺序可能不同于教材，请以程序显示为准。',
        ]
        if self.table and self.table.note:
            details.extend(['当前点群补充说明', self.table.note])
        text.insert('1.0', '\n\n'.join(details))
        text.configure(state='disabled')
        ttk.Button(outer, text='关闭说明', command=window.destroy).pack(anchor='e', pady=(12, 0))
        window.bind('<Escape>', lambda _: window.destroy())
        window.transient(self.root)


def launch(group='C2v'):
    try:
        root = tk.Tk()
    except tk.TclError as error:
        raise ValueError('无法打开桌面窗口。请在本机桌面运行，服务器可使用命令行版本。') from error
    App(root, group)
    root.mainloop()


if __name__ == '__main__':
    launch()
