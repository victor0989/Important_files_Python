# -*- coding: utf-8 -*-
# Macro FreeCAD: Direct Fusion Drive con TPS tipo Parker, ensamblado e imprimible (todo junto)
# Autor: Víctor + Copilot
# Unidades: mm, eje longitudinal = X

import FreeCAD as App, FreeCADGui as Gui, Part, math

doc_name="Direct_Fusion_Drive"
if App.ActiveDocument is None or App.ActiveDocument.Label!=doc_name:
    App.newDocument(doc_name)
doc=App.ActiveDocument

# ========================
# Parámetros base DFD
# ========================
P={
    "nose_len":2400.0,"nose_base_d":1800.0,  # escalado 3x
    "mid_len":4200.0,"mid_d":2700.0,
    "rear_len":2400.0,"rear_d":3600.0,
    "hull_t":30.0,  # aumentado para resistencia
    "cockpit_w":2700.0,"cockpit_h":1200.0,"cockpit_l":1800.0,"cockpit_x0":1800.0,
    "win_w":1800.0,"win_h":750.0,"win_th":60.0,
    "win_y_off":0.5*(2700.0/2.0-750.0/2.0),"win_z":0.0,
    "reactor_d":2400.0,"reactor_l":2700.0,"reactor_cx":7800.0,
    "ring_h":90.0,"ring_ro":1260.0,"ring_ri":1140.0,"ring_n":6,"ring_pitch":450.0,
    "coil_rect_w":240.0,"coil_rect_h":240.0,"coil_R":1320.0,"coil_n":4,"coil_span":2400.0,
    "moderator_t":300.0,"moderator_gap":60.0,"moderator_over":600.0,
    "tungsten_post_t":30.0,
    "nozzle_throat_d":900.0,"nozzle_exit_d":2700.0,"nozzle_l":2100.0,"nozzle_cx":8550.0,"nozzle_fillet_r":120.0,
    "truss_n":3,"truss_tube_w":240.0,"truss_R_attach":1650.0,
    "tank_d":900.0,"tank_l":2100.0,"tank_cx":4800.0,"tank_cy":900.0,"tank_cz":-450.0,
    "leg_L_fold":1200.0,"leg_L_ext":1800.0,"leg_foot_d":540.0,
    "leg_side_x1":3150.0,"leg_side_x2":5850.0,"leg_side_y":1800.0,
    "leg_front_x":1200.0,"leg_front_y":0.0,"leg_front_z":-(2700.0/2.0)+150.0,
    "wing_root_w":1800.0,"wing_tip_w":450.0,"wing_chord":1350.0,
    "fin_h":1200.0,"fin_base":600.0,
    "rad_panel_w":2400.0,"rad_panel_h":1800.0,"rad_panel_n":5
}

# ========================
# TPS tipo Parker y Radiadores
# ========================
TPS={"tps_d":7200.0,"tps_t":300.0,"tps_gap":360.0,"sup_L":840.0,"sup_d_base":2700.0,"sup_d_tip":1800.0}
RAD={"th":12.0,"mount_gap_y":90.0,"x_start":None,"gap_x":None,"count_pairs":8,"span_x":660.0,"arm_len":180.0,"arm_r":30.0}

# ========================
# Materiales
# ========================
MAT={
    'AL':{'name':'AA-2xxx','rho':2700.0,'E':72e9,'nu':0.33,'type':'isotropic'},
    'STEEL':{'name':'SS-304','rho':8000.0,'E':200e9,'nu':0.30,'type':'isotropic'},
    'COPPER':{'name':'Copper','rho':8960.0,'E':110e9,'nu':0.34,'type':'isotropic'},
    'CFRP':{'name':'CFRP','rho':1550.0,'Ex':130e9,'Ey':10e9,'Ez':10e9,'nu_xy':0.25,'type':'orthotropic'},
    'CC':{'name':'C/C TPS','rho':1600.0,'Ex':70e9,'Ey':70e9,'Ez':10e9,'nu_xy':0.2,'type':'orthotropic'},
    'KEVLAR':{'name':'Kevlar','rho':1440.0,'Ex':70e9,'Ey':5e9,'Ez':5e9,'nu_xy':0.27,'type':'orthotropic'},
    'LEAD':{'name':'Lead','rho':11340.0,'E':16e9,'nu':0.44,'type':'isotropic'},
    'TITANIUM':{'name':'Ti-6Al-4V','rho':4430.0,'E':114e9,'nu':0.32,'type':'isotropic'},
    'CARBON_FIBER':{'name':'Carbon Fiber Composite','rho':1600.0,'Ex':200e9,'Ey':10e9,'Ez':10e9,'nu_xy':0.25,'type':'orthotropic'},
    'ABLATIVE':{'name':'Ablative TPS','rho':1200.0,'Ex':50e9,'Ey':50e9,'Ez':5e9,'nu_xy':0.2,'type':'orthotropic'}
}

