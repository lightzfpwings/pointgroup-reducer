# Point Group Reducer · 点群特征标约化

[English](README.en.md) · [繁體中文](README.zh-Hant.md)

## 点群与基函数整合版 0.4.2

[下载整合版](https://github.com/lightzfpwings/pointgroup-reducer/releases/tag/basis-v0.4.2) · [完整说明](basis-character-prototype/README.md)

新增完整流程：位置与 s/p/d 基函数 → 可约特征标 → 全体及各封闭块的不可约组成。几何入口支持 87 个真实空间点群，手动约化入口支持 423 个点群。界面、数学公式、上下标和 LaTeX 输出统一，简体中文／繁体中文／English 可切换并保留输入与结果。

Apple 芯片 Mac 下载 `BasisCharacter-0.4.2-macOS-arm64.zip`，完整解压后打开 `BasisCharacter.app`。Windows、Linux 和 Mac 均可下载任一三语离线 HTML，保存后用浏览器打开。无需联网或安装开发环境。

整合版位于 `basis-character-prototype/`，使用独立版本标签 `basis-v0.4.2`。原 Python/Tk 约化器及 CLI 保留，原生 Windows 旧版下载见 [v2.4.3](https://github.com/lightzfpwings/pointgroup-reducer/releases/tag/v2.4.3)。下文介绍原 Python/Tk 版本。

输入表示的特征标向量 **c**，计算重数 **a**，输出不可约表示分解。

$$\mathbf a=\frac1h X^*W\mathbf c$$

X 每行对应一个完整的复不可约表示，W 的对角元素是共轭类操作数，h 是群阶。输入的 c 必须与表的列顺序一致，每类输入一个数，不自行乘类内操作数。

## 下载和启动

在本仓库 **Releases** 页面下载与系统对应的 ZIP，完整解压后双击启动。独立应用自带运行环境，无需安装 Python 或 LaTeX。

| 系统 | 下载包后缀 | 图形界面入口 |
|---|---|---|
| Windows 64 位 | Windows-x64.zip | PointGroupReducer/PointGroupReducer.exe |
| Mac M 系列 | macOS-arm64.zip | PointGroupReducer.app |

Windows 保留同目录下的 `_internal` 文件夹；macOS 命令行入口为 `Start-CLI.command`。应用未经过开发者签名或 Apple 公证。

## 数学排版与语言切换

- 点群名称、操作表头、特征标、不可约表示及结果公式使用离线数学排版，显示上下标、根号、分数、虚数 i、π 和角度。
- 表头与行高按公式尺寸计算，符号在单元格内居中；表格不显示类内操作数行及左上角标题。
- 结果页与复制文本保留分解、特征标、重数和表示维数，不再显示底部的重建误差。
- 窗口右上角或“语言”菜单切换 **English / 简体中文 / 繁體中文**。按钮、步骤提示、错误反馈和使用说明同步更新。
- 切换语言保留点群、已输入的 c、粘贴框内容和计算结果；语言偏好会保存，下次启动沿用。
- 结果页可“复制文本”或“复制 LaTeX”。LaTeX 包含约化公式、c/a 向量，以及合法表示的分解。
- 命令行支持 `--lang en` / `--lang zh-Hans` / `--lang zh-Hant`；交互步骤中输入 `lang` 可切换语言。
- JSON 保留稳定的点群标签、类顺序和数据字段，不随界面语言改变。

## 操作

“选择点群 → 输入特征标 c → 查看结果”。d 轨道示例只填入数值，再点击“计算”。输入不完整或数值有误时，提示会指出具体共轭类。

| 操作 | 图形界面 | 命令行 |
|---|---|---|
| 返回上一步 | 上一步 / Esc | `0` |
| 返回主页 | 返回主页；Windows Ctrl+Home / Mac Command+Shift+H | `home` |
| 退出 | 退出；Windows Ctrl+Q / Mac Command+Q | `q` |
| 单独输入数值零 | `0` | `=0` |

返回和主页保留输入；更换点群清空旧输入。逗号向量内的 `0` 可直接写。

## 支持范围

下拉列表提供 **423 个点群**：Cn/Cnv/Cnh 与 Dn/Dnh/Dnd 的 n=2…60、S4…S120（偶数），以及 C1、Cs、Ci 和七个多面体点群。输入名称可筛选列表；更高阶可直接输入名称，按回车载入。

对称操作表头直接显示旋转、镜面或反演名称。例如 C2v 的四列为 E、C2、σᵥ(xz)、σᵥ(yz)。轴向点群的主旋转轴默认沿 z（包括 C3 及更高阶轴）；xy 为水平面，xz、yz 为垂直面。其他镜面或垂直二重轴用精确方位角 φ 标注，从 +x 向 +y 测量。多面体群可选一条最高阶旋转轴为 z，同一类的其他等价轴不必平行于 z。名称调整保留原有列顺序及对应特征标。

有限普通三维点群：C1、Cs、Ci；Cn、Cnv、Cnh；Dn、Dnh、Dnd；S2n；T、Th、Td、O、Oh、I、Ih。系列按需生成，目前 n ≤ 2000；大 n 的稠密矩阵需要较多内存。

支持复特征标、非负整数重数检查、d 轨道示例、JSON/CSV 导出。E+ / E− 各为一维复共轭表示，不能各当作二维 E；标签和类顺序可能与教材不同，以本程序表为准。无限点群 C∞v、D∞h 不适用此有限矩阵公式；不包含双群、磁群、空间群。

## 源码运行

Python 3.10+，含 Tkinter。

```bash
python -m pip install -r requirements.txt
python pointgroup.py --gui --lang en
python pointgroup.py C2v --c "5,1,1,1" --lang zh-Hant
python pointgroup.py
python -m unittest -v
```

数值支持 `1/2`、`sqrt(5)`、`1+2i`、`exp(2*pi*i/3)` 等受限表达式。

## 打包和验证

在目标 Windows 或 macOS 的原生 Python 3.12 环境：

```bash
python -m pip install -r requirements-build.txt
python packaging/build_native.py
```

构建先执行 51 项源码测试，以及真实 Tk 的数学渲染、三语切换、输入保留、复制和导出检查；封装后再检查独立 GUI/CLI 启动及示例计算。输出 ZIP、SHA-256 和构建记录。GUI 使用离线 MathText，用户无需安装 LaTeX。

发布工作流只构建 Windows x64 和 Apple 芯片 Mac，两个平台检查均通过后发布。main 分支的 `[release]` 提交、与 VERSION 对应的标签或手动选择 publish 可触发发布。发布页提供两个 ZIP 和统一的 SHA256SUMS.txt；具体构建状态以 Actions 和 BUILD-INFO.json 为准。
