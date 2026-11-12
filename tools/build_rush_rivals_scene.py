"""
RUSH RIVALS — procedural Blender environment builder
Run with: blender --background --python tools/build_rush_rivals_scene.py
Outputs: assets/rush-rivals-world.blend and assets/rush-rivals-world.glb
Requires Blender 3.6+ with glTF 2.0 exporter.
"""
import bpy, math, os
from mathutils import Vector
from math import sin, cos, pi

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "assets")
os.makedirs(OUT, exist_ok=True)

# Clean scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials):
    pass

def mat(name, color, metallic=0.0, rough=0.55, emission=None, strength=0.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bs = m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = (*color, 1)
    bs.inputs["Metallic"].default_value = metallic
    bs.inputs["Roughness"].default_value = rough
    if emission:
        bs.inputs["Emission Color"].default_value = (*emission, 1)
        bs.inputs["Emission Strength"].default_value = strength
    return m

asphalt = mat("Track | midnight asphalt", (0.025,0.045,0.075), .25, .82)
concrete = mat("Track | pale concrete", (.22,.31,.40), .15, .78)
dark = mat("Structures | deep navy alloy", (.018,.055,.105), .72, .32)
glass = mat("Buildings | blue glass", (.025,.16,.26), .65, .2)
cyan = mat("Neon | electric cyan", (.02,.55,.8), .25, .28, (.0,.65,1.0), 3.0)
pink = mat("Neon | hot magenta", (.65,.025,.3), .2, .3, (1.0,.015,.28), 2.5)
gold = mat("Neon | warm amber", (.8,.34,.04), .2, .35, (1.0,.25,.015), 1.8)
white = mat("Road markings", (.75,.9,1), .1, .4, (.4,.75,1), .6)
ground_mat = mat("Ground | deep blue", (.012,.028,.055), .1, .95)
mountain_mat = mat("Terrain | slate", (.035,.075,.12), .05, .95)

def cube(name, loc, scale, material, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o=bpy.context.object; o.name=name; o.dimensions=scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if material: o.data.materials.append(material)
    if bevel:
        mod=o.modifiers.new("Soft machined edges","BEVEL"); mod.width=bevel; mod.segments=2
        o.modifiers.new("Weighted corner normals","WEIGHTED_NORMAL")
    return o

def cyl_between(name, a, b, radius, material, vertices=8):
    mid=(Vector(a)+Vector(b))/2
    d=Vector(b)-Vector(a)
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=d.length, location=mid)
    o=bpy.context.object; o.name=name; o.data.materials.append(material)
    o.rotation_mode='QUATERNION'; o.rotation_quaternion=d.to_track_quat('Z','Y')
    return o

# Closed Catmull-Rom track with deliberately varied elevation.
controls=[
 (0,2,92),(34,5,88),(68,11,66),(82,16,34),(72,12,8),
 (48,5,-8),(62,1,-38),(38,4,-72),(4,10,-84),(-30,15,-72),
 (-62,10,-48),(-82,4,-12),(-70,1,24),(-42,4,62),(-18,8,82)
]
P=[Vector(v) for v in controls]
def sample(t):
    u=(t%1.0)*len(P); i=int(u); f=u-i
    p0=P[(i-1)%len(P)]; p1=P[i%len(P)]; p2=P[(i+1)%len(P)]; p3=P[(i+2)%len(P)]
    return .5*((2*p1)+(-p0+p2)*f+(2*p0-5*p1+4*p2-p3)*f*f+(-p0+3*p1-3*p2+p3)*f*f*f)

N=480
centers=[sample(i/N) for i in range(N+1)]
tangents=[]
for i in range(N+1):
    tangents.append((sample((i+1)/N)-sample((i-1)/N)).normalized())
# Ribbon road mesh
verts=[]; faces=[]
for i,(p,tan) in enumerate(zip(centers,tangents)):
    side=Vector((-tan.z,0,tan.x)).normalized()
    for edge in (-10,10):
        verts.append((p.x+side.x*edge,p.y,p.z+side.z*edge))
for i in range(N):
    a=2*i; faces.append((a,a+1,a+3,a+2))
mesh=bpy.data.meshes.new("Continuous banked raceway mesh"); mesh.from_pydata(verts,[],faces); mesh.materials.append(asphalt)
road=bpy.data.objects.new("RACEWAY | 20m wide closed asphalt ribbon",mesh); bpy.context.collection.objects.link(road)
for poly in mesh.polygons: poly.use_smooth=True
solid=road.modifiers.new("Road thickness","SOLIDIFY"); solid.thickness=.45
bev=road.modifiers.new("Road edge bevel","BEVEL"); bev.width=.12; bev.segments=2

# Raised curbs, safety rails and dashed center markings.
for side_sign in (-1,1):
    rail_curve=bpy.data.curves.new("Neon safety rail path","CURVE"); rail_curve.dimensions='3D'; rail_curve.bevel_depth=.34; rail_curve.bevel_resolution=2
    sp=rail_curve.splines.new('POLY'); sp.points.add(N)
    for i,(p,tan) in enumerate(zip(centers,tangents)):
        side=Vector((-tan.z,0,tan.x)).normalized()*side_sign
        q=p+side*10.45+Vector((0,.75,0)); sp.points[i].co=(q.x,q.y,q.z,1)
    sp.use_cyclic_u=True
    obj=bpy.data.objects.new("Continuous cyan guardrail" if side_sign<0 else "Continuous magenta guardrail",rail_curve)
    bpy.context.collection.objects.link(obj); obj.data.materials.append(cyan if side_sign<0 else pink)
    # segmented curb blocks are light enough and readable
    for i in range(0,N,4):
        p=centers[i]; tan=tangents[i]; side=Vector((-tan.z,0,tan.x)).normalized()*side_sign
        q=p+side*9.85+Vector((0,.18,0))
        o=cube("Reflective curb segment",q,(1.05,.32,.42),pink if (i//4)%2 else white,.06)
        o.rotation_euler[1]=math.atan2(tan.x,tan.z)

for i in range(0,N,12):
    p=centers[i]; tan=tangents[i]
    o=cube("Dashed centerline", (p.x,p.y+.035,p.z),(.22,.045,3.0),white,.025)
    o.rotation_euler[1]=math.atan2(tan.x,tan.z)

# Start/finish arch and two intermediate checkpoint arches.
def arch_at(index, label):
    p=centers[index%N]; tan=tangents[index%N]; yaw=math.atan2(tan.x,tan.z)
    for s in (-1,1):
        q=p+Vector(( -tan.z*s*8.8,0,tan.x*s*8.8))
        cube(label+" | upright", (q.x,p.y+4,q.z),(.9,8,.9),dark,.16)
        cube(label+" | luminous upright", (q.x,p.y+4,q.z),(.18,7.5,.22),cyan,.04)
    beam=cube(label+" | overhead beam",(p.x,p.y+8,p.z),(19,.85,.9),dark,.16); beam.rotation_euler[1]=yaw
    beam2=cube(label+" | neon beam",(p.x,p.y+8.05,p.z),(18,.16,.95),pink,.04); beam2.rotation_euler[1]=yaw
arch_at(0,"START FINISH")
arch_at(115,"CHECKPOINT A")
arch_at(325,"CHECKPOINT B")

# Futuristic tunnel portal near the high-speed back straight.
def tunnel_at(index):
    p=centers[index]; tan=tangents[index]; yaw=math.atan2(tan.x,tan.z)
    # Rectangular portal frame, sized for a 20m road.
    for s in (-1,1):
        q=p+Vector((-tan.z*s*10.5,0,tan.x*s*10.5))
        post=cube("TUNNEL | portal pier",(q.x,p.y+4,q.z),(2.0,8.0,3.0),concrete,.22); post.rotation_euler[1]=yaw
        stripe=cube("TUNNEL | neon pier",(q.x,p.y+4,q.z),(2.12,7.5,.22),cyan,.05); stripe.rotation_euler[1]=yaw
    lintel=cube("TUNNEL | crown",(p.x,p.y+8,p.z),(24,2.0,3.0),dark,.25); lintel.rotation_euler[1]=yaw
    glow=cube("TUNNEL | glowing crown",(p.x,p.y+8.0,p.z),(20,.18,3.12),pink,.05); glow.rotation_euler[1]=yaw
tunnel_at(235)

# Stylized skyline: instanced-looking low-poly towers kept away from road.
for i in range(34):
    t=(i/34.0)
    p=centers[int(t*N)]; tan=tangents[int(t*N)]
    side=Vector((-tan.z,0,tan.x)).normalized()
    s=-1 if i%2==0 else 1
    offset=18+(i%4)*5
    q=p+side*s*offset
    h=7+(i*13%23); w=3+(i%3)*1.3; d=3+(i%4)*.9
    b=cube("NEON DISTRICT | tower %02d"%i,(q.x,h/2-.1,q.z),(w,h,d),glass,.18)
    # sparse vertical neon edge, not a dense window grid
    edge=cube("Tower cyan edge",(q.x-w/2-.08,h/2,q.z),(0.12,h*.88,d*.75),cyan,.025)
    if i%3==0:
        roof=cube("Tower rooftop beacon",(q.x,h+.45,q.z),(w*.5,.45,d*.5),pink,.08)

# Mountain silhouettes outside the city for a strong horizon.
for i in range(14):
    angle=2*pi*i/14
    radius=145+(i%3)*12
    x=cos(angle)*radius; z=sin(angle)*radius
    height=24+(i*11%34)
    bpy.ops.mesh.primitive_cone_add(vertices=5, radius1=22+(i%4)*4, radius2=0, depth=height, location=(x,height/2-1,z))
    m=bpy.context.object; m.name="DISTANT RIDGE | low-poly peak"; m.data.materials.append(mountain_mat)

# Streetlights: sparse paired lamps, no costly point lights.
for i in range(0,N,32):
    p=centers[i]; tan=tangents[i]; side=Vector((-tan.z,0,tan.x)).normalized()
    for s in (-1,1):
        q=p+side*s*13.5
        cyl_between("Streetlight pole",(q.x,p.y,q.z),(q.x,p.y+5.8,q.z),.12,dark,8)
        cube("Streetlight cyan head",(q.x,p.y+5.9,q.z),(.7,.18,.35),cyan,.06)

# Large ground plane and a few readable trackside billboards.
cube("World ground",(0,-2.4,0),(420,.8,420),ground_mat)
for i in range(8):
    p=centers[(i*59+28)%N]; tan=tangents[(i*59+28)%N]; side=Vector((-tan.z,0,tan.x)).normalized()
    q=p+side*(1 if i%2 else -1)*15
    sign=cube("RUSH RIVALS trackside sponsor panel",(q.x,3.1,q.z),(4.8,2.2,.25),dark,.1)
    sign.rotation_euler[1]=math.atan2(tan.x,tan.z)
    glow=cube("Sponsor panel neon trim",(q.x,4.2,q.z),(4.5,.09,.3),gold,.025)
    glow.rotation_euler[1]=math.atan2(tan.x,tan.z)

# Lighting and camera for the saved .blend preview.
world=bpy.context.scene.world
if world:
    world.color=(.015,.025,.05)
    world.use_nodes=True
    world.node_tree.nodes["Background"].inputs[0].default_value=(.012,.025,.05,1)
    world.node_tree.nodes["Background"].inputs[1].default_value=.35
bpy.ops.object.camera_add(location=(125,105,145))
cam=bpy.context.object; cam.name="Preview camera"
cam.rotation_euler=(math.radians(62),0,math.radians(42))
cam.data.lens=48
bpy.context.scene.camera=cam
bpy.ops.object.light_add(type='AREA', location=(10,95,5))
key=bpy.context.object; key.name="Preview softbox"; key.data.energy=1800; key.data.shape='DISK'; key.data.size=90

# Select all exportable environment meshes/curves; omit preview camera and light.
bpy.ops.object.select_all(action='DESELECT')
for obj in bpy.context.scene.objects:
    if obj.type in {'MESH','CURVE'}: obj.select_set(True)
bpy.context.view_layer.objects.active=road

# Save editable project, then export a runtime-friendly GLB.
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,"rush-rivals-world.blend"))
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,"rush-rivals-world.glb"), export_format='GLB', use_selection=True, export_apply=True)
print("RUSH RIVALS environment exported to", OUT)