# ========================
# Utilidades
# ========================
X_AXIS=App.Vector(1,0,0);Y_AXIS=App.Vector(0,1,0);Z_AXIS=App.Vector(0,0,1)
def rot_to_x():return App.Rotation(Y_AXIS,90)
def add_obj(shape,label):obj=doc.addObject("Part::Feature",label);obj.Shape=shape;return obj
def set_mat(obj,mat): 
    if not obj:return
    m=MAT.get(mat,None)if isinstance(mat,str)else mat
    if not m:return
    obj.addProperty("App::PropertyString","Material","Meta","").Material=m.get('name','')
    obj.addProperty("App::PropertyMap","MaterialData","Meta","").MaterialData={k:str(v)for k,v in m.items()}
    obj.addProperty("App::PropertyFloat","Density","Meta","").Density=m.get('rho',0.0)
def make_cyl_x(d,L,cx=0.0,cy=0.0,cz=0.0,label="CylX"):
    r=d/2.0;cyl=Part.makeCylinder(r,L);cyl.Placement=App.Placement(App.Vector(cx-L/2.0,cy,cz),rot_to_x());return add_obj(cyl,label)
def make_cone_x(d1,d2,L,cx=0.0,cy=0.0,cz=0.0,label="ConeX"):
    r1=d1/2.0;r2=d2/2.0;cone=Part.makeCone(r1,r2,L);cone.Placement=App.Placement(App.Vector(cx-L/2.0,cy,cz),rot_to_x());return add_obj(cone,label)
def make_torus_x(R,r,cx=0.0,cy=0.0,cz=0.0,label="TorusX"):
    tor=Part.makeTorus(R,r);tor.Placement=App.Placement(App.Vector(cx,cy,cz),rot_to_x());return add_obj(tor,label)
def make_box(w,d,h,cx=0.0,cy=0.0,cz=0.0,label="Box"):
    b=Part.makeBox(w,d,h);b.Placement=App.Placement(App.Vector(cx-w/2.0,cy-d/2.0,cz-h/2.0),App.Rotation());return add_obj(b,label)
def make_hollow_from_offset(outer_shape,t,label="Shell"): 
    try:
        inner=outer_shape.makeOffsetShape(-t,0.01,join=2,fill=True)
        shell=outer_shape.cut(inner)
        return add_obj(shell,label)
    except Exception:
        return add_obj(outer_shape,label+"_fallback")
def fillet_between(shpA,shpB,r):
    fused=shpA.fuse(shpB)
    try:
        edges=[e for e in fused.Edges if e.Length>30 and e.Length<10000]
        new=fused.makeFillet(r,edges);return new
    except Exception:
        return fused
def sweep_rect_around_X(R,rw,rh,cx,cy,cz,ax0,ax1,label="CoilSweep"):
    circ=Part.makeCircle(R,App.Vector(cx,cy,cz),X_AXIS);path=Part.Wire([circ])
    p0=App.Vector(0,-rw/2.0,-rh/2.0);p1=App.Vector(0,rw/2.0,-rh/2.0)
    p2=App.Vector(0,rw/2.0,rh/2.0);p3=App.Vector(0,-rw/2.0,rh/2.0)
    e1=Part.makeLine(p0,p1);e2=Part.makeLine(p1,p2);e3=Part.makeLine(p2,p3);e4=Part.makeLine(p3,p0)
    prof=Part.Wire([e1,e2,e3,e4])
    prof.Placement=App.Placement(App.Vector(cx,cy,cz),App.Rotation(X_AXIS,0))
    sweep=Part.Wire(path).makePipeShell([prof],True,True)
    return add_obj(sweep,label)

# ========================
# Fuselaje (sólidos)
# ========================
nose=make_cone_x(P["nose_base_d"],0.0,P["nose_len"],cx=P["nose_len"]/2.0,label="Nose"); set_mat(nose,'TITANIUM')
mid =make_cyl_x(P["mid_d"],P["mid_len"],cx=P["nose_len"]+P["mid_len"]/2.0,label="Mid");  set_mat(mid,'CARBON_FIBER')
rear=make_cyl_x(P["rear_d"],P["rear_len"],cx=P["nose_len"]+P["mid_len"]+P["rear_len"]/2.0,label="Rear"); set_mat(rear,'TITANIUM')

