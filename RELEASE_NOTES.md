## v2.3.1 · Formula background and clipping fixes

- Transparent math images blend into page, table heading and selected-row backgrounds.
- Measure glyph bounds at the actual display DPI and add safety margins on every side, fixing clipped symbols such as D6h.
- Table rows and input panels grow to fit their rendered symbols.
- Retains English / 简体中文 / 繁體中文 and all existing calculation and navigation features.
- 31 source tests, including transparency and margins at 96, 110, 144 and 192 DPI. Native GUI geometry and frozen GUI/CLI checks must pass before publication. Manual Windows/macOS click acceptance remains pending.

## 简体中文

修复公式区域白色背景与界面不一致的问题；增加公式四周留白，修复 D6h 等符号顶部被裁切的问题。表格行高和输入区高度自动适应公式尺寸。下载对应系统的 ZIP，完整解压后双击启动，无需安装 Python 或 LaTeX。

## 繁體中文

修復公式區域白色背景與介面不一致的問題；增加公式四周留白，修復 D6h 等符號頂部被裁切的問題。表格列高與輸入區高度自動配合公式尺寸。下載對應系統的 ZIP，完整解壓縮後雙擊啟動，無須安裝 Python 或 LaTeX。
