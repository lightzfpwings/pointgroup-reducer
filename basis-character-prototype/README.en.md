# Point Groups & Basis Functions 0.6.0

Run `python3 build.py` in this directory and open the [0.6.0 English offline page](dist/BasisCharacterPrototype-0.6.0-en.html). Select **Vibrations (IR and Raman)**, open the [water XYZ file](examples/water.xyz) and select C₂ᵥ below the preview. Choose **Confirm structure and point group**, then **Calculate vibrations and activity**.

With only a formula, enter `C2H6O` in the same workflow, choose **Find structures**, then select **Ethanol · trans conformer** or **Dimethyl ether**. Review the selected model, coordinates and point group before calculating its IR and Raman activity.

[简体中文](README.md) · [繁體中文](README.zh-Hant.md)

Use positions and s/p/d functions to construct representation matrices, reduce their characters and generate SALC coefficients for every irrep copy. A second workflow reduces characters entered by hand.

Version 0.6.0 adds 39 organic structures and 21 coordination structures. The offline library now contains 221 candidates for 196 formulas when charge states are counted separately.

## Download and install

| Platform | Download | Install and launch |
|---|---|---|
| Debian or Ubuntu desktop | [BasisCharacter-0.6.0-Linux-all.deb](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.6.0/BasisCharacter-0.6.0-Linux-all.deb) | Run `sudo apt install ./BasisCharacter-0.6.0-Linux-all.deb` in the download directory. Open Point Groups & Basis Functions from the applications menu or run `basis-character`. The launcher uses xdg-utils to open the local page in your default graphical browser. |
| Apple silicon Mac, macOS 12 or later | [BasisCharacter-0.6.0-macOS-arm64.dmg](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.6.0/BasisCharacter-0.6.0-macOS-arm64.dmg) | Open the DMG and drag `BasisCharacter.app` into Applications. |
| Windows x64 | [BasisCharacter-0.6.0-Windows-x64.zip](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.6.0/BasisCharacter-0.6.0-Windows-x64.zip) | Extract the entire ZIP and open `BasisCharacter.exe`. If WebView2 is missing, install it using the bundled Microsoft offline runtime installer. |
| Android 8.0 or later | [BasisCharacter-0.6.0-Android.apk](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.6.0/BasisCharacter-0.6.0-Android.apk) | Open the APK on your device and follow the installation prompts. The app requires Android System WebView or a Chrome WebView provider version 109 or later. Use the system picker to open XYZ coordinates and to load or save JSON projects. |

The Mac app has an ad hoc signature and the DMG is unnotarized. The Windows application has no Authenticode publisher signature. Its bundled WebView2 installer is signed by Microsoft. The Android APK uses a dedicated project signing key for installation and future updates. macOS and Windows may display an unverified-publisher warning. [Signing details](SIGNING.md)