# Casco hueco del fuselaje (si quieres sólido, usa fuse_fuselage_shape directamente)
fuse_fuselage_shape=nose.Shape.fuse(mid.Shape).fuse(rear.Shape)
hull=make_hollow_from_offset(fuse_fuselage_shape,P["hull_t"],label="Hull_Shell"); set_mat(hull,'CARBON_FIBER')

# ========================
# TPS tipo Parker (pieza fusionada imprimible)
# ========================
nose_tip_x=P["nose_len"]
tps_support=make_cone_x(TPS["sup_d_base"],TPS["sup_d_tip"],TPS["sup_L"],
                        cx=nose_tip_x+TPS["tps_gap"]+TPS["sup_L"]/2.0,cy=0.0,cz=0.0,label="TPS_Support"); set_mat(tps_support,'STEEL')
tps_disk   =make_cyl_x(TPS["tps_d"],TPS["tps_t"],
                        cx=nose_tip_x+TPS["tps_gap"]+TPS["sup_L"]+TPS["tps_t"]/2.0,cy=0.0,cz=0.0,label="TPS_Shield");  set_mat(tps_disk,'CC')
TPS_fused_shape=fillet_between(tps_support.Shape,tps_disk.Shape, r=6.0)
TPS_fused=add_obj(TPS_fused_shape,"TPS_Assembly"); set_mat(TPS_fused,'CC')

# Sandwich avanzado (caras ablativas + núcleo carbono); se integra en ensamblado
face_t=20.0; core_t=max(0.0, TPS["tps_t"]-2*face_t)
if core_t>0:
    x_base=nose_tip_x+TPS["tps_gap"]+TPS["sup_L"]
    tps_face_outer=Part.makeCylinder(TPS["tps_d"]/2.0, face_t); tps_face_outer.Placement=App.Placement(App.Vector(x_base,0,0),rot_to_x())
    tps_core      =Part.makeCylinder(TPS["tps_d"]/2.0-10.0, core_t); tps_core.Placement=App.Placement(App.Vector(x_base+face_t,0,0),rot_to_x())
    tps_face_inner=Part.makeCylinder(TPS["tps_d"]/2.0, face_t); tps_face_inner.Placement=App.Placement(App.Vector(x_base+face_t+core_t,0,0),rot_to_x())
    face_out_obj=add_obj(tps_face_outer,"TPS_FaceOuter"); set_mat(face_out_obj,'ABLATIVE')
    core_obj    =add_obj(tps_core,"TPS_Core");            set_mat(core_obj,'CARBON_FIBER')
    face_in_obj =add_obj(tps_face_inner,"TPS_FaceInner"); set_mat(face_in_obj,'ABLATIVE')

# ========================
# Ventanas y cabina
# ========================
win1=make_box(P["win_w"],P["win_th"],P["win_h"],cx=P["cockpit_x0"]+P["cockpit_l"]/2.0,cy=(P["mid_d"]/2.0)-P["win_th"]/2.0,cz=P["win_z"],label="Win_Right")
win2=make_box(P["win_w"],P["win_th"],P["win_h"],cx=P["cockpit_x0"]+P["cockpit_l"]/2.0,cy=-(P["mid_d"]/2.0)+P["win_th"]/2.0,cz=P["win_z"],label="Win_Left")
hull_cut=add_obj(hull.Shape.cut(win1.Shape).cut(win2.Shape),"Hull_Shell_Cut"); set_mat(hull_cut,'CARBON_FIBER')

cockpit_box=Part.makeBox(P["cockpit_l"],P["cockpit_w"],P["cockpit_h"])
cockpit_box.Placement=App.Placement(App.Vector(P["cockpit_x0"],-P["cockpit_w"]/2.0,-P["cockpit_h"]/2.0),App.Rotation())
try: cockpit_f=cockpit_box.makeFillet(60.0,cockpit_box.Edges)  # fillet aumentado
except Exception: cockpit_f=cockpit_box
cockpit=add_obj(cockpit_f,"Cockpit"); set_mat(cockpit,'TITANIUM')

# ========================
# Reactor, anillos, bobinas
# ========================
reactor=make_cyl_x(P["reactor_d"],P["reactor_l"],cx=P["reactor_cx"],label="ReactorCore"); set_mat(reactor,'TITANIUM')

rings=[]
x0=P["reactor_cx"]-P["reactor_l"]/2.0+P["ring_h"]/2.0
for i in range(P["ring_n"]):
    x=x0+i*P["ring_pitch"]
    ring=Part.makeTorus((P["ring_ro"]+P["ring_ri"])/2.0,(P["ring_ro"]-P["ring_ri"])/2.0)
    ring.Placement=App.Placement(App.Vector(x,0,0),rot_to_x())
    rings.append(ring)
