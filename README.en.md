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
| Intel Mac | macOS-x64.zip | PointGroupReducer.app |

Keep Windows `_internal` folders beside their executables. On macOS, `Start-CLI.command` starts the CLI. These apps are not developer signed or Apple notarized. Private repositories require an authorized GitHub login.

## Mathematical notation and languages

v2.3.0 renders point-group names, class headings, irrep labels and formulas with offline MathText, including subscripts, superscripts, primes and complex-irrep signs.

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

The builder runs 29 source tests and real Tk checks of formula images, all languages, preserved drafts, clipboard operations and export. It also checks the frozen GUI and CLI before packaging ZIPs with SHA-256 checksums and build metadata. The release workflow publishes only after all three platforms pass. Automated checks do not replace manual Windows/macOS click acceptance; see Actions and BUILD-INFO.json.
