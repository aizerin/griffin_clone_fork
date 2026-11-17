"""Removable open-reticle centering insert for the delivered 15.6 mm base bore.
Coordinates here are assembled: the wheel top is Z=0, base underside Z=6.5,
and its continuous central-bore lip is Z=16.5. No upper cover is fitted.
"""
from pathlib import Path
import json
import numpy as np
import trimesh
import cadquery as cq
ROOT=Path(__file__).resolve().parent.parent
BORE_DIAMETER=15.6
BORE_LIP_Z=16.5
BOTTOM_Z=2.5
APERTURE_DIAMETER=12.6
CROSS_WIDTH=.6
CROSS_THICKNESS=.6
CENTER_HOLE=1.2
CENTER_RING_OUTER=2.4
# Outer radius versus height. The shallow taper meets the nominal bore edge
# at exactly (R=7.8, Z=16.5); a 45-degree upper flare prints without support.
PROFILE=[(7.1,2.5),(7.4,2.8),(7.4,12.5),(8.1,19.5),(8.1,20.5),(12.,24.4),(12.,25.6)]

def mesh_from_cq(obj):
 s=obj.val() if isinstance(obj,cq.Workplane) else obj
 v,f=s.tessellate(.01,.055)
 return trimesh.Trimesh(np.array([p.toTuple() for p in v]),np.array(f),process=True)

def build():
 inner=APERTURE_DIAMETER/2
 polygon=[(inner,BOTTOM_Z)]+PROFILE+[(inner,PROFILE[-1][1])]
 body=cq.Workplane('XZ').polyline(polygon).close().revolve(360,(0,0),(0,1))
 # Both 0.6-mm cross arms and center ring are connected to the wall on bed.
 for width,height in [(APERTURE_DIAMETER+.4,CROSS_WIDTH),(CROSS_WIDTH,APERTURE_DIAMETER+.4)]:
  rib=cq.Workplane('XY').workplane(offset=BOTTOM_Z).rect(width,height).extrude(CROSS_THICKNESS)
  body=body.union(rib)
 ring=cq.Workplane('XY').workplane(offset=BOTTOM_Z).circle(CENTER_RING_OUTER/2).extrude(CROSS_THICKNESS)
 body=body.union(ring)
 hole=cq.Workplane('XY').workplane(offset=BOTTOM_Z-.1).circle(CENTER_HOLE/2).extrude(CROSS_THICKNESS+.2)
 return body.cut(hole).clean()

if __name__=='__main__':
 for d in ['STL','STEP','verification']:(ROOT/d).mkdir(exist_ok=True)
 obj=build();s=obj.val();assert s.isValid() and len(s.Solids())==1
 cq.exporters.export(obj,str(ROOT/'STEP/01_centering_reticle.step'))
 m=mesh_from_cq(obj);assert m.is_watertight and m.volume>0 and len(m.split())==1
 m.export(ROOT/'verification/reticle_assembly_coordinates.ply')
 m.apply_translation([0,0,-BOTTOM_Z])
 m.export(ROOT/'STL/01_centering_reticle.stl')
 report={'base_bore_diameter_mm':BORE_DIAMETER,'base_bore_lip_height_above_wheel_mm':BORE_LIP_Z,'nominal_bottom_clearance_above_wheel_mm':BOTTOM_Z,'reticle_width_mm':CROSS_WIDTH,'reticle_thickness_mm':CROSS_THICKNESS,'center_sight_hole_mm':CENTER_HOLE,'clear_aperture_mm':APERTURE_DIAMETER,'printed_dimensions_mm':m.extents.tolist(),'volume_mm3':float(m.volume),'watertight':bool(m.is_watertight),'components':1,'step_valid':True,'print_orientation':'reticle on bed; no support; no scaling','contact':'shallow cone at the top edge of the central bore','limitation':'Nominal CAD fit only; printed fit and centering accuracy not yet measured.'}
 (ROOT/'verification/geometry_report.json').write_text(json.dumps(report,indent=2))
 print(json.dumps(report,indent=2),flush=True)