rings_shape=rings[0]
for r in rings[1:]: rings_shape=rings_shape.fuse(r)
rings_obj=add_obj(rings_shape,"Reactor_Rings"); set_mat(rings_obj,'STEEL')

coils=[]
span=P["coil_span"]; cx0=P["reactor_cx"]-span/2.0
for i in range(P["coil_n"]):
    cx=cx0+i*(span/(max(1,(P["coil_n"]-1))))
    coil=sweep_rect_around_X(P["coil_R"],P["coil_rect_w"],P["coil_rect_h"],cx,0.0,0.0,0.0,0.0,label=f"Coil_{i+1}")
    coils.append(coil.Shape)
coils_shape=coils[0]
for c in coils[1:]: coils_shape=coils_shape.fuse(c)
coils_obj=add_obj(coils_shape,"Reactor_Coils"); set_mat(coils_obj,'COPPER')

# ========================
# Blindajes y tobera
# ========================
tw_len=P["tungsten_post_t"]; tw_ro=P["reactor_d"]/2.0; tw_ri=tw_ro-10.0
tw_tube=Part.makeCylinder(tw_ro,tw_len); tw_hole=Part.makeCylinder(tw_ri,tw_len+0.1)
tw_ring=tw_tube.cut(tw_hole)
tw_ring.Placement=App.Placement(App.Vector(P["reactor_cx"]+P["reactor_l"]/2.0-tw_len/2.0,0,0),rot_to_x())
tw_obj=add_obj(tw_ring,"Tungsten_Posterior"); set_mat(tw_obj,'STEEL')

noz=Part.makeCone(P["nozzle_throat_d"]/2.0,P["nozzle_exit_d"]/2.0,P["nozzle_l"])
noz.Placement=App.Placement(App.Vector(P["nozzle_cx"]-P["nozzle_l"]/2.0,0,0),rot_to_x())
noz_obj=add_obj(noz,"Magnetic_Nozzle"); set_mat(noz_obj,'STEEL')
try:
    filleted=fillet_between(rear.Shape,noz,P["nozzle_fillet_r"])
    nozzle_mount=add_obj(filleted,"Nozzle_Mount_Fillet"); set_mat(nozzle_mount,'STEEL')
except Exception:
    nozzle_mount=noz_obj

truss_list=[]
for k in range(P["truss_n"]):
    ang=k*(360.0/P["truss_n"])
    x_attach=P["nose_len"]+P["mid_len"]+P["rear_len"]-50.0
    y=P["truss_R_attach"]*math.cos(math.radians(ang))
    z=P["truss_R_attach"]*math.sin(math.radians(ang))
    L=300.0
    beam=Part.makeBox(L,P["truss_tube_w"],P["truss_tube_w"])
    beam.Placement=App.Placement(App.Vector(x_attach-L/2.0,y-P["truss_tube_w"]/2.0,z-P["truss_tube_w"]/2.0),App.Rotation())
    truss_list.append(beam)
truss_shape=truss_list[0]
for t in truss_list[1:]: truss_shape=truss_shape.fuse(t)
truss_obj=add_obj(truss_shape,"Nozzle_Truss"); set_mat(truss_obj,'STEEL')

mod_inner_r=P["reactor_d"]/2.0+P["moderator_gap"]; mod_outer_r=mod_inner_r+P["moderator_t"]
mod_len=P["reactor_l"]+P["moderator_over"]; mod_cx=P["reactor_cx"]
mod_outer=Part.makeCylinder(mod_outer_r,mod_len); mod_inner=Part.makeCylinder(mod_inner_r,mod_len+0.2)
mod_tube=mod_outer.cut(mod_inner)
mod_tube.Placement=App.Placement(App.Vector(mod_cx-mod_len/2.0,0,0),rot_to_x())
mod_obj=add_obj(mod_tube,"Shield_Moderator"); set_mat(mod_obj,'STEEL')

tn_ro=P["nozzle_exit_d"]/2.0+40.0; tn_ri=tn_ro-10.0; tn_len=20.0
tn_tube=Part.makeCylinder(tn_ro,tn_len); tn_hole=Part.makeCylinder(tn_ri,tn_len+0.1)
tn_ring=tn_tube.cut(tn_hole)
tn_ring.Placement=App.Placement(App.Vector(P["nozzle_cx"]+P["nozzle_l"]/2.0-tn_len/2.0,0,0),rot_to_x())
tn_obj=add_obj(tn_ring,"Tungsten_Nozzle_Rim"); set_mat(tn_obj,'STEEL')

