"""Reviewed English, Simplified Chinese and Traditional Chinese UI messages."""
LANGUAGES = {'en': 'English', 'zh-Hans': '简体中文', 'zh-Hant': '繁體中文'}
# Every key has all three translations. Canonical identifiers and JSON stay stable.
MESSAGES = {
'app_title': ('Point Group Reducer', '点群特征标约化', '點群特徵標約化'),
'smooth_motion': ('Smooth transitions', '平滑过渡', '平滑過渡'),
'language': ('Language', '语言', '語言'),
'home_description': ('Enter characters c to obtain multiplicities a and the irreducible decomposition.', '输入表示的特征标 c，得到重数 a 和不可约表示分解。', '輸入表示的特徵標 c，得到重數 a 和不可約表示分解。'),
'home_steps': ('1  Select group  →  2  Enter c  →  3  View result', '1  选择点群  →  2  输入 c  →  3  查看结果', '1  選擇點群  →  2  輸入 c  →  3  查看結果'),
'start': ('Start calculation', '开始计算', '開始計算'),
'help': ('User guide', '使用说明', '使用說明'),
'exit_program': ('Exit application', '退出程序', '結束程式'),
'exit': ('Exit', '退出', '結束'),
'back': ('Back', '上一步', '上一步'),
'home': ('Home', '返回主页', '返回首頁'),
'keep_input': ('Back and Home keep your entered values.', '返回操作会保留已填写的数据。', '返回操作會保留已填寫的資料。'),
'select_title': ('1 / 3 · Select point group', '1 / 3 · 选择点群', '1 / 3 · 選擇點群'),
'select_instruction': ('Select or type a group name, review the table, then click Next.', '选择或输入点群名称，查看特征标表后点击“下一步”。', '選擇或輸入點群名稱，查看特徵標表後按「下一步」。'),
'input_title': ('2 / 3 · Enter characters c', '2 / 3 · 输入特征标 c', '2 / 3 · 輸入特徵標 c'),
'input_instruction': ('Enter one character per conjugacy class in column order, then click Calculate.', '按表中列顺序，每个共轭类填写一个特征标。填写后点击“计算”。', '按表中欄位順序，每個共軛類填寫一個特徵標。填寫後按「計算」。'),
'result_title': ('3 / 3 · View reduction', '3 / 3 · 查看约化结果', '3 / 3 · 查看約化結果'),
'result_instruction': ('a gives each irrep multiplicity. Go back to edit c, or copy/export the result.', 'a 表示各不可约表示出现的次数。可以返回修改输入，或复制／导出结果。', 'a 表示各不可約表示出現的次數。可返回修改輸入，或複製／匯出結果。'),
'group_name': ('Point group', '点群名称', '點群名稱'),
'view_table': ('View character table', '查看特征标表', '查看特徵標表'),
'group_examples': ('Examples: C2v, D4h, C17v', '例如 C2v、D4h、C17v', '例如 C2v、D4h、C17v'),
'input_box': ('Characters c', '输入特征标 c', '輸入特徵標 c'),
'input_hint': ('One value per box; do not multiply by class size. Enter 0 directly.', '每格填一个数；不乘类内操作数。0 可直接输入。', '每格填一個數；不乘類內操作數。0 可直接輸入。'),
'paste_label': ('Paste vector (commas)', '整行粘贴（逗号分隔）', '整行貼上（逗號分隔）'),
'apply': ('Fill columns', '填入各列', '填入各欄'),
'paste_hint': ('Click Fill columns after pasting', '粘贴后请点“填入各列”', '貼上後請按「填入各欄」'),
'next': ('Next: enter c', '下一步：输入 c', '下一步：輸入 c'),
'export_table': ('Export table', '导出特征标表', '匯出特徵標表'),
'calculate': ('Calculate', '计算', '計算'),
'example': ('Fill five d-orbital example', '填入五个 d 轨道示例', '填入五個 d 軌域範例'),
'clear': ('Clear input', '清空输入', '清空輸入'),
'edit': ('Edit c', '修改输入 c', '修改輸入 c'),
'export_result': ('Export JSON', '导出结果（JSON）', '匯出結果（JSON）'),
'change_group': ('Change group', '更换点群', '更換點群'),
'copy_text': ('Copy text', '复制文本', '複製文字'),
'copy_latex': ('Copy LaTeX', '复制 LaTeX', '複製 LaTeX'),
'navigation': ('Navigation', '导航', '導覽'),
'irrep': ('Irrep', '不可约表示', '不可約表示'),
'class_size': ('Class size', '类内操作数', '類內操作數'),
'group_info': ('Order h = {h}  |  {count} conjugacy classes', '群阶 h = {h}  |  {count} 个共轭类', '群階 h = {h}  |  {count} 個共軛類'),
'ready': ('Character table ready.', '特征标表已就绪。', '特徵標表已就緒。'),
'need_count': ('Expected {count} characters.', '需要 {count} 个特征标。', '需要 {count} 個特徵標。'),
'missing_class': ('Enter the character for {label}.', '请填写 {label} 列的特征标。', '請填寫 {label} 欄的特徵標。'),
'bad_class': ('Cannot parse {label}: {value}. {reason}', '{label} 列的输入无法解析：{value}。{reason}', '{label} 欄的輸入無法解析：{value}。{reason}'),
'valid_group_first': ('Select a valid point group first.', '请先选择有效点群。', '請先選擇有效點群。'),
'group_changed': ('Group name changed. Return to step 1 and load its table.', '点群名称已修改。请返回第一步并查看对应特征标表。', '點群名稱已修改。請返回第一步並查看對應特徵標表。'),
'load_error': ('Cannot load group: {reason}', '无法载入点群：{reason}', '無法載入點群：{reason}'),
'input_changed': ('Input changed; calculate again.', '输入已修改，请重新计算。', '輸入已修改，請重新計算。'),
'cleared': ('Input cleared.', '输入已清空。', '輸入已清空。'),
'paste_first': ('Paste characters separated by commas first.', '请先粘贴特征标，用逗号分隔。', '請先貼上特徵標，以逗號分隔。'),
'paste_count': ('Expected {expected} values; received {actual}. Column order: {columns}.', '需要 {expected} 个值，当前粘贴了 {actual} 个。列顺序：{columns}。', '需要 {expected} 個值，目前貼上了 {actual} 個。欄位順序：{columns}。'),
'filled': ('Columns filled; click Calculate.', '已填入各列，请点击“计算”。', '已填入各欄，請按「計算」。'),
'example_filled': ('Five d-orbital characters filled. Click Calculate to see the decomposition.', '已填入五个 d 轨道的特征标。点击“计算”查看分解。', '已填入五個 d 軌域的特徵標。按「計算」查看分解。'),
'valid_result': ('Reduction succeeded: all multiplicities are nonnegative integers.', '约化成功：所有重数均为非负整数。', '約化成功：所有重數均為非負整數。'),
'invalid_result': ('c is not a valid representation character: multiplicities must be nonnegative integers. Check values and column order.', '此 c 不能构成合法表示：重数必须为非负整数。请检查输入和列顺序。', '此 c 無法構成合法表示：重數必須為非負整數。請檢查輸入與欄位順序。'),
'input_characters': ('Input characters c (class order):', '输入特征标 c（按类顺序）：', '輸入特徵標 c（按類順序）：'),
'multiplicities': ('Coefficients a (irrep multiplicities):', '约化系数 a（各不可约表示出现的次数）：', '約化係數 a（各不可約表示出現的次數）：'),
'invalid_decomposition': ('No valid representation decomposition; these are mathematical expansion coefficients.', '未得到合法表示分解；以上为数学展开系数。', '未得到合法表示分解；以上為數學展開係數。'),
'dimension': ('Representation dimension', '表示维数', '表示維度'),
'residual': ('Character reconstruction error = {value}', '特征标重建误差 = {value}', '特徵標重建誤差 = {value}'),
'calculate_first': ('Calculate a result first.', '请先计算，再导出结果。', '請先計算，再匯出結果。'),
'json_file': ('JSON file', 'JSON 文件', 'JSON 檔案'),
'saved': ('Saved: {path}', '已保存：{path}', '已儲存：{path}'),
'export_error': ('Export failed: {reason}', '导出失败：{reason}', '匯出失敗：{reason}'),
'copied': ('Copied to clipboard.', '已复制到剪贴板。', '已複製至剪貼簿。'),
'copy_error': ('Clipboard unavailable: {reason}', '无法访问剪贴板：{reason}', '無法存取剪貼簿：{reason}'),
'close_help': ('Close guide', '关闭说明', '關閉說明'),
'guide_steps_title': ('Workflow', '操作步骤', '操作步驟'),
'guide_steps': ('1. Select a group and review the column order.\n2. Enter one character c per class without multiplying by class size.\n3. Calculate to read multiplicities a and the decomposition.', '1. 选择点群，查看表的列顺序。\n2. 每类输入一个特征标 c，不乘类内操作数。\n3. 点击计算，读取系数 a 和表示分解。', '1. 選擇點群，查看表的欄位順序。\n2. 每類輸入一個特徵標 c，不乘類內操作數。\n3. 按「計算」，讀取係數 a 與表示分解。'),
'guide_input_title': ('Input rules', '输入规则', '輸入規則'),
'guide_input': ('Enter 0 directly. Expressions include 1/2, sqrt(5), 1+2i and exp(2*pi*i/3).\nPaste vectors separated by commas. Calculate also applies any unapplied pasted vector.\nThe d-orbital example only fills values; click Calculate afterwards.', '0 直接作为数值输入。支持 1/2、sqrt(5)、1+2i、exp(2*pi*i/3)。\n整行粘贴用逗号分隔；计算也会应用尚未填入的粘贴内容。\nd 轨道示例仅填入数据，请再点击“计算”。', '0 直接作為數值輸入。支援 1/2、sqrt(5)、1+2i、exp(2*pi*i/3)。\n整行貼上以逗號分隔；計算也會套用尚未填入的貼上內容。\nd 軌域範例僅填入資料，請再按「計算」。'),
'guide_nav_title': ('Navigation and language', '返回、退出与语言', '返回、結束與語言'),
'guide_nav': ('Esc: Back; {home}: Home; {quit}: Exit.\nBack and Home preserve input. Changing groups clears the previous input.\nSwitch English / Simplified Chinese / Traditional Chinese at the top. The selection is remembered.\nCLI navigation: 0 = Back, home = Home, q = Exit; =0 enters a single numeric zero.', 'Esc 返回上一步；{home} 返回主页；{quit} 退出。\n返回和主页会保留输入；切换点群会清空旧输入。\n顶部可切换英文／简体中文／繁体中文，下次启动会记住选择。\n命令行导航：0 返回、home 主页、q 退出；单独输入数值零使用 =0。', 'Esc 返回上一步；{home} 返回首頁；{quit} 結束。\n返回和首頁會保留輸入；切換點群會清空舊輸入。\n頂部可切換英文／簡體中文／繁體中文，下次啟動會記住選擇。\n命令列導覽：0 返回、home 首頁、q 結束；單獨輸入數值零使用 =0。'),
'guide_symbols_title': ('Symbols and formula', '符号和公式', '符號與公式'),
'guide_symbols': ('c: character column vector; a: multiplicity column vector; h: group order.\nX: irrep characters as rows; W: diagonal matrix of class sizes.\nX* means elementwise complex conjugation, not conjugate transpose.\nValid multiplicities are nonnegative integers; c(E) is the representation dimension.\nMathText renders TeX notation offline. Copy LaTeX produces editable formulas for papers.', 'c：特征标列向量；a：重数列向量；h：群阶。\nX：各不可约表示的特征标作为行；W：类内操作数的对角矩阵。\nX* 仅逐元素取复共轭，不是共轭转置。\n合法重数必须为非负整数；c(E) 等于表示维数。\nMathText 离线渲染 TeX 数学符号；“复制 LaTeX”生成可用于论文的公式源码。', 'c：特徵標行向量（直式）；a：重數行向量（直式）；h：群階。\nX：各不可約表示的特徵標橫向排列；W：類內操作數的對角矩陣。\nX* 僅逐元素取複共軛，不是共軛轉置。\n合法重數必須為非負整數；c(E) 等於表示維度。\nMathText 離線渲染 TeX 數學符號；「複製 LaTeX」產生可用於論文的公式原始碼。'),
'guide_scope_title': ('Scope and conventions', '范围与表的约定', '範圍與表的約定'),
'guide_scope': ('Finite ordinary 3D point groups and polyhedral groups, with n ≤ 2000.\nInfinite groups C∞v and D∞h, double groups, magnetic groups and space groups are excluded.\nE+ / E− are one-dimensional complex conjugate irreps, not separate two-dimensional E irreps.\nLabels and column order may differ from textbooks; use the displayed table.', '支持有限三维普通点群系列和多面体群，当前 n ≤ 2000。\n无限点群 C∞v、D∞h，以及双群、磁群、空间群不在此模式内。\nE+ / E− 为一维复共轭表示，不能分别当作二维 E。\n标签和列顺序可能不同于教材，请以程序显示为准。', '支援有限三維普通點群系列與多面體群，目前 n ≤ 2000。\n無限點群 C∞v、D∞h，以及雙群、磁群、空間群不在此模式內。\nE+ / E− 為一維複共軛表示，不可分別當作二維 E。\n標籤與欄位順序可能不同於教材，請以程式顯示為準。'),
'current_note': ('Current group conventions', '当前点群补充说明', '目前點群補充說明'),
'cyclic_convention': ('Generator r = {generator}. Rk(r^p) = exp(2πikp/{order}); each Rk is a one-dimensional complex irrep.', '生成元 r = {generator}；Rk(r^p) = exp(2πikp/{order})，每个 Rk 为一维复不可约表示。', '生成元 r = {generator}；Rk(r^p) = exp(2πikp/{order})，每個 Rk 為一維複不可約表示。'),
'axis_convention': ('The principal axis is z. Rotation/reflection generator labels appear in the class headings.', '主轴为 z；旋转／反射生成元标签见共轭类表头。', '主軸為 z；旋轉／反射生成元標籤見共軛類表頭。'),
'generator_note': ('Generator labels and class representatives are kept exactly as displayed; class sizes are in a separate row. Conjugate E+ / E− labels denote one-dimensional irreps.', '生成元标签和共轭类代表操作以表中显示为准，类内操作数单列显示。共轭的 E+ / E− 标签表示一维不可约表示。', '生成元標籤與共軛類代表操作以表中顯示為準，類內操作數另列顯示。共軛的 E+ / E− 標籤表示一維不可約表示。'),
'product_note': ('For groups with g/u or prime suffixes, the second half of the columns is the central inversion/reflection times the first half. The suffix records its parity.', '带 g/u 或撇号后缀的群，后半列为中心反演／反射乘以前半列，后缀表示其宇称。', '帶 g/u 或撇號後綴的群，後半欄為中心反演／反射乘以前半欄，後綴表示其宇稱。'),
'polyhedral_note': ('Internal polyhedral representative matrices encode only rotation angle/parity for central atomic shell examples.', '多面体群的内部代表矩阵仅编码转角／宇称，供中心原子轨道示例使用。', '多面體群的內部代表矩陣僅編碼轉角／宇稱，供中心原子軌域範例使用。'),
'language_not_saved': ('Language changed for this session; preference could not be saved.', '本次语言已切换，但无法保存语言偏好。', '本次語言已切換，但無法儲存語言偏好。'),
'core_error': ('{reason}', '{reason}', '{reason}'),
'error_generic': ('Invalid input. Check the group name, column order and finite numeric expressions.', '输入无效，请检查点群名称、列顺序和有限数值表达式。', '輸入無效，請檢查點群名稱、欄位順序與有限數值運算式。'),
}

