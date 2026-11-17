from pathlib import Path
import importlib.util,math,itertools,json,warnings
import numpy as np,trimesh,cadquery as cq
warnings.filterwarnings('ignore',category=RuntimeWarning)
O=Path('models/arms-275')
spec=importlib.util.spec_from_file_location('arm_build',O/'CAD/build_arm.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
arm=mod.mesh_from_cq(mod.create_arm())
g=trimesh.load_scene('models/grip-ccw/verification/only_spiral_assembly.glb').geometry
base=g['01_base_192_M4'];spacer=g['03_wheel_spacer']
# Recover the actual full-size M4 head-pocket centers from the delivered base.
def circle_fit(p):
 p=p[:,:2];v=np.linalg.lstsq(np.c_[2*p[:,0],2*p[:,1],np.ones(len(p))],(p*p).sum(1),rcond=None)[0]
 return v[:2],np.sqrt(v[2]+v[:2]@v[:2])
loops=base.section(plane_normal=[0,0,1],plane_origin=[0,0,10]).discrete
holes=np.array([c for c,r in map(circle_fit,loops) if abs(r-4.15)<.03]);assert len(holes)==18,len(holes)
records=[];assembled={k:v.copy() for k,v in g.items()};max_intersection=0.
def intersection(a,b,label):
 global max_intersection
 if np.any(np.minimum(a.bounds[1],b.bounds[1])-np.maximum(a.bounds[0],b.bounds[0])<1e-6):v=0.
 else:v=abs(float(trimesh.boolean.intersection([a,b],engine='manifold').volume))
 max_intersection=max(max_intersection,v)
 assert v<.01,(label,v)
 return v
for i in range(1,4):
 old=g['arm_'+str(i)];u=old.centroid[:2].copy();u/=np.linalg.norm(u);w=np.array([-u[1],u[0]])
 angle=math.atan2(u[1],u[0]);rot=trimesh.transformations.rotation_matrix(angle,[0,0,1])
 local=np.c_[holes@u,holes@w];chosen=local[(local[:,0]>70)&(np.abs(local[:,1])<8)]
 assert len(chosen)==4,(i,chosen)
 bolts=[]
 for x,y in chosen:
  nut=cq.Workplane('XY').workplane(offset=1).center(float(x),float(y)).polygon(6,7/math.cos(math.pi/6)).extrude(3.2)
  nut=nut.cut(cq.Workplane('XY').workplane(offset=.9).center(float(x),float(y)).circle(2.05).extrude(3.4))
  shank=cq.Workplane('XY').workplane(offset=1).center(float(x),float(y)).circle(2).extrude(8)
  head=cq.Workplane('XY').workplane(offset=9).center(float(x),float(y)).circle(3.8).extrude(2.2)
  nm,sm,hm=map(mod.mesh_from_cq,[nut,shank,head]);bolts.append((nm,sm,hm))
  for label,part in [('screw',sm),('head',hm)]:
   b=part.copy();b.apply_transform(rot);intersection(b,base,f'{label}/base arm {i}')
 for d in [-12,-6,0,6,12]:
  a=arm.copy();a.apply_translation([d,0,0])
  for j,(nm,sm,hm) in enumerate(bolts):
   intersection(a,nm,f'arm {i} offset {d} nut {j}')
   intersection(a,sm,f'arm {i} offset {d} shaft {j}')
  a.apply_transform(rot)
  checks={}
  for name in ['01_base_192_M4','03_wheel_spacer','02_cover_195','04_axle_shim']:
   checks[name]=intersection(a,g[name],f'arm {i} offset {d} / {name}')
  records.append({'arm':i,'radial_offset_mm':d,'intersection_mm3':checks})
 nominal=arm.copy();nominal.apply_transform(rot);assembled['arm_'+str(i)]=nominal
 print('arm',i,'four M4 fasteners and existing parts clear at offsets -12 to +12 mm',flush=True)
# Nominal fit to the measured 275 mm wheel, before adding 2 mm side padding.
wheel=trimesh.creation.cylinder(radius=137.5,height=15,sections=360);wheel.apply_translation([0,0,-7.5])
for i in range(1,4):intersection(assembled['arm_'+str(i)],wheel,f'arm {i}/275 mm wheel')
for i,j in itertools.combinations(range(1,4),2):intersection(assembled['arm_'+str(i)],assembled['arm_'+str(j)],'arms')
scene=trimesh.Scene()
for name,m in assembled.items():scene.add_geometry(m,node_name=name,geom_name=name)
scene.export(O/'verification/assembly_275mm.glb')
step=cq.importers.importStep(str(O/'STEP/06_adjustable_arm_275mm_v2.step')).val();assert step.isValid() and len(step.Solids())==1
report={'result':'PASS','wheel_diameter_mm':275,'assembly':'existing CCW base with original cover, sliders, spacer and shim; only arms replaced','bolt_rows':'middle and outer; 4 x M4x8 and 4 x M4 nuts per arm','radial_adjustment_checked_mm':[-12,12],'sampled_offsets_mm':[-12,-6,0,6,12],'maximum_intersection_mm3':max_intersection,'fastener_model':'4 mm shaft x 8 mm from seat at z=9; head 7.6 x 2.2 mm; M4 hex nut 7 AF x 3.2 mm; same as existing assembly','screw_tip_height_above_wheel_mm':1,'arm_new_length_mm':float(arm.extents[0]),'step_valid':True,'checks':records,'limitation':'CAD fit and sampled adjustment checks; physical print and rim contact not yet verified.'}
(O/'verification/compatibility.json').write_text(json.dumps(report,indent=2))
print('PASS; maximum intersection',max_intersection,flush=True)
