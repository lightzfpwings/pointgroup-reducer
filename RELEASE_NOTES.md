## v2.4.1 · Exact symbolic values

- Character tables display fractions, radicals (such as √2), exact trigonometric values and complex components instead of decimal approximations.
- Exact expressions are generated from character formulas and retained from validated user input; rounded decimals are never guessed to be radicals.
- Result formulas, text/LaTeX copy, orbital examples and CSV retain symbolic values. JSON keeps its numeric fields and adds `X_symbolic` and `result.symbolic`.
- Table columns expand to fit longer symbolic expressions. Transparent formulas and smooth page transitions remain available.
- 43 source tests and native GUI/frozen application smoke checks gate publication.

## 简体中文

特征标、根号数、分数、三角函数和复数实部／虚部改用符号显示，例如 √2、−1/2 + √3*i/2。输入、轨道示例、结果公式、复制和 CSV 均保留符号形式。JSON 增加符号字段，同时保留用于计算的数值字段。表格列宽随表达式调整，保留透明公式背景和平滑过渡。

## 繁體中文

特徵標、根號數、分數、三角函數與複數實部／虛部改用符號顯示，例如 √2、−1/2 + √3*i/2。輸入、軌域範例、結果公式、複製與 CSV 均保留符號形式。JSON 新增符號欄位，同時保留用於計算的數值欄位。表格欄寬隨表達式調整，保留透明公式背景與平滑過渡。
