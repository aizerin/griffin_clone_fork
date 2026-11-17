# Derived from Giffin Grip Clone by vpxr, CC BY-NC 4.0. See the repository README and LICENSE.txt.
from pathlib import Path
import json, math, shutil
import numpy as np
import trimesh
import cadquery as cq

ROOT=Path(__file__).resolve().parent.parent
SRC=ROOT.parents[1]/'upstream/source'
OUT=ROOT
S=195.0/249.0
# CCW viewed from above the wheel. A vertical-plane reflection reverses
# spiral handedness and every matching contact while retaining dimensions.
REFLECT_X=np.diag([-1.,1.,1.,1.])
def export_ccw_step(shape,path):
 path=Path(path)
 cq.exporters.export(shape.mirror("YZ"),str(path.with_stem(path.stem+"_CCW")))

def mesh_from_cq(obj):
 s=obj.val() if isinstance(obj,cq.Workplane) else obj
 v,f=s.tessellate(.02,.08)
 return trimesh.Trimesh(np.array([p.toTuple() for p in v]),np.array(f),process=True)

def circle_fit(p):
 p=np.asarray(p)[:,:2]
 a=np.c_[2*p[:,0],2*p[:,1],np.ones(len(p))];v=np.linalg.lstsq(a,(p*p).sum(1),rcond=None)[0]
 return v[:2],np.sqrt(v[2]+np.dot(v[:2],v[:2]))

def circle_center(m,z):
 loops=m.section(plane_normal=[0,0,1],plane_origin=[0,0,z]).discrete
 fit=[circle_fit(p) for p in loops]
 return max(fit,key=lambda q:q[1])[0]

base=trimesh.load_mesh(SRC/'sggc-basev2.stl')
center=circle_center(base,-5)
loops=base.section(plane_normal=[0,0,1],plane_origin=[0,0,-5]).discrete
holes=np.array([c for c,r in map(circle_fit,loops) if 1.9<r<2.1])
assert len(holes)==18
holes=(holes-center)*S
base.apply_translation([-center[0],-center[1],12.5])
base.apply_scale([S,S,1])
# Restore actual M4 fasteners after shrinking XY: 4.3 bore, 8.3 head recess.
cutters=[]
cutters.append(mesh_from_cq(cq.Workplane('XY').workplane(offset=6.3).circle(7.8).extrude(14)))
for x,y in holes:
 cutters.append(mesh_from_cq(cq.Workplane('XY').workplane(offset=6.3).center(x,y).circle(2.15).extrude(6.5)))
 cutters.append(mesh_from_cq(cq.Workplane('XY').workplane(offset=9.0).center(x,y).circle(4.15).extrude(3.5)))
base=trimesh.boolean.difference([base]+cutters,engine='manifold')
parts={'01_base_192_M4':base}

for src,name in [('sggc-coverv2','02_cover_195'),('sggc-whspacer','03_wheel_spacer'),('sggc-shim','04_axle_shim'),('sggc-sliderv2','05_low_slider')]:
 m=trimesh.load_mesh(SRC/(src+'.stl'))
 # Each source export has slightly different placement. Center concentric parts on their own circles.
 c=center
 if src=='sggc-coverv2':c=circle_center(m,10)
 elif src=='sggc-whspacer':c=circle_center(m,-9)
 elif src=='sggc-shim':c=circle_center(m,-7)
 m.apply_translation([-c[0],-c[1],12.5]);m.apply_scale([S,S,1])
 parts[name]=m

# Replace the source axle with a concentric 15 mm shaft and a groove for a 13 x 2 mm O-ring.
# The source STL groove overlaps its supplied shim. This stack leaves 0.3 mm axial clearance.
old_axle_cut=mesh_from_cq(cq.Workplane('XY').workplane(offset=-1).circle(8.2).extrude(21.5))
cover=trimesh.boolean.difference([parts['02_cover_195'],old_axle_cut],engine='manifold')
axle=cq.Workplane('XY').workplane(offset=.6).circle(7.5).extrude(20.2)
groove=cq.Workplane('XY').workplane(offset=2).circle(8).circle(6.6).extrude(2)
axle=axle.cut(groove).clean()
parts['02_cover_195']=trimesh.boolean.union([cover,mesh_from_cq(axle)],engine='manifold')
export_ccw_step(axle,str(OUT/'STEP/axle_reference_integrated_in_cover.step'))
washer=cq.Workplane('XY').workplane(offset=4.3).circle(11).circle(7.8).extrude(2.2)
parts['04_axle_shim']=mesh_from_cq(washer)
export_ccw_step(washer,str(OUT/'STEP/04_axle_shim.step'))

