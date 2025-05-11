# API Vedya Draw

A Fusion 360 add-in for generating parametric and direct designs using the Vedya design system.

## Overview

This add-in provides tools for creating generative designs within Fusion 360, with a focus on:
- Mandala-like patterns
- Modular storage systems (UMSS)
- Architectural models (Parthenon)

## Installation

1. Clone this repository to your local machine
2. In Fusion 360, go to **Scripts and Add-Ins** (Shift+S)
3. Click the green "+" icon next to "My Scripts"
4. Navigate to the cloned repository and select the `src` folder
5. Click "Run" to execute the script

## Configuration

### VSCode Setup

1. Install recommended extensions:
   - ms-python.black-formatter
   - ms-python.vscode-pylance

2. Configure Python paths in `.vscode/settings.json`:
   ```json
   "python.autoComplete.extraPaths": [
       "/path/to/Autodesk/Autodesk Fusion 360/API/Python/defs"
   ],
   "python.analysis.extraPaths": [
       "/path/to/Autodesk/Autodesk Fusion 360/API/Python/defs"
   ]
   ```

3. Set up debugging in `.vscode/launch.json`

## Project Structure

- `APIDrawVedya.py` - Main entry point for the Fusion 360 add-in
- `APIDrawVedya.manifest` - Add-in manifest file
- `__main__.py` - Standalone execution entry point
- `/core` - Core functionality
  - `/context.py` - Fusion 360 design context
  - `/types.py` - Type definitions
  - `/utils.py` - Utility functions
  - `/geometry` - Geometric primitives and operations
  - `/fabrication` - Fabrication-specific code
    - `/design` - Design templates
      - `/umss` - Universal Modular Storage System
      - `/parthenon` - Parthenon architectural model
      - `/shire` - Shire festival installation
- `/lib` - Standalone Python library for coordinate transformations and rendering

## Usage

The add-in creates designs based on the selected fabrication type and mode:

```python
# Example from APIDrawVedya.py
context = FusionDesignContext(
    app_context=adsk.core.Application.get(),
    design_type=DesignType.DIRECT,
    seed=create_seed(),
    fabrication_type=FabricationType.CNC_MILL,
    fabrication_mode=FabricationMode.NORMAL,
)

# Generate the design
start_func(root_component)
```

## Fabrication Types

- `CNC_MILL` - For CNC milling operations
- `PRINT_3D` - For 3D printing
- `LASER_CUT` - For laser cutting

## Fabrication Modes

- `NORMAL` - Standard design generation
- `SLICER` - Generates sliced layers for fabrication
- `AGGREGATOR` - Combines multiple components

## Examples

### UMSS (Universal Modular Storage System)

The UMSS is a modular storage system designed for 3D printing:
- Based on 128mm x 128mm tiles
- Uses CA007 (6x3mm) and CA008 (8x3mm) magnets
- Includes female/male tile pairs

See [UMSS Design](./core/fabrication/design/umss/index.py) for implementation details.

### Shire Festival Installation

A mandala-like design for the Shire festival in Victoria, Melbourne:
- Collaboration with Adam Brown, Gemma & team in Tasmania
- Uses Huon Pine wood
- Generated using a specific seed for consistency

See [Shire Design](./core/fabrication/design/shire/index.py) for implementation details.

## Library Tools

The `lib` directory contains standalone Python tools for:
- Coordinate transformations (cartesian, cylindrical, spherical)
- Rendering outputs to various formats
- Example generators

See [Library Documentation](./lib/README.md) for more details.

## Troubleshooting

1. [Fixing VSCode x Python Code Hints](https://forums.autodesk.com/t5/fusion-api-and-scripts/code-hints-in-visual-studio-code-howto/td-p/9151250)
2. If you encounter errors with Python paths, ensure your `.vscode/settings.json` points to the correct Fusion 360 API location
3. For logging issues, check the `logfile.txt` in the add-in directory

## Resources

- [Fusion 360 API Documentation](https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-7B5A90C8-E94C-48DA-B16B-430729B734DC)
- [Python API Reference](https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-9BAACC99-6666-4210-9F52-36D6A3275E5B)
- [3D Printing Prototypes](../public/README.md)