Standalone HTML files are also available in all three languages, alongside the source archive and `SHA256SUMS.txt`. [Download 0.6.0](https://github.com/lightzfpwings/pointgroup-reducer/releases/tag/basis-v0.6.0)

**From basis functions** supports 87 verified spatial point groups. Expand representative positions by symmetry or enter individual sites, add s, p and five real d harmonics, and calculate. The application constructs the full representation matrices, identifies closed blocks in the chosen basis, computes characters, and reduces both the total space and each block.

**Enter characters** retains the original reducer's 423 selectable finite point groups. Enter one unweighted character per conjugacy class in the table order. Separate values with commas or semicolons. Expressions support i, π, sqrt, cos, sin, exp and arithmetic. Complex conjugate irreps remain separate rows. Reduction uses `a = X.conj() @ W @ c / h`; successful results require nonnegative integer multiplicities and reconstruction within tolerance.

Both workflows provide MathML subscripts, superscripts, fractions, radicals and complex values, together with text/LaTeX copying, input saving and full result export. Basis JSON files from versions 0.1–0.3 remain readable; results are recomputed rather than trusted from the file.

After calculating **From basis functions**, choose **Generate SALC coefficients**, then select an irrep and copy. Each column gives one combination $\psi = \sum_j c_j \phi_j$ in the original function order. Copying includes the selected copy. Full JSON export includes every generated copy. In the xz-plane water example, the H 1s orbitals give the normalized sum (A1) and difference (B1), each with coefficient magnitudes 1/√2.

The character projector is $P_\alpha = \frac{d_\alpha}{|G|}\sum_{g\in G}\chi_\alpha(g)^*D(g)$, with * denoting complex conjugation. The calculation constructs partner functions for each repeated irrep and checks orthogonality, invariance under the generators and the character of each copy. The model treats different sites, radial IDs and angular momenta as orthogonal. Within each group it uses direction dot products for p and tensor Frobenius products for d. Overall phases, bases within degenerate spaces and the choice of equivalent copies are free. [MIT representation theory notes](https://ocw.mit.edu/courses/18-712-introduction-to-representation-theory-fall-2010/24d8b3fa2ce48e48ee6c2d8d5e3562f6_MIT18_712F10_replect.pdf)

Try **Central d · Oₕ**: five global d functions form blocks of dimensions 3 and 2, yielding T2g + Eg. In C2v, all five components are separately closed and the total is 2A1 + A2 + B1 + B2. The water example yields A1 + B1. Benzene has 30 functions and four closed blocks, with independent equivalent copies retained.

The d basis is the five real spherical harmonics dxy, dxz, dyz, dx²−y² and dz²; dz² means 2z²−x²−y². Symmetric traceless tensors are orthonormal under the Frobenius inner product and transform actively as `Q → RQRᵀ`. Local frame columns give local axes in global coordinates. Enter perpendicular local x′ and z′ directions; the application constructs right-handed y′. Sites need not be at the origin, but must respect the selected symmetry. Add different local frames to individually selected sites when needed.

QR factorization expands transformed functions in a nonorthogonal angular basis, with a reconstruction check for each transformation.

Limits are 120 sites and 180 functions. Radial IDs identify copies; this is not a quantum-chemistry basis library. Closed blocks need not be irreducible and can change with the chosen basis. Cartesian six-component d, automatic point-group identification, AO overlap integrals and electronic energies are not implemented.

Character-table expressions display exact formulas; calculations use double precision. Exports retain full numeric precision and tolerances rather than claiming symbolic proofs. The original Python reducer remains compatible, with this integrated app in a separate directory. Synced project sources remain unchanged. The application runs without the original Python program. Tests compare all 423 complex tables and each original irrep's reduction, alongside integrated workflows, parsing, language switching and legacy input compatibility.

Version 0.4.2 corrects orbital and direction subscripts, group/irrep scripts, angle fractions, scientific notation, and upright imaginary units and function names. Bold a/X/W/c use a star explicitly defined as elementwise conjugation without transposition. MathML and LaTeX share an expression tree that preserves signs, fractions, powers and grouping; small nonzero values are retained.

Version 0.4.2 fixes mathematical table headers displaying `[object MathMLMathElement]`. Headers and body cells share node insertion. Regression checks cover character, basis-result, manual-result and vector tables in all three languages.

Version 0.4.3 adds the Windows x64 wrapper, native JSON dialogs, clipboard support and remembered language menus. It also fixes position-tolerance editing. Run `python packaging/build_windows.py` on Windows x64 with the .NET 10 SDK to build the package. The package self-check runs the shared calculation script through Jint. The 0.4.4 Windows executable has no Authenticode signature. The original release includes the offline WebView2 installer, and the lightweight ZIP includes a download shortcut.

## Vibrational spectroscopy in 0.5.0

**Vibrations (IR and Raman)** uses the selected spatial point group and the coordinates of every atom, including atoms at the symmetry centre. Open or paste a single XYZ frame, enter coordinates manually or load a project. An XYZ frame has an atom count (1–120), a comment line that may be blank, then one element symbol and three coordinates in Å per atom. D and T are distinct isotope labels.

Browse the structure catalog by name or enter a formula in Vibrational spectroscopy. Try `C4H8` for cis- and trans-2-butene, isobutene and cyclobutane, or `Pt(NH3)2Cl2` for cisplatin and transplatin. Enter `[Fe(CN)6]4-` for hexacyanoferrate(II), or omit the charge to see both Fe(II) and Fe(III). Inspect and confirm the geometry before calculating IR and Raman selection rules. All coordinates are included for offline use on Android and desktop.

Seventeen new organic models use NIST CCCBDB reference coordinates reoriented and symmetrized to remove rounding residuals. The α/β-D-glucose anomers and D/L-alanine enantiomers use PubChem computed conformers. Other additions use idealized geometries with explicit ligand atoms. Ferrocene includes eclipsed and staggered ring orientations. The original tetrahedral carbon and silicon substitution models remain available by formula. Project JSON stores the selected model, its charge where applicable and the full coordinates used in the calculation. [NIST CCCBDB](https://cccbdb.nist.gov/exp2x.asp?casno=74840&charge=0) · [PubChem](https://pubchem.ncbi.nlm.nih.gov/compound/79025)

Rotate the preview and compare atom IDs with the coordinate table. Select A, B and C to measure A–B and the angle at B. Gray connections in an XYZ preview are distance estimates using covalent radii. Green lines join atoms selected for measurement. Confirmation checks that every operation gives a bijection between atoms of the same type and reports the largest mapping deviation. XYZ inputs default to the atomic centroid as the symmetry origin and preserve the file axes and raw coordinates. Check the axis convention for the group and, if needed, orient coordinates in a molecular editor before import. Editing the structure, group, origin or tolerance requires a new confirmation. [XYZ format](https://openbabel.org/docs/FileFormats/XYZ_cartesian_coordinates_format.html) · [Covalent radii](https://doi.org/10.1039/B801115J)

Once confirmed, choose **Calculate vibrations and activity**. For each operation, the Cartesian displacement character is the number of fixed atoms times the trace of its spatial matrix. Removing translations and rotations leaves 3N−6 vibrational degrees of freedom for a nonlinear molecule, 3N−5 for a linear molecule and zero for a single atom. Electric-dipole IR activity follows the vector representation. Raman activity follows the six components of the symmetric polarizability tensor.

Each degenerate multiplet counts as one fundamental, with complex conjugate rows paired for real displacements. When a finite subgroup is selected, its symmetry determines the degeneracies and counts. Frequencies require masses and force constants. Intensities also require dipole or polarizability derivatives. Load the methane (Td) or carbon dioxide (D4h) vibration example to try the calculation. Methane has nine vibrational degrees of freedom and four fundamentals, A1 + E + 2T2. Two are IR allowed and all four are Raman allowed. The symmetry assignments agree with the experimental compilation. [NIST methane data](https://cccbdb.nist.gov/exp2x.asp?casno=74828)

For water in the xz plane, each of the two A₁ vibrations allows z-polarized IR absorption and three independent Raman tensor entries xx, yy and zz. The B₁ vibration allows x and xz. For CO₂ along z, the A₁g entry “xx + yy, zz” means that xx and yy are equal and zz is independent. Each off-diagonal label stands for a pair of equal matrix entries. Copied results preserve these combinations. Each row in the exported JSON `spectrum.activities` contains unit dipole directions in `irDirections` and symmetric matrices with unit Frobenius norm in `ramanTensors`. [Calculation and acceptance examples (Chinese)](SPECTROSCOPY_DESIGN.md)
