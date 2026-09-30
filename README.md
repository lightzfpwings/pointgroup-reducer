# Point Group Reducer · 点群特征标约化

输入表示的特征标向量 **c**，计算约化系数 **a**，输出不可约表示分解。

```text
a = (1/h) X.conj() W c
C2v：c = [5,1,1,1] → a = [2,1,1,1]
Γ = 2A1 + A2 + B1 + B2
```

X 的每一行是一种完整的复不可约表示；W 的对角线是各共轭类的操作数，h 为群阶。c 的分量顺序必须与表的列顺序一致，每类输入一个值，不要自行乘类内操作数。

## 下载和双击使用

在仓库的 **Releases** 页面选择对应平台的 ZIP，完整解压后启动。仅已成功构建并上传的文件可下载；源码仓库里的工作流不等于已有预编译发行版。

| 发行包 | 图形界面入口 | 命令行入口 |
|---|---|---|
| GitHub 原生构建的 Windows x64 包 | `PointGroupReducer/PointGroupReducer.exe` | `PointGroupReducer-CLI/PointGroupReducer-CLI.exe` |
| Windows 旧便携结构的 2.2.0 更新包 | 根目录 `PointGroupReducer.exe` | 根目录 `PointGroupReducer-CLI.exe` |
| GitHub 原生构建的 macOS 包 | `PointGroupReducer.app` | `Start-CLI.command` |
| macOS 本机封装源码包 | 先运行 `1_首次封装.command`，再打开生成的 `.app` | 打开生成的 `PointGroupReducer-CLI.command` |

Windows 请保留应用旁边的 `_internal` 文件夹。macOS 本机封装包首次需要含 Tkinter 的 Python 3.12 或 3.13，联网封装后，生成的应用即可独立运行。应用未经过开发者签名或 Apple 公证。

图形界面流程：**选择点群 → 输入特征标 c → 查看结果**。每页只有当前步骤的操作提示，公式和其他说明在“使用说明”中。

- “填入五个 d 轨道示例”只填入数据，请再点击“计算”。
- 输入不完整或数值有误时，窗口下方会指出具体的共轭类。
- 图形输入框中的 `0` 是数值零。
- 返回会保留输入；更换点群会清空旧输入。

| 操作 | 图形界面 | 命令行 |
|---|---|---|
| 返回上一步 | “上一步”或 Esc | `0` |
| 返回主页 | “返回主页”；Windows Ctrl+Home，Mac Command+Shift+H | `home` |
| 退出 | “退出”、关闭窗口；Windows Ctrl+Q，Mac Command+Q | `q` |
| 单独输入数值零 | `0` | `=0` |

## 支持的点群

有限普通三维点群：C1、Cs、Ci；Cn、Cnv、Cnh；Dn、Dnh、Dnd；S2n；T、Th、Td、O、Oh、I、Ih。系列按需生成，当前 n ≤ 2000；大 n 的稠密矩阵需要较多内存。

支持复特征标、非负整数重数检查、d 轨道示例、JSON/CSV 导出。GUI 导出 JSON；CLI 可导出 JSON 和 CSV。E+ / E− 是一维复共轭表示，不能分别作为二维 E。程序标签和类顺序可能与教材不同，请先查看表。

无限点群 C∞v、D∞h 不适用有限 h、X、W 公式；不包含双群、磁群或空间群。

## 从源码运行

需要 Python 3.10 或更新版本和 Tkinter。

```bash
python -m pip install -r requirements.txt
python pointgroup.py             # 命令行菜单
python pointgroup.py --gui       # 图形界面
python pointgroup.py C2v --c "5,1,1,1"
python pointgroup.py D4h --shell 2
python pointgroup.py C3v --table
python -m unittest -v
```

数值支持 `1/2`、`sqrt(5)`、`1+2i`、`exp(2*pi*i/3)` 等受限表达式。

## 本机独立应用构建

在目标操作系统、原生架构的 Python 3.12 环境运行：

```bash
python -m pip install -r requirements-build.txt
python packaging/build_native.py
```

Windows 也可双击 `packaging/windows/Build-Windows.cmd`；macOS 可运行 `packaging/macos/Build-macOS.command`。构建工具会运行源码测试和原生 GUI/CLI 启动检查，再生成 `release/` 下的 ZIP、SHA-256、依赖和系统记录。它不会覆盖同名已有结果目录。

## GitHub 自动构建与发布

`.github/workflows/release.yml` 支持手动执行和 `v*` 标签。分别使用 Windows、macOS Apple Silicon、macOS Intel runner 原生构建，生成可独立运行的发行包。

手动执行先提供 Actions 下载文件。手动执行并选择发布，或推送与 VERSION 一致的标签（当前 `v2.2.0`），在三个平台都通过后创建 GitHub Release 并上传 ZIP 与校验文件。发布工作流需要仓库允许 GitHub Actions 和内容写入权限。私有仓库的执行受账户 Actions 额度限制。

## 当前验证范围

2.2.0 已在 Linux 上通过 21 项源码测试（含 213 个点群实例）和真实 Tk 控件交互检查。此处未做 Windows/macOS 实机人工点击验收。现有 Windows 便携更新包沿用先前 bootloader 和运行库，仅更新加载的源码；其构建记录中不声称通过 Windows 实机验收。

GitHub 原生发行包必须以实际工作流结果为准；未执行的工作流不代表这些平台已经构建成功。macOS 本机封装包仍需在 Mac 上执行首次封装。