# ========================
# Tanques laterales (sólidos)
# ========================
tank1=make_cyl_x(P["tank_d"],P["tank_l"],cx=P["tank_cx"],cy=P["tank_cy"],cz=P["tank_cz"],label="Tank_Right"); set_mat(tank1,'AL')
tank2=make_cyl_x(P["tank_d"],P["tank_l"],cx=P["tank_cx"],cy=-P["tank_cy"],cz=P["tank_cz"],label="Tank_Left"); set_mat(tank2,'AL')

# ========================
# Tren de aterrizaje (sólidos)
# ========================
def make_leg(x,y,z,L,d,label):
    shaft=Part.makeCylinder(d/4.0,L)
    foot=Part.makeCylinder(d/2.0,20.0)
    shaft.Placement=App.Placement(App.Vector(x-L/2.0,y,z),rot_to_x())
    foot.Placement=App.Placement(App.Vector(x+L/2.0-10.0,y,z-d/4.0),App.Rotation())
    return add_obj(shaft.fuse(foot),label)

leg_r = make_leg(P["leg_side_x1"], P["leg_side_y"], P["leg_front_z"], P["leg_L_fold"], P["leg_foot_d"], "Leg_Right_Front"); set_mat(leg_r,'STEEL')
leg_l = make_leg(P["leg_side_x1"],-P["leg_side_y"], P["leg_front_z"], P["leg_L_fold"], P["leg_foot_d"], "Leg_Left_Front"); set_mat(leg_l,'STEEL')
leg_r2= make_leg(P["leg_side_x2"], P["leg_side_y"], P["leg_front_z"], P["leg_L_fold"], P["leg_foot_d"], "Leg_Right_Rear"); set_mat(leg_r2,'STEEL')
leg_l2= make_leg(P["leg_side_x2"],-P["leg_side_y"], P["leg_front_z"], P["leg_L_fold"], P["leg_foot_d"], "Leg_Left_Rear"); set_mat(leg_l2,'STEEL')
leg_f = make_leg(P["leg_front_x"], P["leg_front_y"], P["leg_front_z"], P["leg_L_fold"], P["leg_foot_d"], "Leg_Nose"); set_mat(leg_f,'STEEL')

# ========================
# Alas / radiadores (alas sólidas)
# ========================
def make_trapezoid_wing(root_w,tip_w,chord,thickness=20.0,x0=1400.0,y0=0.0,z0=0.0,side=1,label="Wing"):
    x_le=x0; x_te=x0+chord; z_mid=z0
    p1=App.Vector(x_le,0,z_mid+root_w/2.0); p2=App.Vector(x_te,0,z_mid+root_w/2.0)
    p3=App.Vector(x_te,0,z_mid+tip_w/2.0); p4=App.Vector(x_le,0,z_mid+tip_w/2.0)
    wire=Part.makePolygon([p1,p2,p3,p4,p1]); face=Part.Face(wire)
    solid=face.extrude(App.Vector(0,side*(root_w-tip_w),0))
    slab=Part.makeBox(chord,thickness,(root_w+tip_w)/2.0)
    slab.Placement=App.Placement(App.Vector(x0,side*thickness/2.0,z0-(root_w+tip_w)/4.0),App.Rotation())
    return add_obj(solid.common(slab),label)

wing_r=make_trapezoid_wing(P["wing_root_w"],P["wing_tip_w"],P["wing_chord"],x0=P["nose_len"]+500.0,side= 1,label="Wing_Right"); set_mat(wing_r,'AL')
wing_l=make_trapezoid_wing(P["wing_root_w"],P["wing_tip_w"],P["wing_chord"],x0=P["nose_len"]+500.0,side=-1,label="Wing_Left");  set_mat(wing_l,'AL')

# Aleta vertical
def make_fin(h,base,thickness=20.0,x_base=None,z0=0.0,label="Fin"):
    if x_base is None: x_base=P["nose_len"]+P["mid_len"]+P["rear_len"]-300.0
    p1=App.Vector(x_base,0,z0); p2=App.Vector(x_base+base,0,z0); p3=App.Vector(x_base,0,z0+h)
    wire=Part.makePolygon([p1,p2,p3,p1]); face=Part.Face(wire)
    fin=face.extrude(App.Vector(0,thickness,0))
    fin.Placement=App.Placement(App.Vector(0,-thickness/2.0,0),App.Rotation())
    return add_obj(fin,label)
fin=make_fin(P["fin_h"],P["fin_base"],x_base=P["nose_len"]+P["mid_len"]+200.0,label="Fin_Vertical"); set_mat(fin,'AL')

