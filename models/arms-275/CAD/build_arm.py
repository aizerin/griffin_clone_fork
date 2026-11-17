"""Replacement arms for the existing 195 mm Giffin Grip prototype.
Derived adaptation of Giffin Grip Clone by vpxr; CC BY-NC 4.0.
Measured wheel diameter 275 mm. Arm shortened by 50 mm in total.
Use the middle and outer pairs of existing M4 base holes.
"""
from pathlib import Path
import json,math
import cadquery as cq
import numpy as np
import trimesh

ROOT=Path(__file__).resolve().parent.parent
WHEEL_DIAMETER=275.0
SIDE_PAD=2.0
ARM_INNER=51.7
WIDTH=28.0
THICKNESS=6.5
RIM_DROP=10.0
LANE_OFFSET=5.199987122349466
SLOT_CENTER=81.5754
SLOT_LENGTH=52.0
NUT_CHANNEL_LENGTH=54.2
R=WHEEL_DIAMETER/2+SIDE_PAD
ARM_OUTER=R+5.5

def create_arm():
 a=cq.Workplane('XY').center((ARM_INNER+ARM_OUTER)/2,0).rect(ARM_OUTER-ARM_INNER,WIDTH).extrude(THICKNESS)
 a=a.edges('|Z').fillet(2)
 nose=cq.Workplane('XY').workplane(offset=-RIM_DROP).center((R-1+ARM_OUTER)/2,0).rect(ARM_OUTER-R+1,WIDTH).extrude(RIM_DROP+.1)
 nose=nose.cut(cq.Workplane('XY').workplane(offset=-RIM_DROP-1).circle(R).extrude(RIM_DROP+2))
 a=a.union(nose)
 # Same transverse lanes and fasteners; centered travel on the middle/outer hole pairs.
 for y in [-LANE_OFFSET,LANE_OFFSET]:
  a=a.cut(cq.Workplane('XY').workplane(offset=-.1).center(SLOT_CENTER,y).slot2D(SLOT_LENGTH,4.4).extrude(6.8))
  a=a.cut(cq.Workplane('XY').workplane(offset=-.1).center(SLOT_CENTER,y).slot2D(NUT_CHANNEL_LENGTH,7.25).extrude(4.3))
 return a.clean()

def mesh_from_cq(s):
 if isinstance(s,cq.Workplane):s=s.val()
 v,f=s.tessellate(.02,.08)
 return trimesh.Trimesh(np.array([p.toTuple() for p in v]),np.array(f),process=True)

if __name__=='__main__':
 for d in ['STL','STEP','verification']:(ROOT/d).mkdir(exist_ok=True)
 arm=create_arm()
 assert arm.val().isValid() and len(arm.solids().vals())==1
 cq.exporters.export(arm,str(ROOT/'STEP/06_adjustable_arm_275mm_v2.step'))
 m=mesh_from_cq(arm)
 m.export(ROOT/'verification/arm_assembly_coordinates.ply')
 # The same physical arm works for both CW and CCW; it is symmetric across Y=0.
 m.apply_transform(trimesh.transformations.rotation_matrix(math.pi,[1,0,0]))
 m.apply_translation([-m.bounds.mean(0)[0],-m.bounds.mean(0)[1],-m.bounds[0,2]])
 assert m.is_watertight and m.volume>0 and len(m.split())==1
 m.export(ROOT/'STL/06_adjustable_arm_275mm_v2.stl')
 report={'wheel_diameter_mm':WHEEL_DIAMETER,'silicone_pad_thickness_mm':SIDE_PAD,'plastic_contact_radius_mm':R,'rim_drop_mm':RIM_DROP,'previous_arm_length_mm':143.3,'new_arm_length_mm':ARM_OUTER-ARM_INNER,'shortened_by_mm':143.3-(ARM_OUTER-ARM_INNER),'dimensions_mm':m.extents.tolist(),'volume_mm3':float(m.volume),'watertight':bool(m.is_watertight),'components':1,'step_valid':True,'mount_lane_offset_mm':LANE_OFFSET,'bolt_rows':'middle and outer; innermost unused','slot_center_radius_mm':SLOT_CENTER,'slot_length_mm':SLOT_LENGTH,'nut_channel_length_mm':NUT_CHANNEL_LENGTH,'intended_radial_adjustment_mm':[-12,12]}
 (ROOT/'verification/geometry_report.json').write_text(json.dumps(report,indent=2))
 print(json.dumps(report,indent=2),flush=True)
