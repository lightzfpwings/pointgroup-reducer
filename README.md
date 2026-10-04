# Point Group Reducer · 点群特征标约化

[English](README.en.md) · [繁體中文](README.zh-Hant.md)

输入表示的特征标向量 **c**，计算重数 **a**，输出不可约表示分解。

$$\mathbf a=\frac1h X^*W\mathbf c$$

X 每行对应一个完整的复不可约表示，W 的对角元素是共轭类操作数，h 是群阶。输入的 c 必须与表的列顺序一致，每类输入一个数，不自行乘类内操作数。

## 下载和启动

在本仓库 **Releases** 页面下载与系统对应的 ZIP，完整解压后双击启动。独立应用自带运行环境，无需安装 Python 或 LaTeX。

| 系统 | 下载包后缀 | 图形界面入口 |
|---|---|---|
| Windows 64 位 | Windows-x64.zip | PointGroupReducer/PointGroupReducer.exe |
| Mac M 系列 | macOS-arm64.zip | PointGroupReducer.app |
| Intel Mac | macOS-x64.zip | PointGroupReducer.app |

Windows 保留同目录下的 `_internal` 文件夹；macOS 命令行入口为 `Start-CLI.command`。应用未经过开发者签名或 Apple 公证。私有仓库需登录有权限的 GitHub 账号。

## v2.3.0 数学排版与语言切换

- 点群名称、共轭类表头、不可约表示和结果公式采用 MathText 数学渲染，正确显示上下标、撇号、复共轭表示的正负号。
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

对称操作表头直接显示旋转、镜面或反演名称。例如 C2v 的四列为 E、C2、sigma_v(xz)、sigma_v(yz)。轴向点群的主旋转轴默认沿 z（包括 C3 及更高阶轴）；xy 为水平面，xz、yz 为垂直面。其他镜面或垂直二重轴用精确方位角 phi 标注，从 +x 向 +y 测量。多面体群可选一条最高阶旋转轴为 z，同一类的其他等价轴不必平行于 z。名称调整保留原有列顺序及对应特征标。

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

构建先执行 50 项源码测试，以及真实 Tk 的数学渲染、三语切换、输入保留、复制和导出检查；封装后再检查独立 GUI/CLI 启动及示例计算。输出 ZIP、SHA-256 和构建记录。GUI 使用离线 MathText，用户无需安装 LaTeX。

`.github/workflows/release.yml` 在三个平台都通过后才发布。手动执行并选中 publish，或推送与 VERSION 对应的标签（v2.3.0）。构建检查不替代 Windows/macOS 实机人工点击验收；具体状态以 Actions 和发行包 BUILD-INFO.json 为准。