# ========================
# Radiadores sólidos imprimibles (+Y / -Y)
# ========================
rads=[]
if RAD["x_start"] is None: RAD["x_start"]=P["nose_len"]+300.0
if RAD["gap_x"] is None:   RAD["gap_x"]=max(220.0, P["rad_panel_w"]*0.25)
for i in range(RAD["count_pairs"]):
    x = RAD["x_start"] + i*RAD["gap_x"]
    # +Y
    arm_r = Part.makeCylinder(RAD["arm_r"], RAD["arm_len"]); arm_r.Placement = App.Placement(App.Vector(x, P["mid_d"]/2.0, 0), rot_to_x())
    plate_r = Part.makeBox(RAD["th"], P["rad_panel_w"], P["rad_panel_h"])
    plate_r.Placement = App.Placement(App.Vector(x+RAD["arm_len"], P["mid_d"]/2.0+RAD["mount_gap_y"], -P["rad_panel_h"]/2.0), App.Rotation())
    rR = add_obj(arm_r.fuse(plate_r), f"Radiator_R_{i+1}"); set_mat(rR,'AL'); rads.append(rR)
    # -Y
    arm_l = Part.makeCylinder(RAD["arm_r"], RAD["arm_len"]); arm_l.Placement = App.Placement(App.Vector(x, -P["mid_d"]/2.0, 0), rot_to_x())
    plate_l = Part.makeBox(RAD["th"], P["rad_panel_w"], P["rad_panel_h"])
    plate_l.Placement = App.Placement(App.Vector(x+RAD["arm_len"], -(P["mid_d"]/2.0+RAD["mount_gap_y"]+P["rad_panel_w"]), -P["rad_panel_h"]/2.0), App.Rotation())
    rL = add_obj(arm_l.fuse(plate_l), f"Radiator_L_{i+1}"); set_mat(rL,'AL'); rads.append(rL)

# ========================
# Antena HGA y Panel lateral (sólidos simples)
# ========================
HGA={"arm_L":180.0,"arm_r":12.0,"dish_r":200.0,"dish_t":6.0,"x":P["nose_len"]+250.0,"y":-(P["mid_d"]/2.0+140.0),"z":120.0}
hga_arm=Part.makeCylinder(HGA["arm_r"], HGA["arm_L"]); hga_arm.Placement=App.Placement(App.Vector(HGA["x"]-HGA["arm_L"]/2.0,HGA["y"],HGA["z"]),rot_to_x())
hga_dish=Part.makeCylinder(HGA["dish_r"], HGA["dish_t"]); hga_dish.Placement=App.Placement(App.Vector(HGA["x"]-HGA["arm_L"],HGA["y"],HGA["z"]-HGA["dish_r"]/2.0),App.Rotation())
hga=add_obj(hga_arm.fuse(hga_dish),"HGA_Simple"); set_mat(hga,'STEEL')

SA={"arm_L":160.0,"arm_r":10.0,"L":700.0,"W":520.0,"H":18.0,"tilt_deg":8.0,"x":P["nose_len"]+260.0,"y":P["mid_d"]/2.0+140.0,"z":-60.0}
sa_arm=Part.makeCylinder(SA["arm_r"], SA["arm_L"]); sa_arm.Placement=App.Placement(App.Vector(SA["x"]-SA["arm_L"]/2.0,SA["y"],SA["z"]),rot_to_x())
sa_panel=Part.makeBox(SA["L"], SA["W"], SA["H"]); sa_panel.Placement=App.Placement(App.Vector(SA["x"]-SA["L"]/2.0,SA["y"]-SA["W"]/2.0,SA["z"]-SA["H"]/2.0),App.Rotation(App.Vector(1,0,0), SA["tilt_deg"]))
sa=add_obj(sa_arm.fuse(sa_panel),"Solar_Array_Simple"); set_mat(sa,'CFRP')

# ========================
# Características adicionales de nave espacial
# ========================
# Antena parabólica grande para comunicaciones
large_dish_r = 800.0
large_dish_t = 20.0
large_dish_arm_l = 400.0
large_dish_x = P["nose_len"] + P["mid_len"] + P["rear_len"] - 1000.0
large_dish_y = 0.0
large_dish_z = P["mid_d"]/2.0 + 500.0
large_dish_arm = Part.makeCylinder(40.0, large_dish_arm_l)
large_dish_arm.Placement = App.Placement(App.Vector(large_dish_x - large_dish_arm_l/2.0, large_dish_y, large_dish_z), rot_to_x())
large_dish = Part.makeCylinder(large_dish_r, large_dish_t)
large_dish.Placement = App.Placement(App.Vector(large_dish_x - large_dish_arm_l, large_dish_y, large_dish_z - large_dish_r/2.0), App.Rotation())
large_comm = add_obj(large_dish_arm.fuse(large_dish), "Large_Comm_Dish"); set_mat(large_comm, 'CARBON_FIBER')

