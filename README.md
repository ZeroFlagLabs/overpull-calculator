# Overpull Calculator

ZeroFlagLabs | Windows desktop application | v2.0.0

Estimates the allowable axial overpull of a uniform annular cross-section. Version 2.0.0 modernises the original v1.0/v1.1 interface without changing its calculation engine.

## Download

Download the [latest Windows portable ZIP](https://github.com/ZeroFlagLabs/overpull-calculator/releases/latest), extract the single unsigned EXE and run it. Verify the ZIP SHA-256 in the release notes. No installer or separate Python runtime required.

## Calculation

Force (lbf) = yield strength (psi) × design factor × π/4 × (minimum OD² − maximum ID²), with diameters in inches. Design factor is the allowable fraction of yield (greater than zero, up to one); a decimal or fraction is accepted. ID = 0 represents solid material. Results round to the nearest whole lbf using the original Python rounding method.

The model assumes uniform axial stress in a concentric section. It does not account for stress concentrations, threads, other load combinations or code compliance. Use appropriate engineering judgement.

Reset restores startup defaults. Settings provides assumptions, optional stable release checks and application information. Updates are not downloaded or installed automatically.

## Development and licences

See [development](docs/DEVELOPMENT.md), [third-party notices](docs/THIRD_PARTY_NOTICES.md) and [LGPL rebuild instructions](docs/ONEFILE_REBUILD_AND_LGPL.md). Original application code is MIT licensed.
