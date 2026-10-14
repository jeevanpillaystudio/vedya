# Vedya

Vedya builds geometric reliefs and modular parts for fabrication, as Python functions over build123d. Its first designs are ports of a Fusion 360 script from 2024, held to what that script built. Every length is in millimetres.

## Designs and what they build

**Design**:
A named build: a frozen dataclass of parameters, whose defaults build it as made, and a function from those parameters to a model. A design is registered under the `vedya.designs` entry-point group.
_Avoid_: template, composition, script

**Part**:
One named solid of a design, such as Shire's `core`. In a ported design, a part is what one top-level component of the old script held.
_Avoid_: component, body

**Model**:
A design's parts by name, in the order the design builds them. It fixes which parts it holds, not the parts themselves.
_Avoid_: document, assembly, component tree

**Aggregate**:
The union of a model's parts: the one solid that is milled or printed whole.
_Avoid_: aggregator body, merge

**Slice**:
One of the level pieces an aggregate is cut into from the bottom up, at a fixed height, for laser cutting or printing. The last slice is what is left above the last cut.
_Avoid_: layer (for this sense), split

**Layer** (Shire):
Shire's unit of depth, 4.8 mm. Every height in Shire is a whole number of layers or a fraction of one, up to eight layers, 38.4 mm.
_Avoid_: level, step

## Geometry

**Region**:
Flat faces on the XY plane, made from primitives with 2D booleans: `+`, `-` and `&`. A ported design constructs each region; it never picks one by its area.
_Avoid_: profile, sketch

**Mask**:
The fixed region a seed-of-life layer is carved from, such as the circle of 360 mm less the outer diamond.
_Avoid_: boundary, clip region

**Stroke**:
The band of a given width along a region's outline, on the side its alignment names, with sharp corners.
_Avoid_: thin wall, thin extrude, offset

**Alignment**:
The side of an outline a stroke grows to: `INSIDE`, `OUTSIDE` or `CENTER` (`vedya.geometry.Align`). They are Fusion's Side1, Side2 and Center.
_Avoid_: Side1, Side2 (outside the stand-in)

**Slab**:
A region swept straight up from a height by a thickness. Every solid Vedya builds is a union of slabs.
_Avoid_: extrude, body, prism (outside the stand-in)

**Diamond**:
A square turned 45°, given by its half-diagonal.
_Avoid_: rotated square, angled rectangle, three-point rectangle

**Astroid**:
The four-cusped curve R·(cos³θ, sin³θ), given by R, the distance from its centre to a cusp. It is drawn as the spline through 129 samples, as Fusion fitted it, and so has slightly rounded cusps.
_Avoid_: star, hypocycloid

**Seed of life**:
A ring along a circle and six petal rings of the same radius, each centred on that circle at 60° steps. In Shire the centre ring is stroked inside its circle and the petals astride theirs.
_Avoid_: flower of life, rosette

**Torus rings**:
A ring along a circle of radius r and a number of rings along circles of radius r/2, each centred r/2 out, so that each touches the large circle from inside and passes through the centre. Every ring is stroked inside its circle.
_Avoid_: torus (that is the Shire part built from them)

**Depth step**:
One slab of a stack that gives a pattern relief. A stack's steps have equal heights, and the stroke grows with height (`THICKER_UPWARD`, the old code's Decrement) or shrinks.
_Avoid_: repeat, depth iteration

**Seed-of-life layer**:
A mask carved by seeds of life in passes, each pass a stack of depth steps rising from the same height. Each slab cuts back every earlier slab it overlaps to its own heights. Shire's `layer-0`, `layer-1` and `layer-2` are seed-of-life layers.
_Avoid_: seed layer component, leaf

**Seed pass**:
One pass of a seed-of-life layer: the seeds' radius, the stroke added at each step, the pass's height, and its number of steps (`SeedPass`).
_Avoid_: ring set

## The pin

**Golden**:
The fingerprints of every part of a ported design, and of its aggregate where the old script made one, measured by running the 2024 script on the stand-in. Each is a file in `tests/golden/`, which records the commit it was run from.
_Avoid_: snapshot, fixture, expected values

**Fingerprint**:
A shape's volume, area, bounding box and centroid: the numbers compared against a golden.
_Avoid_: hash, signature

**Stand-in**:
`tools/legacy/adsk/`: the members of Fusion 360's `adsk` API the 2024 scripts call, built on build123d, in centimetres, so that those scripts run unchanged from git history. It holds every body as a stack.
_Avoid_: mock, fake, emulator, shim

**Stack**:
A solid made of prisms along z, held as bands: from one height to the next, one region. The stand-in works its booleans out on stacks, band by band, in the plane.
_Avoid_: mesh, voxel

**Reach**:
Which bodies a Fusion Cut, Intersect or Join extrude acts on when the script names none. In the milled contract, a Cut or Intersect reaches every body it overlaps in its top-level component; a Join reaches only its own component.
_Avoid_: participants, scope

**Milled contract**:
What the port reproduces: the model the April 2024 script put into the piece that was milled, as its toolpaths record it. ADR 0003 states it.
_Avoid_: intended design, HEAD behaviour

**Toolpaths**:
The two G-code files in `public/cnc-cuts/`, from which the piece was milled in April 2024. They are the outside record Shire is checked against.
_Avoid_: CAM output, G-code (as the name of the record)