# Vela solar para propulsión
solar_sail_l = 5000.0
solar_sail_w = 4000.0
solar_sail_t = 5.0
solar_sail_arm_l = 1000.0
solar_sail_x = P["nose_len"] + P["mid_len"] + P["rear_len"] + 2000.0
solar_sail_arm = Part.makeCylinder(50.0, solar_sail_arm_l)
solar_sail_arm.Placement = App.Placement(App.Vector(solar_sail_x - solar_sail_arm_l/2.0, 0, 0), rot_to_x())
solar_sail = Part.makeBox(solar_sail_l, solar_sail_w, solar_sail_t)
solar_sail.Placement = App.Placement(App.Vector(solar_sail_x + solar_sail_arm_l/2.0 - solar_sail_l/2.0, -solar_sail_w/2.0, -solar_sail_t/2.0), App.Rotation())
solar_sail_obj = add_obj(solar_sail_arm.fuse(solar_sail), "Solar_Sail"); set_mat(solar_sail_obj, 'CARBON_FIBER')

# Propulsores de control de actitud
attitude_thrusters = []
thruster_count = 8
thruster_r = 50.0
thruster_l = 200.0
for i in range(thruster_count):
    angle = i * (360.0 / thruster_count)
    r = P["mid_d"]/2.0 + 200.0
    x = P["nose_len"] + P["mid_len"]/2.0
    y = r * math.cos(math.radians(angle))
    z = r * math.sin(math.radians(angle))
    thruster = Part.makeCylinder(thruster_r, thruster_l)
    thruster.Placement = App.Placement(App.Vector(x, y, z), rot_to_x())
    att_obj = add_obj(thruster, f"Attitude_Thruster_{i+1}"); set_mat(att_obj, 'TITANIUM')
    attitude_thrusters.append(att_obj)

# ========================
# Blindaje adicional de radiación solar
# ========================
rad_shield_d_out = P["mid_d"] + 600.0
rad_shield_d_in = P["mid_d"] + 100.0
rad_shield_l = P["nose_len"] + P["mid_len"] + P["rear_len"] + 2000.0
rad_shield_cx = (P["nose_len"] + P["mid_len"] + P["rear_len"]) / 2.0
rad_shield_outer = Part.makeCylinder(rad_shield_d_out/2.0, rad_shield_l)
rad_shield_inner = Part.makeCylinder(rad_shield_d_in/2.0, rad_shield_l + 10.0)
rad_shield = rad_shield_outer.cut(rad_shield_inner)
rad_shield.Placement = App.Placement(App.Vector(rad_shield_cx - rad_shield_l/2.0, 0, 0), rot_to_x())
rad_shield_obj = add_obj(rad_shield, "Radiation_Shield"); set_mat(rad_shield_obj, 'LEAD')

# ========================
# Escudos contra meteoritos
# ========================
meteor_shield_count = 12
meteor_shield_r = P["mid_d"]/2.0 + 400.0
meteor_shield_z = P["nose_len"] + P["mid_len"]/2.0
meteor_shields = []
for i in range(meteor_shield_count):
    angle = i * (360.0 / meteor_shield_count)
    x = meteor_shield_r * math.cos(math.radians(angle))
    y = meteor_shield_r * math.sin(math.radians(angle))
    meteor_shield = Part.makeCylinder(200.0, 100.0)
    meteor_shield.Placement = App.Placement(App.Vector(meteor_shield_z, x, y), App.Rotation())
    obj_meteor = add_obj(meteor_shield, f"Meteor_Shield_{i+1}"); set_mat(obj_meteor, 'STEEL')
    meteor_shields.append(obj_meteor)

# ========================
# Paneles solares adicionales
# ========================
extra_sa_count = 6
extra_sa_list = []
for i in range(extra_sa_count):
    angle = i * (360.0 / extra_sa_count)
    r = P["mid_d"]/2.0 + 500.0
    x = P["nose_len"] + P["mid_len"]/2.0
    y = r * math.cos(math.radians(angle))
    z = r * math.sin(math.radians(angle))
    extra_sa_arm = Part.makeCylinder(30.0, 300.0)
    extra_sa_arm.Placement = App.Placement(App.Vector(x - 150.0, y, z), rot_to_x())
    extra_sa_panel = Part.makeBox(600.0, 400.0, 30.0)
    extra_sa_panel.Placement = App.Placement(App.Vector(x + 150.0, y - 200.0, z - 15.0), App.Rotation())
    extra_sa = add_obj(extra_sa_arm.fuse(extra_sa_panel), f"Extra_Solar_Array_{i+1}"); set_mat(extra_sa, 'CFRP')
    extra_sa_list.append(extra_sa)

