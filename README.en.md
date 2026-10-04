# Point Group Reducer

[简体中文](README.md) · [繁體中文](README.zh-Hant.md)

Enter the character vector **c** to calculate irrep multiplicities **a** and the representation decomposition:

$$\mathbf a=\frac1h X^*W\mathbf c$$

X contains complete complex irrep characters as rows, W contains conjugacy-class sizes on its diagonal, and h is the group order. Enter one character per class in the displayed column order; do not multiply by class size.

## Download and launch

Download a ZIP from this repository's Releases page and extract it completely. No Python or LaTeX installation is required.

| System | Package suffix | GUI launcher |
|---|---|---|
| Windows 64-bit | Windows-x64.zip | PointGroupReducer/PointGroupReducer.exe |
| Apple Silicon Mac | macOS-arm64.zip | PointGroupReducer.app |

Keep Windows `_internal` folders beside their executables. On macOS, `Start-CLI.command` starts the CLI. These apps are not developer signed or Apple notarized.

## Mathematical notation and languages

The application typesets point-group names, operation headings, character values, irrep labels and formulas offline, including radicals, fractions, imaginary i, π and angles. Cells follow rendered image dimensions, with centered symbols and sufficient margins. The class-size row and upper-left irrep heading are omitted. Results and copied text show decomposition, characters, multiplicities and dimension without the reconstruction-error footer.

Use the top-right selector or Language menu to choose **English / 简体中文 / 繁體中文**. Buttons, instructions, errors and the guide update together. Switching keeps your group, input values, pasted vector and result. Your language choice is remembered.

The result page has **Copy text** and **Copy LaTeX**. LaTeX includes the reduction formula, c/a vectors and the decomposition when the characters form a valid representation. JSON identifiers and fields remain language independent.

## Workflow and navigation

Select group → enter c → view result. The five d-orbital example only fills values; click Calculate afterwards. Errors identify the relevant class.

| Action | GUI | CLI |
|---|---|---|
| Back | Back / Esc | `0` |
| Home | Home; Windows Ctrl+Home / Mac Command+Shift+H | `home` |
| Exit | Exit; Windows Ctrl+Q / Mac Command+Q | `q` |
| Single numeric zero | `0` | `=0` |

Back and Home keep your input. Changing groups clears it. A zero within a comma-separated vector needs no prefix. CLI language flags: `--lang en`, `--lang zh-Hans`, `--lang zh-Hant`; use `lang` during an interactive step to switch without losing state.

## Scope

The searchable selector offers **423 groups**: Cn/Cnv/Cnh and Dn/Dnh/Dnd for n=2…60, even S4…S120, C1/Cs/Ci and seven polyhedral groups. Type a name to filter. Higher orders remain available by manual entry and Enter.

Class headings directly name rotations, mirrors or inversion. For example, C2v uses E, C2, σᵥ(xz), σᵥ(yz). For axial groups, the principal rotation axis defaults to z, including C3 and higher orders. The xy plane is horizontal; xz and yz are vertical. Other mirrors and perpendicular twofold axes use an exact azimuth φ measured from +x toward +y. For polyhedral groups, one highest-order rotation axis may be chosen as z; equivalent axes in a class need not be parallel to z. Renaming preserves column order and character data.

Finite ordinary 3D point groups: C1, Cs, Ci; Cn, Cnv, Cnh; Dn, Dnh, Dnd; S2n; T, Th, Td, O, Oh, I, Ih. Families are generated on demand with n ≤ 2000; large dense matrices require substantial memory.

Complex characters, nonnegative integer multiplicity checks, central d-shell examples, JSON and CSV are supported. E+ / E− are each one-dimensional complex conjugate irreps, not separate two-dimensional E irreps. Labels and class order may differ from textbooks. Infinite C∞v / D∞h, double groups, magnetic groups and space groups are excluded.

## Run from source

Python 3.10+ with Tkinter:

```bash
python -m pip install -r requirements.txt
python pointgroup.py --gui --lang en
python pointgroup.py C2v --c "5,1,1,1" --lang en
python pointgroup.py --lang en
python -m unittest -v
```

Inputs may use `1/2`, `sqrt(5)`, `1+2i`, `exp(2*pi*i/3)` and other permitted numeric expressions.

## Build and validation

On native Windows or macOS, using Python 3.12:

```bash
python -m pip install -r requirements-build.txt
python packaging/build_native.py
```

The builder runs 51 source tests and real Tk checks of formula images, all languages, preserved drafts, clipboard operations and export. It also checks the frozen GUI and CLI before packaging ZIPs with SHA-256 checksums and build metadata. The release workflow supports Windows x64 and Apple Silicon macOS and publishes only after both pass. A main-branch commit marked `[release]`, a VERSION-matching tag or a manual publish run triggers publication. Release assets contain two ZIPs and one SHA256SUMS.txt. See Actions and BUILD-INFO.json for build results.
