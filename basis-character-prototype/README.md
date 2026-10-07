# 点群与基函数 0.4.2

[English](README.en.md) · [繁體中文](README.zh-Hant.md)

[正式发布 0.4.2](https://github.com/lightzfpwings/pointgroup-reducer/releases/tag/basis-v0.4.2)

将位置与 s/p/d 基函数计算、可约特征标和不可约分解整合在同一离线应用中。保留简洁白底单栏，公式、表格、复制文本与 LaTeX 使用一致的数学约定。右上角或 Mac“语言”菜单可切换简体中文、繁体中文和 English，切换保留输入、结果与查看状态，并记住偏好。

## 启动

Mac Apple 芯片：解压 `dist/BasisCharacter-0.4.2-macOS-arm64.zip`，退出旧版后打开 `BasisCharacter.app`。支持 macOS 12+，不需要 Python、Node、浏览器或联网。ZIP 的 `offline/` 目录另有三种默认语言的 HTML 版本。

浏览器版：直接打开 `dist/BasisCharacterPrototype-0.4.2-zh-Hans.html`、`…-zh-Hant.html` 或 `…-en.html`。每份文件均包含全部功能和三语切换。开发页 `index.html` 需要同目录九个 JS 文件。

应用仍使用本地临时签名，未 Apple 开发者签名或公证。自动化检查覆盖计算与应用事件；自动化未进行桌面窗口、浏览器排版和系统文件对话框的视觉验收；本版本已获用户试用后的发布批准。

## 两种计算方式

**从基函数计算**：选择已验证的 87 个真实空间点群之一，输入代表位置并对称展开，或逐中心输入。添加 s、全局或自定义 p、五个实 d 分量；程序逐函数构建 D(g)、识别当前基下的封闭块、计算特征标，并自动约化全体及各块。点群范围为 C1/Cs/Ci；Cn/Cnv/Cnh、Dn/Dnh/Dnd（n=2…12）；S4…S24（偶数）；T/Th/Td/O/Oh/I/Ih。

**手动输入特征标**：保留原程序可选的 423 个有限点群，轴向族 n 至 60、S 至 120。按当前表列顺序输入每类一个值，不乘类大小。逗号或分号分隔，可用 i、π、sqrt、cos、sin、exp、四则运算和幂。保留完整复不可约表示，E+/E− 不合并成一行。分解仍采用 `a = X.conj() @ W @ c / h`，检查非负整数重数及重建误差；非法输入不会输出成功分解。

两条入口使用同一特征标表、类顺序、MathML 数学排版和结果格式。展示 X 的精确公式与根式；实际计算使用双精度，导出保留完整精度及容差，不把数值结果冒充符号证明。输入框的表达式有长度和复杂度限制，不调用 eval。

## 示例与保存

- 苯 D6h：30 个函数、五个输入批次，自动识别四个封闭块，再分别输出不可约组成。C px/py 联合；C 2s 与 H 1s 保留两个独立等价副本。
- 水 C2v：xz 平面内两个 H 的 s，分解为 A1 + B1。
- 中心 p：C2v 三个独立分量；Oh 三者联合。
- 中心 d Oh：全局坐标五个 d 自动分为 3+2 维块，分解为 T2g + Eg。C2v 五个分量分别封闭，总体为 2A1 + A2 + B1 + B2。
- 二十面体 Ih：+z 代表位置生成十二个 s，分解为 Ag + Hg + T1u + T2u。

保存输入、载入、撤销、导出完整结果、单独导出向量、复制文本和 LaTeX 都在同一应用内完成。0.1–0.3 的基函数 JSON 仍可载入；载入后重新计算，不信任文件内旧结果。手动输入另存为 `input.mode = "manual"`。语言偏好与数学输入分离。

## d 和变换约定

主动操作 `U(g)φ_j = Σ_i φ_i D_ij(g)`；位置 `r → Rr`、p 方向 `u → Ru`。每个中心/径向类型最多三个独立 p；非正交方向通过 Gram 矩阵准确展开，不丢弃残差。

d 为五维实球谐函数 dxy、dxz、dyz、dx²−y²、dz²（即 2z²−x²−y²）。对称无迹张量 Q 满足 `f(x)=xᵀQx`；标准张量按 Frobenius 内积正交归一，变换为 `Q → RQRᵀ`。局部轴矩阵 A 的列为 x′/y′/z′ 在全局坐标中的方向，轨道为 `AQ₀Aᵀ`。高级设置输入垂直的 x′、z′，系统生成右手 y′。同批中心共用轴；不同中心可分别选中添加。

d 的中心可在原点或对称相容的非原点位置。JSON 使用 `family:"d"`、`component:"dxy"` 等标识和可选 `frame`；缺省为单位矩阵。径向 ID 是副本标识，不是量子化学基组库。最多 120 个中心、180 个函数。

“封闭计算块”不一定不可约，也不保证是最小不变空间；换基会改变当前块结构。各独立等价副本均保留。六维 Cartesian d、自动点群识别、XYZ 导入、实际 AO 重叠积分、SALC 系数及电子能量尚未实现。

## 模块与验证

几何引擎仍独立；适配器明确映射共轭类，轴向群匹配实际空间矩阵，多面体群保留明确逐类对应。新增约化引擎采用原程序的完整复表及数值算法，生成 423 张解析表。原有 Python 约化代码保持兼容，整合版位于独立目录；同步 `sources/` 未修改，运行整合版无需原 Python 程序。

原数学约定来源：[core.py](https://github.com/lightzfpwings/pointgroup-reducer/blob/main/core.py)、[operation_labels.py](https://github.com/lightzfpwings/pointgroup-reducer/blob/main/operation_labels.py)。固定快照记录检索日期和源文件 SHA-256。测试逐项比较原表数值、列/行名称及每个原不可约行的约化结果，并核验基函数链、复数解析、错误处理、三语切换、复制和旧文件兼容性。

开发：先 `python3 build.py`，再 `node --test tests/*.test.js`。Mac 封装 `python3 packaging/build_macos.py`，需要 Apple 命令行工具；构建后执行签名校验与 Apple JavaScriptCore 自检。DOM 替身测试与数学节点检查不等于浏览器渲染验收。独立结果和测试证据见 `validation/`。

0.4.2 修正数学排版：p/d 与方向分量使用正规下标，群名及不可约符号上下标一致，角度以 φ 和 π 分数显示；科学计数法使用 ×10 的幂，复数单位 i 与函数名直立。约化公式使用粗体 a/X/W/c，星号明确表示逐项复共轭，不含转置。MathML 与 LaTeX 共用表达式树，保留负号、分数、幂与括号的数值含义；小的非零数不再显示为零。

0.4.2 修复数学表头变成 `[object MathMLMathElement]` 的问题。表头与正文共用节点插入逻辑；三语的特征标表、基函数结果表、手动输入结果表与向量表均检查数学表头节点。