MESSAGES.update({
'representation_invalid': ('Not a valid representation character within tolerance (multiplicities must be nonnegative integers).', '输入不是容差内的合法表示特征标（重数须为非负整数）。', '輸入不是容差內的合法表示特徵標（重數須為非負整數）。'),
'cli_description': ('Point group character reduction: a = X.conj() @ W @ c / h', '点群特征标约化：a = X.conj() @ W @ c / h', '點群特徵標約化：a = X.conj() @ W @ c / h'),
'arg_group': ('e.g. C2v, D4h, Ih or C17v', '例如 C2v、D4h、Ih 或 C17v', '例如 C2v、D4h、Ih 或 C17v'),
'arg_c': ('Characters in column order, comma-separated', '按列输入，用逗号分隔，例如 --c "5,1,1,1"', '依欄位順序輸入，以逗號分隔，例如 --c "5,1,1,1"'),
'arg_gui': ('Open desktop interface', '打开图形界面', '開啟圖形介面'),
'arg_list': ('Show supported point groups', '显示点群覆盖范围', '顯示點群支援範圍'),
'arg_table': ('Show character table only', '仅查看特征标表', '僅查看特徵標表'),
'arg_shell': ('Central shell example: s=0, p=1, d=2, f=3', '中心原子轨道示例：s=0、p=1、d=2、f=3', '中心原子軌域範例：s=0、p=1、d=2、f=3'),
'arg_json': ('Export complete table and result to JSON', '导出完整表与结果 JSON', '匯出完整表與結果 JSON'),
'arg_csv': ('Export character table to CSV', '导出特征标表 CSV', '匯出特徵標表 CSV'),
'arg_tol': ('Absolute tolerance, default 1e-7', '绝对容差，默认 1e-7', '絕對容差，預設 1e-7'),
'arg_missing_group': ('Specify a point group for noninteractive mode, e.g. C2v --table.', '非交互模式请指定点群，例如 C2v --table；交互菜单请直接运行程序。', '非互動模式請指定點群，例如 C2v --table；互動選單請直接執行程式。'),
'arg_conflict': ('Choose only one of --c and --shell.', '--c 与 --shell 只能选择一个。', '--c 與 --shell 只能選擇一個。'),
'cli_home': ('\n=== Point Group Reducer · Home ===\n1 Start    2 Scope    q Exit    lang Language\nOr enter a group, e.g. C2v.', '\n=== 点群约化 · 主菜单 ===\n1 开始计算    2 支持范围    q 退出    lang 语言\n也可直接输入点群名，例如 C2v。', '\n=== 點群約化 · 主選單 ===\n1 開始計算    2 支援範圍    q 結束    lang 語言\n也可直接輸入點群名，例如 C2v。'),
'cli_choice': ('Choice: ', '选择：', '選擇：'),
'cli_nav': ('\n0 Back | home Home | q Exit | lang Language; use =0 for a single numeric zero.', '\n导航：0 上一步 | home 主菜单 | q 退出 | lang 语言；数值零请写 =0（逗号向量中的 0 可直接写）。', '\n導覽：0 上一步 | home 主選單 | q 結束 | lang 語言；數值零請寫 =0（逗號向量中的 0 可直接寫）。'),
'cli_group': ('Point group: ', '输入点群：', '輸入點群：'),
'cli_vector': ('c (comma-separated; Enter for individual values; d for d orbitals): ', '输入 c（逗号分隔；Enter 逐项输入；d 填入五个 d 轨道示例）：', '輸入 c（逗號分隔；Enter 逐項輸入；d 填入五個 d 軌域範例）：'),
'cli_result': ('1 Edit c | 2 Change group | s Export JSON | 0 Back | home Home | q Exit: ', '1 重新输入 c | 2 更换点群 | s 导出 JSON | 0 返回输入 | home 主菜单 | q 退出：', '1 重新輸入 c | 2 更換點群 | s 匯出 JSON | 0 返回輸入 | home 主選單 | q 結束：'),
'cli_path': ('JSON path (0 returns): ', '导出 JSON 路径（0 返回结果）：', '匯出 JSON 路徑（0 返回結果）：'),
'cli_choose': ('Choose 1, 2, s, 0, home or q.', '请选择 1、2、s、0、home 或 q。', '請選擇 1、2、s、0、home 或 q。'),
'cli_empty_path': ('Path cannot be empty.', '路径不能为空。', '路徑不可為空。'),
'cli_existing': ('File exists; choose a different filename.', '该文件已存在，请换一个文件名，避免覆盖。', '該檔案已存在，請換一個檔名，以免覆寫。'),
'cli_error': ('Error: {reason}; retry or use a navigation command.', '错误：{reason}；可以重试或使用导航命令。', '錯誤：{reason}；可重試或使用導覽指令。'),
'cli_exited': ('Exited.', '已退出。', '已結束。'),
'cli_scope': ('Supported: Cn/Cnv/Cnh, Dn/Dnh/Dnd, S2n, T/Th/Td/O/Oh/I/Ih. Infinite groups excluded. Common groups: ', '支持 Cn/Cnv/Cnh、Dn/Dnh/Dnd、S2n、T/Th/Td/O/Oh/I/Ih；无限群不适用。常用：', '支援 Cn/Cnv/Cnh、Dn/Dnh/Dnd、S2n、T/Th/Td/O/Oh/I/Ih；無限群不適用。常用：'),
'cli_table_note': ('X rows: irreps; columns: conjugacy classes; W=diag(n_j). Do not multiply c by n_j.', 'X: 行=不可约表示；列=共轭类；W=diag(n_j)。输入类代表的特征标，不乘 n_j。', 'X：橫列=不可約表示；直欄=共軛類；W=diag(n_j)。輸入類代表的特徵標，不乘 n_j。'),
'cli_orthogonality': ('Orthogonality error = {value}', '正交性误差 = {value}', '正交性誤差 = {value}'),
'cli_cancelled': ('Cancelled.', '已取消。', '已取消。'),
})