# Match slider orientation to the actual cover slots and add print clearance in XY.
m=parts['05_low_slider'];cover=parts['02_cover_195']
cn=np.array([.927033,-.374981,0]);sn=np.array([.925642,-.378399,0]);cn/=np.linalg.norm(cn);sn/=np.linalg.norm(sn)
da=math.atan2(cn[1],cn[0])-math.atan2(sn[1],sn[0])
m.apply_transform(trimesh.transformations.rotation_matrix(da,[0,0,1]))
c=m.bounds.mean(0);c[2]=0;m.apply_translation(-c);m.apply_scale([.96,.96,1]);m.apply_translation(c)
def guide_mid(mesh,minarea):
 ids=[i for i in range(len(mesh.facets)) if mesh.facets_area[i]>minarea and abs(mesh.facets_normal[i][2])<.002 and abs(np.dot(mesh.facets_normal[i],cn))>.999]
 return np.mean([cn@mesh.triangles_center[mesh.facets[i]].mean(0) for i in ids])
m.apply_translation(cn*(guide_mid(cover,150)-guide_mid(m,35)))
v=m.vertices.copy();v[v[:,2]>22.0,2]+=.2;m.vertices=v;m.apply_translation([0,0,1])

# Derive mounting angle and slot spacing from the actual STL, not nominal STEP positions.
group=holes[holes[:,0]>40]
v=group.mean(0);theta=math.atan2(v[1],v[0]);u=np.array([math.cos(theta),math.sin(theta)]);w=np.array([-u[1],u[0]])
coords=np.c_[group@u,group@w];lane=float(np.mean(np.abs(coords[:,1])))
print('scale',S,'holes radial/tangential',coords.round(3),'lane',lane,flush=True)

# Support spacer with generous clear passages for 28 mm arms, including 10 mm radial adjustment.
spacer=cq.Workplane('XY').circle(80).circle(75).extrude(6.5)
spacer=spacer.union(cq.Workplane('XY').circle(17).circle(11.5).extrude(6.5))
for i in range(3):
 spoke=cq.Workplane('XY').center(47,0).rect(64,6).extrude(6.5).rotate((0,0,0),(0,0,1),math.degrees(theta)+60+i*120)
 spacer=spacer.union(spoke)
for i in range(3):
 gap=cq.Workplane('XY').workplane(offset=-1).center(62,0).rect(66,29).extrude(9).rotate((0,0,0),(0,0,1),math.degrees(theta)+i*120)
 spacer=spacer.cut(gap)
spacer=spacer.clean()
assert spacer.val().isValid() and len(spacer.solids().vals())==1
parts['03_wheel_spacer']=mesh_from_cq(spacer)
export_ccw_step(spacer,str(OUT/'STEP/03_wheel_spacer.step'))

# New M4 arms: top contacts underside of base at z=6.5, lower face rests on wheel at z=0.
D=355.6;PAD=2.0;R=D/2+PAD;ARM_INNER=42.0;ARM_OUTER=R+5.5;WIDTH=28.0;THICK=6.5;DROP=10.0
arm=cq.Workplane('XY').center((ARM_INNER+ARM_OUTER)/2,0).rect(ARM_OUTER-ARM_INNER,WIDTH).extrude(THICK)
arm=arm.edges('|Z').fillet(2)
nose=cq.Workplane('XY').workplane(offset=-DROP).center((R-1+ARM_OUTER)/2,0).rect(ARM_OUTER-R+1,WIDTH).extrude(DROP+.1)
nose=nose.cut(cq.Workplane('XY').workplane(offset=-DROP-1).circle(R).extrude(DROP+2))
arm=arm.union(nose).clean()
# 3 bolt positions per lane at approximately 57.2, 73.45 and 89.7 mm radius. Check actual nut clearance near slot ends.
for y in [-lane,lane]:
 arm=arm.cut(cq.Workplane('XY').workplane(offset=-.1).center(79,y).slot2D(67,4.4).extrude(6.8))
 # Nuts enter from below; 7.25-mm channel prevents an M4 hex nut from turning.
 arm=arm.cut(cq.Workplane('XY').workplane(offset=-.1).center(79,y).slot2D(69,7.25).extrude(4.3))
