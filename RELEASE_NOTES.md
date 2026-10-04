# v2.4.3 · 结果简化与点群列表扩展

- 删除结果页底部的特征标重建误差，复制文本及命令行结果同步简化；计算合法性校验保留。
- 可选点群从 **42 个扩展到 423 个**。Cn/Cnv/Cnh、Dn/Dnh/Dnd 列至 n=60，S 系列列出 S4 至 S120 的偶数阶，保留 C1、Cs、Ci 与七个多面体点群。
- 输入点群名称可筛选下拉列表；更高阶仍可直接输入并按回车载入。
- 保留操作符号居中、完整公式显示及根号、虚数、π 和角度的数学排版。

只提供 Windows x64 和 Apple 芯片 Mac（arm64）独立软件包。完整解压后双击 `.exe` 或 `.app`，无需安装 Python 或 LaTeX。`SHA256SUMS.txt` 为统一校验文件。

发布前通过 51 项源码测试，计算回归覆盖全部 423 个可选点群，并在两个目标平台执行原生选择、结果显示、复制及封装后 GUI/CLI 检查。macOS 应用未经过 Apple 开发者签名或公证。

## English

Result pages, copied text and CLI results omit the final character-reconstruction error. Internal validity checks remain. The searchable selector expands from 42 to 423 groups: six cyclic/dihedral families through n=60, even S4…S120, C1/Cs/Ci and seven polyhedral groups. Higher orders remain available by manual entry. Centered operation headings and mathematical notation are retained.

Standalone packages support Windows x64 and Apple Silicon macOS. Publication requires 51 source tests covering all selectable groups and native/frozen GUI and CLI checks on both platforms.

## 繁體中文

刪除結果頁、複製文字與命令列結果底部的特徵標重建誤差，保留內部合法性檢查。可選點群從 42 個擴展至 423 個，各循環／二面體系列列至 n=60，S 系列列出 S4 至 S120 的偶數階，保留基本與多面體點群。輸入名稱可篩選，更高階仍可直接輸入。只提供 Windows x64 與 Apple 晶片 Mac 套件。
