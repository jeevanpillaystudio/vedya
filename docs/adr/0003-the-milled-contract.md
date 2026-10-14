# 0003: Shire reproduces the model that was milled

Status: accepted, October 2026; amended October 2026, when layer 0 came to be cut to the board by default.

## Context

"Port Shire one to one" has three readings, and they give different solids:

- What the code at HEAD builds: Shire does not import there.
- What the code evidently intends: a hole through the centre, and a terrain ("kailash") band cut into the core.
- What the code built in April 2024 (`57f2b02`, tag `fusion/milled`), when the piece was milled from it. `a36cc3c` (tag `fusion/shire-last`) builds the same geometry.

What the code built turns on Fusion behaviours the script never states. Autodesk's documentation and staff say that a Cut, Intersect or Join extrude with no participants named acts on every visible body it intersects, in any component. The documentation does not say which side of an outline a Side1 thin wall grows to.

The two April toolpaths, `public/cnc-cuts/6mm-adaptive.tap` and `3mm-adaptive.tap`, are the only record of the model that was milled. They were generated within a day of the April script, for flat end mills of 6 and 3 mm. Their z = 0 is the design's top, 38.4 mm up, and both tools' depths land on the design's levels: the 6 mm tool's deepest cut, −19.2 mm, is the top of the core's base, and the 3 mm tool's, −28.68 mm, is 0.12 mm above the board's top. They measure:

| Question | What the toolpaths show |
| --- | --- |
| Was the centre bored through? | Within 90 mm of the centre the deepest cut is 4.8 mm, to 33.6 mm, the top of the core's highest astroid; elsewhere the board is cut 28.68 mm deep. There was no hole of radius 57.6 mm. |
| Was the kailash band cut? | Inside the 40,166 mm² band the April script's cut picks, 11,302 positions of the 6 mm tool and 436 of the 3 mm tool, none deeper than 14.4 mm, to 24.0 mm. The band was not cut to its 16.8 mm floor. |
| Which side is a Side1 wall? | Along the middle and inner diamonds, tool centres below the wall's top stop 10.2 mm (6 mm tool) and 8.7 mm (3 mm tool) inside the outline, and 3 and 1.5 mm outside it: a 7.2 mm wall inside the outline. Side1 is the inside. |
| Is there a wall along the board's inside edge? | Both tools cut 2 to 22 mm deep within 19.2 mm of the board's edge, all along both axes, up to a boundary 12.8 mm inside the edge. The milled model had no border wall inside the outline. |

The photograph, `public/final-piece.jpeg`, agrees: a plateau at the centre with only a small point, and no flat-bottomed band inside the middle diamond.

Fusion's documented reach contradicts the first two rows: the middle cut would have bored the centre, and the kailash cut would have cut its band. The port's first reading confined every feature to its own component and the components inside it. The toolpath test (below) disproved it. A seed-of-life layer is one top-level component, with a component per pass and, inside that, one per depth step. With each step's cuts confined to its own component, the two passes' slabs stay whole where they overlap in height, and the model stands 1.2 to 2.4 mm above about 70,000 positions of each tool. With each Cut and Intersect reaching across the layer's top-level component, a later pass trims the earlier pass's slabs to its own heights, and no tool position cuts into the model; April still equals August, and there is still no centre hole or kailash band (commits `cc13aa0` and `d87ef6d`).

## Decision

Shire reproduces the milled model. The stand-in (ADR 0002) runs the 2024 script under these behaviours, and the new design builds what it gives:

- A Cut or Intersect reaches every body it overlaps in its top-level component: its own component and every component nested in it. A Join reaches only its own component's bodies, and makes a new body where it reaches none. A Cut or Intersect that reaches nothing raises Fusion's "No target body found to cut or intersect!".
- A Side1 thin wall grows inside its outline (`Align.INSIDE`), as the toolpaths show for the diamonds and forum reports for circles. Side2 grows outside (`Align.OUTSIDE`), as UMSS's milestone-5 volumes show for a circle.
- There is no centre hole. The middle cut, in a top-level component holding only a ring outside its disc, reaches nothing; the script catches the error, and the ring stands.
- There is no kailash band. In April its cut, from a top-level component of its own, reaches nothing; by August its call raises a `TypeError` before it runs. The in-bounds intersect never runs either, and the outer diagonal steps are commented out. None of them is built.
- The aggregate is the union of every part. April and August give the same one.
- The torus adds no relief. Its region lies inside the core's top astroid, over the same heights, 28.8 to 33.6 mm, so the core already holds all of it; the toolpaths agree, cutting no deeper than 4.8 mm within 90 mm of the centre. It is kept as a part because the design built it.
- Layer 0 overhung the board's long sides by up to 40 mm, from 320 to 360 mm out: the script drew its circle, of radius 360 mm, on a board 640 mm wide, and nothing in the 2024 code trims it. The board could not hold it, and the milling boundary lies inside the board, so the piece shows nothing of it. Shire now cuts layer 0 to the board by default (`ShireParams.clip_to_board`), as layer 2 is cut; `clip_to_board=False` builds the 2024 model exactly, overhang included. The pin is kept on that unclipped build: the goldens and every comparison with the stand-in use it, and the tests hold the default's layer 0 and aggregate to the unclipped ones cut to the board.

The border is the open question. The script draws it as a Side1 wall on the board's outline, 19.2 mm thick, standing on the board from 9.6 to 38.4 mm; under the rule above that is a wall inside the outline, and that is what Shire builds. The milled model had no wall there. Either Fusion put the wall outside the outline, so that it fell outside the milled area, or the border was left out of the model given to CAM. The repository does not record which.

## The toolpath test

`tests/test_toolpaths.py` checks Shire, every part but the border, against both toolpaths, exactly in plan:

- For each height a part's top sits at, the plan of all material standing above it, each face drawn as a polygon within 0.005 mm of its edges.
- Every position the tool passes through below the design's top, at each programmed point and along every move, no two checked points more than 0.25 mm apart.
- At each, the model may stand at most 0.15 mm above the tool's tip, the stock CAM left on floors, and no more than 0.1 mm inside the edge of the tool's flat end. The 0.1 mm is CAM's own contact with walls, 0.070 mm at its deepest, and is an order of magnitude below 1.2 mm, the shallowest step of a seed-of-life layer, the smallest error the test exists to catch.

The border is left out because the toolpaths cut where its wall stands, along the whole edge of the board. Including it would fail on the open question rather than on anything the test can settle. Leaving it out exempts only the border: the parts that reach the board's edge, the core's base and layer 2, are checked there as everywhere else, and the border is still pinned by its golden.

## Consequences

- The stand-in's contract (`tools/legacy/adsk/fusion.py`), the goldens and Shire's `seed_layer` encode this rule. Changing it changes the goldens.
- Shire is not what Autodesk's documentation predicts the code built. A reader who expects a centre hole or a kailash band will not find one, by design.
- Why the cuts stayed in their top-level component, against the documentation, is not known: Fusion behaved so for this code, in Direct design mode, or the model was changed by hand before CAM.

## What would change it

- A record of the model given to CAM, such as a recovered Fusion document or the CAM setup, which would settle the border and the reach.
- A decision to change the design, such as boring the centre or cutting the kailash band. That would be a new design or a new parameter, not a change to this contract.