ERRORS = {
'数值表达式过长。': ('Numeric expression is too long.', '數值運算式過長。'),
'表达式过于复杂。': ('Expression is too complex.', '運算式過於複雜。'),
'只支持数值、i、pi、四则运算、幂及 sqrt/exp/cos/sin。': ('Use numbers, i, pi, arithmetic, powers and sqrt/exp/cos/sin only.', '僅支援數值、i、pi、四則運算、冪及 sqrt/exp/cos/sin。'),
'不能输入 NaN 或无穷大。': ('NaN and infinity are not allowed.', '不可輸入 NaN 或無窮大。'),
'无效的数值表达式。': ('Invalid numeric expression.', '無效的數值運算式。'),
'输入必须是有限数。': ('Input must be finite.', '輸入必須是有限數。'),
'特征标表必须为完整的方阵。': ('Character table must be a complete square matrix.', '特徵標表必須為完整的方陣。'),
'不可约表示维数平方和不等于 h。': ('Sum of squared irrep dimensions does not equal h.', '不可約表示維度平方和不等於 h。'),
'l 必须为非负整数。': ('l must be a nonnegative integer.', 'l 必須為非負整數。'),
'容差必须大于 0 且小于 0.01。': ('Tolerance must be between 0 and 0.01.', '容差必須大於 0 且小於 0.01。'),
'这是无限群，h 不是有限数，不能使用有限的 X、W 和 c。需以连续特征标函数及 Haar 积分约化；本程序的有限群模式不适用。': ('This is an infinite group. Finite h, X, W and c cannot be used; continuous characters and Haar integration are required.', '這是無限群，無法使用有限的 h、X、W、c；須使用連續特徵標函數與 Haar 積分約化。'),
'未知点群。支持 Cn、Cnv、Cnh、Dn、Dnh、Dnd、S2n、T/Th/Td/O/Oh/I/Ih。': ('Unknown group. Supported: Cn, Cnv, Cnh, Dn, Dnh, Dnd, S2n, T/Th/Td/O/Oh/I/Ih.', '未知點群。支援 Cn、Cnv、Cnh、Dn、Dnh、Dnd、S2n、T/Th/Td/O/Oh/I/Ih。'),
'此实现为稠密矩阵，单次 n 上限为 2000；不是数学上的点群限制。': ('This dense-matrix implementation limits n to 2000; this is not a mathematical group limit.', '此實作使用稠密矩陣，單次 n 上限為 2000；這不是數學上的點群限制。'),
'该点群名称无效；Dn 系列要求 n≥2，S 系列不带后缀。': ('Invalid group name. Dn requires n ≥ 2; S groups have no suffix.', '該點群名稱無效；Dn 系列要求 n≥2，S 系列不帶後綴。'),
}