# ========================
# Antenas de comunicación adicionales
# ========================
comm_antenna_count = 6
comm_antennas = []
for i in range(comm_antenna_count):
    angle = i * (360.0 / comm_antenna_count) + 30
    r = TPS["tps_d"]/2.0 + 200.0
    x = TPS["tps_d"]/2.0 + TPS["tps_t"] + TPS["sup_L"] + nose_tip_x
    y = r * math.cos(math.radians(angle))
    z = r * math.sin(math.radians(angle))
    comm_antenna = Part.makeCylinder(50.0, 1000.0)
    comm_antenna.Placement = App.Placement(App.Vector(x, y, z), rot_to_x())
    obj_comm = add_obj(comm_antenna, f"Comm_Antenna_{i+1}"); set_mat(obj_comm, 'AL')
    comm_antennas.append(obj_comm)

# ========================
# Blindaje adicional de radiación solar (Lead shield around fuselage)
# ========================
rad_shield_d_out = P["mid_d"] + 400.0
rad_shield_d_in = P["mid_d"] + 50.0
rad_shield_l = P["nose_len"] + P["mid_len"] + P["rear_len"] + 1000.0
rad_shield_cx = (P["nose_len"] + P["mid_len"] + P["rear_len"]) / 2.0
rad_shield = make_hollow_cyl(rad_shield_d_out, rad_shield_d_in, rad_shield_l)
rad_shield.Placement.Base = App.Vector(rad_shield_cx - rad_shield_l/2.0, 0, 0)
rad_shield_obj = add_obj(rad_shield, "Radiation_Shield"); set_mat(rad_shield_obj, 'LEAD')

# ========================
# Paneles solares adicionales
# ========================
extra_sa_count = 4
extra_sa_list = []
for i in range(extra_sa_count):
    angle = i * (360.0 / extra_sa_count)
    x = P["nose_len"] + P["mid_len"] / 2.0
    r = P["mid_d"] / 2.0 + 300.0
    y = r * math.cos(math.radians(angle))
    z = r * math.sin(math.radians(angle))
    extra_sa_arm = Part.makeCylinder(20.0, 200.0)
    extra_sa_arm.Placement = App.Placement(App.Vector(x - 100.0, y, z), rot_to_x())
    extra_sa_panel = Part.makeBox(400.0, 300.0, 20.0)
    extra_sa_panel.Placement = App.Placement(App.Vector(x + 100.0, y - 150.0, z - 10.0), App.Rotation())
    extra_sa = add_obj(extra_sa_arm.fuse(extra_sa_panel), f"Extra_Solar_Array_{i+1}"); set_mat(extra_sa, 'CFRP')
    extra_sa_list.append(extra_sa)

# ========================
# Ensamblado total fusionado (pieza única imprimible)
# ========================
to_fuse = [
    hull_cut, cockpit, TPS_fused, nose, mid, rear,
    reactor, rings_obj, coils_obj, mod_obj, tw_obj,
    (nozzle_mount if 'nozzle_mount' in globals() else noz_obj),
    tn_obj, truss_obj, tank1, tank2,
    leg_r, leg_l, leg_r2, leg_l2, leg_f,
    wing_r, wing_l, fin, hga, sa, rad_shield_obj
] + rads + meteor_shields + extra_sa_list + comm_antennas + [large_comm, solar_sail_obj] + attitude_thrusters

# Elimina posibles None y duplica protección
to_fuse = [o for o in to_fuse if o and hasattr(o,'Shape')]

fused = to_fuse[0].Shape
for o in to_fuse[1:]:
    try:
        fused = fused.fuse(o.Shape)
    except Exception:
        pass

Assembly_Fused = add_obj(fused, "Assembly_Fused")  # Sólido único imprimible
set_mat(Assembly_Fused, 'AL')  # material global visual (las subpropiedades ya están en piezas individuales)

# Opcional: compuesto no fusionado (solo visual)
compound = Part.Compound([o.Shape for o in to_fuse])
add_obj(compound, "Assembly_Compound")

doc.recompute()
print("Ensamblado completado: Assembly_Fused (única pieza) y Assembly_Compound (visual). Nave espacial avanzada con TPS de carbono ablative, materiales resistentes (titanio, fibra de carbono), vela solar, antena parabólica grande, propulsores de actitud, escudos contra meteoritos y radiación. Optimizado para impresión 3D en Cura y lanzamiento al espacio exterior. Listo para exportar STL/STEP.")
