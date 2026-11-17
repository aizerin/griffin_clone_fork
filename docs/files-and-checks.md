# Files, CAD and checks

Use the [four-plate print list](../README.md#print-the-275-mm-ccw-version) for a fresh 275 mm CCW build. The folders below also preserve the earlier variants; printing every file would produce duplicates.

| Folder | Contents |
|---|---|
| [grip-cw](../models/grip-cw/) | First working geometry set: CW base and matching cover, low slider, spacer, washer, 355.6 mm arms and fit coupons |
| [grip-ccw](../models/grip-ccw/) | Full mirrored geometry and projects; only the spiral base must change on an existing CW grip |
| [arms-275](../models/arms-275/) | Shorter arms, adjusted rim curvature and nut channels; projects for printing one arm or three. Same arm works with either spiral. |
| [centering-reticle](../models/centering-reticle/) | The removable open crosshair for the uncovered base |
| [print](../print/) | Combined small-parts plate for the measured 275 mm wheel, using the short arms and original low sliders |
| [upstream](../upstream/) | Original Printables description, original STEP and the unmodified smaller-version meshes used as CAD inputs |
| [profiles](../profiles/) | Saved PrusaSlicer INDX PETG profiles for the grip/arms and for the reticle; the projects also carry their own settings |

**What the file formats mean:** STL files are individual parts in print orientation, in millimeters. 3MF files include the plate layout and print settings. STEP files are editable solids, generally in assembly coordinates. GLB files under `verification/` show assembly positions; they are not print plates. The axle STEP is a reference: the axle is already part of the printed cover.

**What was changed from upstream:** the complete smaller plate meshes were scaled in XY by 195/249, keeping the track heights. The M4 screw holes and head pockets were restored to full size. The cover axle, retaining groove and washer were revised together; the slider clearances were adjusted for printing. The support spacer and arm slots allow radial adjustment. The original STEP includes sectors rather than complete plates: **there is no modified solid STEP for the complete base or cover**. Use their finished STL/3MF or edit the generator. This fork supplies low jaws; the upstream tall heads and their M3 mounting hardware are not part of this build.

## Optional fit tests

The [fit-test project](../models/grip-cw/3MF/00_Fit_test.3mf) contains three distinct pieces:

- **Rim fit coupon:** only the bent end of the **long, 355.6 mm arm**, to check pad contact and splash-pan clearance. For the 275 mm curvature, use the [one-short-arm project](../models/arms-275/3MF/01_One_arm_275mm_v2.3mf) instead.
- **Slider fit coupon:** a short length of cover slot. Remove supports from the real slider and check that it slides without prying. This does not test engagement with the spiral.
- **Low slider:** a real jaw; keep it for assembly if it fits. The two coupons are not installed.

The archived `03_Arms_sliders_shim` plate in **both** grip folders contains the **long** arms. Use the hardware plate in `print/` for a complete set with short arms.

## Rebuild an edited part

Use Python 3.12 and a virtual environment for the pinned CAD packages. From the repository root, for example:

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python models/arms-275/CAD/build_arm.py
```

The other generators are [CW grip](../models/grip-cw/CAD/build.py), [CCW grip](../models/grip-ccw/CAD/build.py) and [reticle](../models/centering-reticle/CAD/build.py). Run them in a checkout you can modify: they overwrite the corresponding generated outputs. Parameters such as wheel diameter, pad thickness or bore dimensions are in the generator. Alter the contact geometry there rather than scaling an entire STL, which would also change M4 clearances.

**3MF plates do not update when STL files change.** Reload the changed model in PrusaSlicer, preserve the required part orientation/support settings and save a new project. To recreate the published combined hardware plate **from the two existing 3MF projects**, run `python tools/build_275_plate.py`. It keeps the three original sliders and washer in place and substitutes the short arm mesh for each of the three long arms.

## Verification

- [CCW conversion](../models/grip-ccw/verification/ccw_conversion_checks.json): watertight mirrored meshes, volume/dimension agreement and saved projects checked against their STL geometry.
- [Base-only swap](../models/grip-ccw/verification/only_spiral_replacement.json): original cover, sliders and support parts with the reversed base in one assembled pose.
- [275 mm arm compatibility](../models/arms-275/verification/compatibility.json): base/spacer clearance and M4 hardware at five radial positions from −12 to +12 mm. [View the checked assembly](../models/arms-275/verification/assembly_275mm.glb).
- [Reticle fit](../models/centering-reticle/verification/fit_checks.json) and [first three layers](../models/centering-reticle/verification/reticle_toolpath_checks.json): cone seating, open center and all four arms of the crosshair.
- [275 mm hardware plate](../print/verification.json): per-object mesh and support settings checked; final 3MF sliced independently. Each model folder also retains its earlier slicing estimates.

The recorded prototype checks are geometric and slicer checks. They do not certify a load, a maximum speed, the entire jaw travel or the accuracy of a physical print. Test hand movement and rim fit on your own wheel.
