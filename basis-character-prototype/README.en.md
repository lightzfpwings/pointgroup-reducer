# Point Groups & Basis Functions 0.4.2

[简体中文](README.md) · [繁體中文](README.zh-Hant.md)

[Published release 0.4.2](https://github.com/lightzfpwings/pointgroup-reducer/releases/tag/basis-v0.4.2)

An offline application that connects positions and s/p/d basis functions to reducible characters and irreducible decompositions. Both workflows share a simple white interface, class conventions, mathematical tables, and output formatting. Switch between English, Simplified Chinese and Traditional Chinese using the top-right selector or the Mac Language menu. Inputs, results and inspector selections are preserved; the preference is remembered.

On an Apple silicon Mac running macOS 12+, extract the ZIP, quit the previous version, and open `BasisCharacter.app`. No Python, Node, browser or network is required. The `offline/` folder also contains standalone HTML files starting in each of the three languages; every file supports switching languages.

**From basis functions** supports 87 verified spatial point groups. Expand representative positions by symmetry or enter individual sites, add s, p and five real d harmonics, and calculate. The application constructs the full representation matrices, identifies closed blocks in the chosen basis, computes characters, and reduces both the total space and each block.

**Enter characters** retains the original reducer's 423 selectable finite point groups. Enter one unweighted character per conjugacy class in the table order. Separate values with commas or semicolons. Expressions support i, π, sqrt, cos, sin, exp and arithmetic. Complex conjugate irreps remain separate rows. Reduction uses `a = X.conj() @ W @ c / h`; successful results require nonnegative integer multiplicities and reconstruction within tolerance.

Both workflows provide MathML subscripts, superscripts, fractions, radicals and complex values, together with text/LaTeX copying, input saving and full result export. Basis JSON files from versions 0.1–0.3 remain readable; results are recomputed rather than trusted from the file.

Try **Central d · Oₕ**: five global d functions form blocks of dimensions 3 and 2, yielding T2g + Eg. In C2v, all five components are separately closed and the total is 2A1 + A2 + B1 + B2. The water example yields A1 + B1. Benzene has 30 functions and four closed blocks, with independent equivalent copies retained.

The d basis is the five real spherical harmonics dxy, dxz, dyz, dx²−y² and dz²; dz² means 2z²−x²−y². Symmetric traceless tensors are orthonormal under the Frobenius inner product and transform actively as `Q → RQRᵀ`. Local frame columns give local axes in global coordinates. Enter perpendicular local x′ and z′ directions; the application constructs right-handed y′. Sites need not be at the origin, but must respect the selected symmetry. Add different local frames to individually selected sites when needed.

Limits are 120 sites and 180 functions. Radial IDs identify copies; this is not a quantum-chemistry basis library. Closed blocks need not be irreducible and can change with the chosen basis. Cartesian six-component d, automatic point-group identification, XYZ import, AO overlap integrals, SALC coefficients and electronic energies are not implemented.

Character-table expressions display exact formulas; calculations use double precision. Exports retain full numeric precision and tolerances rather than claiming symbolic proofs. The original Python reducer remains compatible, with this integrated app in a separate directory. Synced project sources remain unchanged. The application runs without the original Python program. Tests compare all 423 complex tables and each original irrep's reduction, alongside integrated workflows, parsing, language switching and legacy input compatibility.

The Mac app uses an ad-hoc local signature and is not Apple Developer signed or notarized. Mathematical, event and packaging checks do not constitute automated visual verification of browser layout, native windows or system file dialogs. The user approved this version for publication after manual use.

Version 0.4.2 corrects orbital and direction subscripts, group/irrep scripts, angle fractions, scientific notation, and upright imaginary units and function names. Bold a/X/W/c use a star explicitly defined as elementwise conjugation without transposition. MathML and LaTeX share an expression tree that preserves signs, fractions, powers and grouping; small nonzero values are retained.

Version 0.4.2 fixes mathematical table headers displaying `[object MathMLMathElement]`. Headers and body cells share node insertion. Regression checks cover character, basis-result, manual-result and vector tables in all three languages.
