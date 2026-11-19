# Point Groups & Basis Functions 0.4.5

[简体中文](README.md) · [繁體中文](README.zh-Hant.md)

Use positions and s/p/d functions to construct representation matrices, reduce their characters and generate SALC coefficients for every irrep copy. A second workflow reduces characters entered by hand.

On Windows or macOS, download `BasisCharacterPrototype-0.4.5-en.html` and open it offline in a browser. All three language variants have the same calculations and language selector. Choose `-zh-Hans.html` or `-zh-Hant.html` for a Chinese default. The release includes the module source ZIP and `SHA256SUMS.txt`. [Download 0.4.5](https://github.com/lightzfpwings/pointgroup-reducer/releases/tag/basis-v0.4.5)

The previous release provides native packages for Windows x64 and Apple silicon Macs. Updated native packages are pending publisher signing and verification. [0.4.4 native downloads](https://github.com/lightzfpwings/pointgroup-reducer/releases/tag/basis-v0.4.4) · [Signing and notarization](SIGNING.md)

**From basis functions** supports 87 verified spatial point groups. Expand representative positions by symmetry or enter individual sites, add s, p and five real d harmonics, and calculate. The application constructs the full representation matrices, identifies closed blocks in the chosen basis, computes characters, and reduces both the total space and each block.

**Enter characters** retains the original reducer's 423 selectable finite point groups. Enter one unweighted character per conjugacy class in the table order. Separate values with commas or semicolons. Expressions support i, π, sqrt, cos, sin, exp and arithmetic. Complex conjugate irreps remain separate rows. Reduction uses `a = X.conj() @ W @ c / h`; successful results require nonnegative integer multiplicities and reconstruction within tolerance.

Both workflows provide MathML subscripts, superscripts, fractions, radicals and complex values, together with text/LaTeX copying, input saving and full result export. Basis JSON files from versions 0.1–0.3 remain readable; results are recomputed rather than trusted from the file.

After calculating **From basis functions**, choose **Generate SALC coefficients**, then select an irrep and copy. Each column gives one combination $\psi = \sum_j c_j \phi_j$ in the original function order. Copying includes the selected copy. Full JSON export includes every generated copy. In the xz-plane water example, the H 1s orbitals give the normalized sum (A1) and difference (B1), each with coefficient magnitudes 1/√2.

The character projector is $P_\alpha = \frac{d_\alpha}{|G|}\sum_{g\in G}\chi_\alpha(g)^*D(g)$, with * denoting complex conjugation. The calculation constructs partner functions for each repeated irrep and checks orthogonality, invariance under the generators and the character of each copy. The model treats different sites, radial IDs and angular momenta as orthogonal. Within each group it uses direction dot products for p and tensor Frobenius products for d. Overall phases, bases within degenerate spaces and the choice of equivalent copies are free. [MIT representation theory notes](https://ocw.mit.edu/courses/18-712-introduction-to-representation-theory-fall-2010/24d8b3fa2ce48e48ee6c2d8d5e3562f6_MIT18_712F10_replect.pdf)

Try **Central d · Oₕ**: five global d functions form blocks of dimensions 3 and 2, yielding T2g + Eg. In C2v, all five components are separately closed and the total is 2A1 + A2 + B1 + B2. The water example yields A1 + B1. Benzene has 30 functions and four closed blocks, with independent equivalent copies retained.

The d basis is the five real spherical harmonics dxy, dxz, dyz, dx²−y² and dz²; dz² means 2z²−x²−y². Symmetric traceless tensors are orthonormal under the Frobenius inner product and transform actively as `Q → RQRᵀ`. Local frame columns give local axes in global coordinates. Enter perpendicular local x′ and z′ directions; the application constructs right-handed y′. Sites need not be at the origin, but must respect the selected symmetry. Add different local frames to individually selected sites when needed.

QR factorization expands transformed functions in a nonorthogonal angular basis, with a reconstruction check for each transformation.

Limits are 120 sites and 180 functions. Radial IDs identify copies; this is not a quantum-chemistry basis library. Closed blocks need not be irreducible and can change with the chosen basis. Cartesian six-component d, automatic point-group identification, XYZ import, AO overlap integrals and electronic energies are not implemented.

Character-table expressions display exact formulas; calculations use double precision. Exports retain full numeric precision and tolerances rather than claiming symbolic proofs. The original Python reducer remains compatible, with this integrated app in a separate directory. Synced project sources remain unchanged. The application runs without the original Python program. Tests compare all 423 complex tables and each original irrep's reduction, alongside integrated workflows, parsing, language switching and legacy input compatibility.

Version 0.4.2 corrects orbital and direction subscripts, group/irrep scripts, angle fractions, scientific notation, and upright imaginary units and function names. Bold a/X/W/c use a star explicitly defined as elementwise conjugation without transposition. MathML and LaTeX share an expression tree that preserves signs, fractions, powers and grouping; small nonzero values are retained.

Version 0.4.2 fixes mathematical table headers displaying `[object MathMLMathElement]`. Headers and body cells share node insertion. Regression checks cover character, basis-result, manual-result and vector tables in all three languages.

Version 0.4.3 adds the Windows x64 wrapper, native JSON dialogs, clipboard support and remembered language menus. It also fixes position-tolerance editing. Run `python packaging/build_windows.py` on Windows x64 with the .NET 10 SDK to build the package. The package self-check runs the shared calculation script through Jint. The 0.4.4 Windows executable has no Authenticode signature. The original release includes the offline WebView2 installer, and the lightweight ZIP includes a download shortcut.
