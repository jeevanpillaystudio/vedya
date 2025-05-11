# Vedya Design System

A generative design system for creating and fabricating mandala-like patterns and modular structures.

## Overview

**Project:** Mandala Sculpture for Australia Bush Festival  
**Materials:** Wood (Huon Pine), Modelling Paste, 3D Print Materials, CNC Router Materials  
**Dimensions:** Full Installation 2m x 2m; Prototypes vary in size

![Vedya Prototype](public/lidar-scans/vedya-prototype-wood.blend)

## Algorithm & Design Approach

The Vedya system uses a hierarchical composition-based algorithm to generate complex geometric designs:

### Core Algorithm

```
FUNCTION GenerateVedyaDesign(designType, seed, fabricationType, fabricationMode):
    // Initialize design context
    context = CreateDesignContext(designType, seed, fabricationType, fabricationMode)
    
    // Generate base geometry based on selected design template
    IF designTemplate == "shire":
        component = GenerateShireDesign(context.rootComponent)
    ELSE IF designTemplate == "umss":
        component = GenerateUMSSDesign(context.rootComponent)
    ELSE IF designTemplate == "parthenon":
        component = GenerateParthenonDesign(context.rootComponent)
    
    // Apply post-processing based on fabrication mode
    IF fabricationMode == "slicer":
        SliceComponent(component, layerDepth, layerCount)
    ELSE IF fabricationMode == "aggregator":
        AggregateComponents(component)
    
    RETURN component
```

### Composition System

The design generation uses a composition-based approach:

1. **Primitive Shapes**: Basic geometric elements (circles, rectangles)
2. **Modifiers**: Operations applied to shapes (extrude, boolean, array)
3. **Composition Layers**: Collections of shapes with modifiers
4. **Full Composition**: Hierarchical arrangement of layers

Example of the Shire design generation:

```
FUNCTION GenerateShireDesign(rootComponent):
    // Create background layer
    background = CreateBackgroundLayer(rootComponent)
    
    // Create border
    border = CreateBorder(rootComponent)
    
    // Create seed of life patterns (layered)
    seedOfLifeLayer0 = CreateSeedOfLifeLayer0(rootComponent)
    seedOfLifeLayer1 = CreateSeedOfLifeLayer1(rootComponent)
    seedOfLifeLayer2 = CreateSeedOfLifeLayer2(rootComponent)
    
    // Create core component
    core = CreateComponentCore(rootComponent)
    
    // Create torus astroid pattern
    torusAstroid = CreateTorusAstroid(rootComponent)
    
    // Apply middle cut
    ApplyMiddleCut(rootComponent)
    
    // Apply terrain cut (optional)
    ApplyTerrainCut(rootComponent)
    
    RETURN rootComponent
```

### Geometric Operations

The system uses several key geometric operations:

1. **Boolean Operations**: Union, difference, and intersection of shapes
2. **Array Patterns**: Radial, linear, and grid arrangements of elements
3. **Extrusion**: Converting 2D sketches to 3D forms
4. **Coordinate Transformations**: Mapping between coordinate systems (cartesian, cylindrical, spherical)

## Architecture

The Vedya system follows a pattern → transform → render workflow:
- **Pattern:** Generate base geometric patterns
- **Transform:** Apply coordinate transformations (cartesian, cylindrical, spherical)
- **Render:** Output to various formats (STL, OBJ, PNG)

## Setup & Installation

### Fusion 360 Integration

1. Configure environment:
   ```
   # In .env file
   PYTHONPATH=/path/to/fusion360/API/Python/libs
   LOGFILEPATH=/path/to/logfile.txt
   ```

2. Run the script:
   - Open Fusion 360
   - Open the script in Script Editor
   - Run the script

### Python Development

1. Setup environment:
   ```
   poetry shell
   poetry install
   ```

2. Available commands:
   ```
   # Transform coordinates
   vedya transform input.txt --target cylinder --resolution 0.1 --length 10 --height 4 --radius 1 --output output.txt
   
   # Render output
   vedya render output.txt --output output.stl --color grayscale
   
   # Run examples
   vedya example output_path
   ```

## Fabrication Methods

### 3D Printing
- **Printers:** Bambu Labs X1C/P1S (256mm³ build volume)
- **Materials:** PLA, PETG, TPU, ABS, ASA, PVA, PET
- **Examples:**
  - [Print 1 with Kailash Terrain](public/3d-printer-prototypes/print-1/3d-vedya-print-with-kailash-0.75;1;8.mp4)
  - [Print 2 Standard](public/3d-printer-prototypes/print-2/3d-vedya-print-1;1;8.mp4)

### CNC Milling
- Used for wood components (Huon Pine)
- [Laser Prototype Slice](public/laser-prototypes/vedya-laser-1/slice-body-8/slice-body-8.stl)

### Terrain Models
- [Low Resolution Kailash](public/low-res-kailash/low-res-kailash.stl)
- [Medium Resolution Kailash](public/mid-res-kailash/mid-res-kailash.stl)

## Project Components

### Shire
Mandala design for Australia Bush Festival, collaboration between Jeevan Pillay and Adam Brown, Gemma & team at Tasmania.
- Implementation: [Shire Design](src/core/fabrication/design/shire/index.py)

### UMSS
Universal Modular Storage System with magnetic connections
- Implementation: [UMSS Design](src/core/fabrication/design/umss/index.py)
- Specifications: [Magnet Fitting Details](public/README.md)

### Parthenon
Generative architectural model
- Implementation: [Parthenon Design](src/core/fabrication/design/parthenon/index.py)

## Documentation

Additional documentation available in subdirectories:
- [Core Library Documentation](src/lib/README.md)
- [3D Printer Prototyping](public/README.md)
- [Print 1 Notes](public/3d-printer-prototypes/print-1/README.md)
- [Print 2 Notes](public/3d-printer-prototypes/print-2/README.md)

## Troubleshooting

- [Fixing VSCode x Python Code Hints](https://forums.autodesk.com/t5/fusion-api-and-scripts/code-hints-in-visual-studio-code-howto/td-p/9151250)
- [BambuStudio Filament Process](public/3d-printer-prototypes/README.md)