arm=arm.clean()
assert arm.val().isValid() and len(arm.solids().vals())==1
export_ccw_step(arm,str(OUT/'STEP/06_adjustable_arm_14in.step'))
# Printable outer end only, for verifying wheel contact height, curvature and splash-pan clearance.
coupon=arm.intersect(cq.Workplane('XY').workplane(offset=-11).center((R-11+ARM_OUTER)/2,0).rect(ARM_OUTER-(R-11)+2,WIDTH+2).extrude(19)).clean()
export_ccw_step(coupon,str(OUT/'STEP/07_rim_fit_coupon.step'))
parts['06_adjustable_arm_14in']=mesh_from_cq(arm)
parts['07_rim_fit_coupon']=mesh_from_cq(coupon)
guide=cq.Workplane('XY').rect(24,32).extrude(3).cut(cq.Workplane('XY').center(0,3).rect(8.3*S,28).extrude(4)).clean()
parts['08_slider_fit_coupon']=mesh_from_cq(guide)
export_ccw_step(guide,str(OUT/'STEP/08_slider_fit_coupon.step'))

# Assembly poses retained for CAD inspection, STL exports below are oriented for printing.
assembly={k:v.copy() for k,v in parts.items()}
phase=math.radians(107)
for key in ['01_base_192_M4','03_wheel_spacer']:
 assembly[key].apply_transform(trimesh.transformations.rotation_matrix(phase,[0,0,1]))
for i in [1,2]:
 a=parts['05_low_slider'].copy();a.apply_transform(trimesh.transformations.rotation_matrix(i*2*math.pi/3,[0,0,1]));assembly[f'slider_{i+1}']=a
for i in range(3):
 a=parts['06_adjustable_arm_14in'].copy();a.apply_transform(trimesh.transformations.rotation_matrix(theta+phase+i*2*math.pi/3,[0,0,1]));assembly[f'arm_{i+1}']=a
assembly.pop('06_adjustable_arm_14in');assembly.pop('07_rim_fit_coupon');assembly.pop('08_slider_fit_coupon')
scene=trimesh.Scene()
for name,m in assembly.items():
 m.apply_transform(REFLECT_X)
 scene.add_geometry(m,node_name=name,geom_name=name)
scene.export(OUT/'verification/assembly_geometry.glb')

# Orient cover top-face down; arm top-face down. Slider laid on a broad side to preserve its guide steps.
for name,m in parts.items():
 if name in ['02_cover_195','06_adjustable_arm_14in','07_rim_fit_coupon']:
  m.apply_transform(trimesh.transformations.rotation_matrix(math.pi,[1,0,0]))
 if name=='05_low_slider':
  # Side orientation produces fewer unsupported islands; use organic supports for this part.
  m.apply_transform(trimesh.geometry.align_vectors(cn,[0,0,-1]))
 m.apply_translation([-m.bounds.mean(0)[0],-m.bounds.mean(0)[1],-m.bounds[0,2]])
 m.apply_transform(REFLECT_X)
 assert m.is_watertight and m.volume>0, name
 m.export(OUT/'STL'/(name+'_CCW.stl'))

report={'handedness':'CCW viewed from above wheel','reflection':'X -> -X; all matching parts','xy_scale':S,'z_scale':1,'nominal_wheel_diameter_mm':D,'nominal_side_pad_mm':PAD,'rim_contact_drop_mm':DROP,'mount_angle_degrees':180-math.degrees(theta),'mount_lane_offset_mm':lane,'mount_holes_mm':(holes*np.array([-1,1])).tolist(),'parts':{n:{'dimensions_mm':m.extents.tolist(),'watertight':bool(m.is_watertight),'components':len(m.split()),'solid_volume_mm3':float(m.volume)} for n,m in parts.items()}}
(OUT/'verification/geometry_report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report['parts'],indent=2),flush=True)
