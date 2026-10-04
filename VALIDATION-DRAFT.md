# Operation-name draft validation — 2026-10-03

Status: unpublished source draft based on v2.4.1. VERSION remains 2.4.1.

- 50 source unit tests passed, including 7 new operation-name checks.
- Independently reconstructed matrices match the displayed operations for 206 axial point-group instances (C1/Cs/Ci and seven families for n=2..30).
- Character values, class order, class sizes, h, W, irreps and symbolic character formulas remain unchanged.
- MathText parses generated operation names; exact azimuths use pi fractions.
- English, Simplified Chinese and Traditional Chinese explain the z-axis and azimuth convention.
- Supplied d-shell examples have been regenerated with the current class names.
- Native GUI smoke coverage includes direct C2v mirror labels, D4d mirror azimuths and S6 operation powers.
- Native Windows/macOS builds and manual window inspection have not run for this draft. The current session has no desktop display.

No release tag, release asset, main-branch update or publish workflow is requested for this draft.

## Preview 2: mathematical table geometry

The GUI now draws a measured fixed header and mathematical cells on synchronized canvases, rather than relying on platform Treeview heading sizing. Header height and row height include 12 px of clearance on each side of the tallest rendered expression. Numbers use MathText via exact SymPy LaTeX, including radicals, fractions, complex components and trigonometric angles. Only visible cells are drawn. Native checks inspect actual allocated header height, image bounds, center coordinates, synchronized horizontal scrolling, vertical scrolling, navigation and resizing. Native screenshots are included as QA artifacts. This remains a test build; no main merge or Release is authorized.