def tr(key, language='zh-Hans', **values):
    index = {'en': 0, 'zh-Hans': 1, 'zh-Hant': 2}[language]
    return MESSAGES[key][index].format(**values)


def error_text(error, language):
    text = str(error)
    import re
    match = re.fullmatch(r'需要 (\d+) 个特征标，每个共轭类输入一个。', text)
    if match:
        return tr('need_count', language, count=match[1])
    if text in ERRORS:
        return text if language == 'zh-Hans' else ERRORS[text][0 if language == 'en' else 1]
    return text


class UIError(ValueError):
    def __init__(self, key, language='zh-Hans', **values):
        self.key, self.values = key, values
        translated = dict(values)
        if 'reason' in translated:
            translated['reason'] = error_text(translated['reason'], language)
        super().__init__(tr(key, language, **translated))



def group_notes(table, language):
    notes = [tr('generator_note', language)]
    if table.name.startswith('S') and len(table.classes)>1:
        notes.append(tr('cyclic_convention', language, generator=table.classes[1], order=table.h))
    elif table.name.startswith(('C','D')):
        notes.append(tr('axis_convention', language))
    if table.name.endswith('h') and table.name != 'Th' or any(x.endswith(('g', 'u')) for x in table.irreps):
        notes.append(tr('product_note', language))
    if table.name.startswith(('T', 'O', 'I')):
        notes.append(tr('polyhedral_note', language))
    return '\n'.join(notes)

