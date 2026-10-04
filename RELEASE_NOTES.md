# v2.4.2 · 数学表格显示修复

- 操作符号按实际公式尺寸调整表头高度，并在单元格内水平、垂直居中，修复遮挡与裁切。
- 特征标中的根号、分数、虚数 i、π 和角度采用数学排版。
- 删除“类内操作数”行及左上角“不可约表示”标题。
- 表头直接显示对称操作名称；轴向点群的主旋转轴默认沿 z。
- 调整窗口布局，使小屏幕上的输入区和底部按钮保持可见。

仅提供 **Windows x64** 和 **Apple 芯片 Mac（arm64）** 独立软件包。完整解压后双击 `.exe` 或 `.app`，无需安装 Python 或 LaTeX。`SHA256SUMS.txt` 为两份软件包的统一校验文件。

用户已确认 preview.2 显示正常；正式软件包在两个目标平台重新构建，通过 50 项源码测试、原生窗口布局及封装后的 GUI/CLI 检查。macOS 应用未经过 Apple 开发者签名或公证。

## English

Operation headings are centered inside measured cells with enough space for complete formulas. Character values now typeset radicals, fractions, imaginary i, π and angles. The class-size row and upper-left irrep heading are removed. Direct symmetry-operation names and the z-axis convention are retained, and compact windows keep their controls visible.

Standalone packages support Windows x64 and Apple Silicon macOS only. Extract the ZIP completely and launch the executable or app; Python and LaTeX are bundled or unnecessary. Both native builds pass 50 source tests and GUI/CLI smoke checks before publication.

## 繁體中文

修復操作符號被表頭遮擋及裁切的問題，依公式尺寸調整儲存格並置中。根號、分數、虛數 i、π 與角度改用數學排版；刪除「類內操作數」列與左上角標題。保留直接對稱操作名稱及 z 軸約定，調整小螢幕的輸入區與底部按鈕。

僅提供 Windows x64 與 Apple 晶片 Mac 獨立套件，完整解壓縮後雙擊啟動。
