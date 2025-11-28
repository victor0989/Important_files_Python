Verde_masMetal_masBLindajeMasSateliteOscuro.py
import FreeCAD as App,FreeCADGui as Gui,Part,math

doc_name="CassiniUltra_HeavySatellite_RadiationShield_SOLID_INTEGRATED_ELEC_EXTENDED"
doc = App.ActiveDocument if App.ActiveDocument and App.ActiveDocument.Label==doc_name else App.newDocument(doc_name)
doc = App.ActiveDocument

# ---------------- PARÁMETROS BASE (tu referencia) ----------------
P={"tank_len":11000.0,"tank_d":6000.0,"hull_t":85.0,"hull_outer_d":7000.0,"liner_t":36.0,
   "tps_front_R":4200.0,"tps_front_t":220.0,"tps_offset":780.0,"shoulder_len":1600.0,
   "bus_len":5200.0,"bus_outer_d":6800.0,"bus_inner_d":5600.0,
   "hga_R":2800.0,"hga_t":32.0,"hga_offset":880.0,"hga_mast_len":2000.0,"hga_mast_d":320.0,
   "rtg_box_l":1600.0,"rtg_box_w":920.0,"rtg_box_t":420.0,"rtg_arm_len":1650.0,"rtg_arm_d":320.0,"rtg_arm_offset_z":1400.0,
   "throat_d":900.0,"exit_d":5600.0,"nozzle_len":4600.0,
   "gimbal_ring_ro":2800.0,"gimbal_ring_t":160.0,
   "bulkhead_t":90.0,
   "frame_ring_d":4600.0,"frame_ring_t":140.0,"frame_step":800.0,
   "rcs_thr_d":520.0,"rcs_thr_len":900.0,"rcs_ring_R":4200.0,"rcs_count":12,
   "aux_thr_d":1200.0,"aux_thr_len":1800.0,"aux_thr_ring_R":4800.0,"aux_thr_count":12,
   "rad_shield_inner_d":7600.0,"rad_shield_t":220.0,"rad_shield_gap":120.0,"rad_shield_len":7600.0,
   "whipple_t":80.0,"whipple_gap":300.0,
   "inst_bay_len":2400.0,"inst_bay_d":4800.0,
   "mag_boom_len":5200.0,"mag_boom_d":220.0,"star_boom_len":3800.0,"star_boom_d":180.0,
   "fin_len":1600.0,"fin_w":940.0,"fin_t":180.0,
   "ion_thr_d":380.0,"ion_thr_len":1100.0,"ion_ring_R":3600.0,"ion_count":16,
   "hall_thr_d":720.0,"hall_thr_len":1400.0,"hall_arm_len":1800.0,
   "rad_len":3200.0,"rad_w":1400.0,"rad_t":90.0,"rad_z":1800.0,
   "parker_shield_R":3200.0,"engine_bay_len":2800.0}

# ---------------- PARÁMETROS NUEVOS (ampliación) ----------------
A={
   # Cúpula superior tipo casquete
   "dome_R": 2400.0, "dome_t": 45.0, "dome_offset": 600.0,
   # Patas + pads
   "leg_n": 4, "leg_len": 3000.0, "leg_d": 280.0, "leg_base_R": 3200.0, "leg_base_cx": -600.0,
   "pad_d": 1600.0, "pad_t": 120.0, "pad_drop": 2600.0,
   # Antena parabólica de malla
   "dish_R": 2200.0, "dish_t": 40.0, "dish_mast_len": 1800.0, "dish_mast_d": 200.0, "dish_cx": 800.0, "dish_cy": 3600.0, "dish_cz": 1600.0,
   # Tanques auxiliares (esférico + cilíndrico)
   "aux_sphere_R": 1400.0, "aux_sphere_cx": 900.0, "aux_sphere_cy": -3600.0, "aux_sphere_cz": 1200.0,
   "aux_cyl_d": 1800.0, "aux_cyl_len": 2600.0, "aux_cyl_cx": 1200.0, "aux_cyl_cy": 3400.0, "aux_cyl_cz": -800.0,
   # Paneles y rejillas en bus (indentaciones)
   "panel_w": 1200.0, "panel_t": 60.0, "panel_h": 1600.0,
   # Cluster de 3 motores grandes + anillo de auxiliares (cola)
   "core_throat": 1400.0, "core_exit": 3000.0, "core_len": 2600.0,
   "tri_throat": 1200.0, "tri_exit": 2600.0, "tri_len": 2400.0, "tri_R": 2000.0, "tri_count": 3,
   "aux_count": 12, "aux_d1": 400.0, "aux_d2": 800.0, "aux_len": 1000.0, "aux_R": 3200.0,
   "engine_ring_d": 5000.0, "engine_ring_t": 200.0
}

# ---------------- UTILIDADES ----------------
X_AXIS=App.Vector(1,0,0);Y_AXIS=App.Vector(0,1,0);Z_AXIS=App.Vector(0,0,1)
rot_to_x=lambda:App.Rotation(Y_AXIS,90)

def add_obj(s,n):
    o=doc.addObject("Part::Feature",n); o.Shape=s; return o

def color(o,rgb):
    if hasattr(o,"ViewObject"): o.ViewObject.ShapeColor=rgb

def cyl_x(d,L,cx=0,cy=0,cz=0):
    s=Part.makeCylinder(d/2.0,L)
    s.Placement=App.Placement(App.Vector(cx-L/2.0,cy,cz),rot_to_x())
    return s

def cone_x(d1,d2,L,cx=0,cy=0,cz=0):
    s=Part.makeCone(d1/2.0,d2/2.0,L)
    s.Placement=App.Placement(App.Vector(cx-L/2.0,cy,cz),rot_to_x())
    return s

def sphere_section(R,t,cx):
    so,si=Part.makeSphere(R),Part.makeSphere(R-t)
    so.Placement=si.Placement=App.Placement(App.Vector(cx,0,0),App.Rotation())
    box=Part.makeBox(2*R,4*R,4*R,App.Vector(cx,-2*R,-2*R))
    return so.common(box).cut(si.common(box))

def sphere_at(R,cx=0,cy=0,cz=0):
    s=Part.makeSphere(R)
    s.Placement=App.Placement(App.Vector(cx,cy,cz),App.Rotation())
    return s

def box_at(l,w,t,x,y,z):
    b=Part.makeBox(l,w,t); b.translate(App.Vector(x,y,z)); return b

def refine_shape(shp):
    try: return shp.removeSplitter()
    except Exception: return shp

def fuse_many(lst):
    if not lst: return None
    s=lst[0]
    for e in lst[1:]:
        try: s=s.fuse(e)
        except: pass
    return refine_shape(s)

# ---------------- BASE ORIGINAL ----------------
tank_cx=0.0
tank=cyl_x(P["tank_d"],P["tank_len"],cx=tank_cx)
liner=cyl_x(P["tank_d"]-2*P["liner_t"],P["tank_len"]-2*P["liner_t"],cx=tank_cx)
hull=cyl_x(P["hull_outer_d"],P["tank_len"],cx=tank_cx).cut(tank)
bus_shell=cyl_x(P["bus_outer_d"],P["bus_len"],cx=tank_cx).cut(cyl_x(P["bus_inner_d"],P["bus_len"]-2*P["hull_t"],cx=tank_cx))

cap_center_x=tank_cx+P["tank_len"]/2.0+P["tps_offset"]
tps_front=sphere_section(P["tps_front_R"],P["tps_front_t"],cap_center_x)
shoulder_cx=cap_center_x-P["shoulder_len"]/2.0
shoulder=cone_x(2*P["tps_front_R"],P["hull_outer_d"],P["shoulder_len"],cx=shoulder_cx)
parker=cyl_x(P["parker_shield_R"]*2.0,240.0,cx=cap_center_x+P["tps_offset"]+220.0)

payload_cx=tank_cx+P["tank_len"]/2.0-P["bus_len"]/2.0
hga_center_x=cap_center_x-P["hga_offset"]
hga_dish=sphere_section(P["hga_R"],P["hga_t"],hga_center_x)
hga_mast=cyl_x(P["hga_mast_d"],P["hga_mast_len"],cx=hga_center_x-P["hga_mast_len"]/2.0)
pallet=box_at(P["inst_bay_len"],P["inst_bay_d"],P["bulkhead_t"],payload_cx,-P["inst_bay_d"]/2.0,-P["hull_outer_d"]/2.0)

rtg_solids=[]
for sgn in(+1,-1):
    arm=cyl_x(P["rtg_arm_d"],P["rtg_arm_len"],cx=payload_cx-400.0,cy=sgn*(P["bus_outer_d"]/2.0+600.0),cz=P["rtg_arm_offset_z"])
    box=box_at(P["rtg_box_l"],P["rtg_box_w"],P["rtg_box_t"],payload_cx-400.0+P["rtg_arm_len"],sgn*(P["bus_outer_d"]/2.0+600.0-P["rtg_box_w"]/2.0),P["rtg_arm_offset_z"]-P["rtg_box_t"]/2.0)
    rtg_solids+=[arm,box]

mag_boom=cyl_x(P["mag_boom_d"],P["mag_boom_len"],cx=payload_cx+300.0,cy=(P["bus_outer_d"]/2.0+300.0),cz=300.0)
star_boom=cyl_x(P["star_boom_d"],P["star_boom_len"],cx=payload_cx+200.0,cy=-(P["bus_outer_d"]/2.0+200.0),cz=250.0)

rcs_solids=[]
for i in range(P["rcs_count"]):
    ang=2*math.pi*i/P["rcs_count"]
    y=P["rcs_ring_R"]*math.cos(ang); z=P["rcs_ring_R"]*math.sin(ang)
    rcs_solids.append(cyl_x(P["rcs_thr_d"],P["rcs_thr_len"],cx=payload_cx-300.0,cy=y,cz=z))

aux_solids=[]
for i in range(P["aux_thr_count"]):
    ang=2*math.pi*i/P["aux_thr_count"]
    y=P["aux_thr_ring_R"]*math.cos(ang); z=P["aux_thr_ring_R"]*math.sin(ang)
    aux_solids.append(cyl_x(P["aux_thr_d"],P["aux_thr_len"],cx=payload_cx-900.0,cy=y,cz=z))

hall_solids=[]
for sgn in(+1,-1):
    hall_solids.append(cyl_x(P["hall_thr_d"],P["hall_thr_len"],cx=payload_cx+P["hall_arm_len"],cy=sgn*(P["hull_outer_d"]/2.0+900.0),cz=600.0))

frame_rings=[]; frame_count=int(P["bus_len"]//P["frame_step"])
for i in range(frame_count+1):
    x=tank_cx-P["bus_len"]/2.0+i*P["frame_step"]
    ring=Part.makeTorus(P["frame_ring_d"]/2.0,P["frame_ring_t"]/2.0)
    ring.Placement=App.Placement(App.Vector(x,0,0),App.Rotation(X_AXIS,90))
    frame_rings.append(ring)

nozzle_cx=tank_cx-P["tank_len"]/2.0-P["nozzle_len"]/2.0
nozzle=cone_x(P["throat_d"],P["exit_d"],P["nozzle_len"],cx=nozzle_cx)
gimbal_ring=Part.makeTorus(P["gimbal_ring_ro"],P["gimbal_ring_t"]/2.0)
gimbal_ring.Placement=App.Placement(App.Vector(nozzle_cx+P["nozzle_len"]/2.0,0,0),App.Rotation(X_AXIS,90))

rad_shield=cyl_x(P["rad_shield_inner_d"]+2*(P["rad_shield_t"]+P["rad_shield_gap"]),P["rad_shield_len"],cx=payload_cx).cut(
           cyl_x(P["rad_shield_inner_d"],P["rad_shield_len"]-2*P["rad_shield_t"],cx=payload_cx))
whipple_shell=cyl_x(P["rad_shield_inner_d"]+2*(P["rad_shield_t"]+P["whipple_gap"]),P["rad_shield_len"],cx=payload_cx).cut(
              cyl_x(P["rad_shield_inner_d"]+2*(P["rad_shield_t"]+P["whipple_gap"])-P["whipple_t"],P["rad_shield_len"]-2*P["whipple_t"],cx=payload_cx))
inst_bay=cyl_x(P["inst_bay_d"],P["inst_bay_len"],cx=payload_cx)

rads=[]
for sgn in(+1,-1):
    rads.append(box_at(P["rad_len"],P["rad_w"],P["rad_t"],payload_cx-600.0, sgn*(P["bus_outer_d"]/2.0+P["rad_w"]/2.0), P["rad_z"]))

fins=[]
for sgn in(+1,-1):
    fins.append(box_at(P["fin_len"],P["fin_t"],P["fin_w"],payload_cx-200.0, sgn*(P["hull_outer_d"]/2.0+100.0), -P["fin_w"]/2.0))

# ---------------- AMPLIACIÓN NUEVA ----------------
# Cúpula superior
dome_cx = tank_cx + P["tank_len"]/2.0 + A["dome_offset"]
dome_outer = sphere_at(A["dome_R"], cx=dome_cx)
dome_inner = sphere_at(A["dome_R"]-A["dome_t"], cx=dome_cx)
cut_box = Part.makeBox(2*A["dome_R"], 4*A["dome_R"], 4*A["dome_R"], App.Vector(dome_cx,-2*A["dome_R"],-2*A["dome_R"]))
dome_shell = dome_outer.common(cut_box).cut(dome_inner.common(cut_box))

# Patas y pads
legs=[]; pads=[]
for i in range(A["leg_n"]):
    ang = i*(360.0/A["leg_n"])
    y = A["leg_base_R"]*math.cos(math.radians(ang))
    z = A["leg_base_R"]*math.sin(math.radians(ang))
    leg = cyl_x(A["leg_d"], A["leg_len"], cx=A["leg_base_cx"], cy=y*0.98, cz=z*0.98)
    legs.append(leg)
    pad = cyl_x(A["pad_d"], A["pad_t"], cx=A["leg_base_cx"]-A["pad_drop"], cy=y, cz=z)
    pads.append(pad)

# Antena parabólica
dish_center_x = payload_cx + A["dish_cx"]
dish_mast = cyl_x(A["dish_mast_d"], A["dish_mast_len"], cx=dish_center_x, cy=A["dish_cy"], cz=A["dish_cz"])
dish = sphere_section(A["dish_R"], A["dish_t"], dish_center_x)
# recortar a casquete parabólico simple (usamos esfera por robustez visual)
dish_cut = Part.makeBox(2*A["dish_R"], 4*A["dish_R"], 4*A["dish_R"], App.Vector(dish_center_x,-2*A["dish_R"], -A["dish_R"]))
dish_shell = dish.common(dish_cut)

# Tanques auxiliares
aux_sphere = sphere_at(A["aux_sphere_R"], cx=A["aux_sphere_cx"], cy=A["aux_sphere_cy"], cz=A["aux_sphere_cz"])
aux_cyl = cyl_x(A["aux_cyl_d"], A["aux_cyl_len"], cx=A["aux_cyl_cx"], cy=A["aux_cyl_cy"], cz=A["aux_cyl_cz"])

# Paneles en bus (indentaciones / placas)
panels=[]
for px,py,pz in [
    (payload_cx+400.0,  P["bus_outer_d"]/2.0+30.0,   -800.0),
    (payload_cx-200.0,  P["bus_outer_d"]/2.0+30.0,    600.0),
    (payload_cx-900.0,  P["bus_outer_d"]/2.0+30.0,   -300.0),
]:
    panel = box_at(A["panel_w"],A["panel_t"],A["panel_h"], px, py, pz)
    panels.append(panel)

# Cluster de motores en la base (cola)
engine_base_x = tank_cx - P["tank_len"]/2.0 - 600.0

core_noz = cone_x(A["core_throat"], A["core_exit"], A["core_len"], cx=engine_base_x)

tri_nozz=[]
for i in range(A["tri_count"]):
    ang = i*(360.0/A["tri_count"])
    y = A["tri_R"]*math.cos(math.radians(ang))
    z = A["tri_R"]*math.sin(math.radians(ang))
    noz = cone_x(A["tri_throat"], A["tri_exit"], A["tri_len"], cx=engine_base_x, cy=y, cz=z)
    tri_nozz.append(noz)

aux_thr=[]
for i in range(A["aux_count"]):
    ang = i*(360.0/A["aux_count"])
    y = A["aux_R"]*math.cos(math.radians(ang))
    z = A["aux_R"]*math.sin(math.radians(ang))
    thr = cone_x(A["aux_d1"], A["aux_d2"], A["aux_len"], cx=engine_base_x-200.0, cy=y, cz=z)
    aux_thr.append(thr)

engine_ring = cyl_x(A["engine_ring_d"], A["engine_ring_t"], cx=engine_base_x)

# ---------------- ENSAMBLAJE ----------------
assembly = fuse_many(
    [tank,liner,hull,bus_shell,tps_front,shoulder,parker,hga_dish,hga_mast,pallet,
     mag_boom,star_boom,rad_shield,whipple_shell,inst_bay] +
    rtg_solids + rcs_solids + aux_solids + hall_solids + frame_rings + rads + fins +
    [dome_shell] + legs + pads + [dish_mast, dish_shell] + [aux_sphere, aux_cyl] + panels +
    [engine_ring, core_noz] + tri_nozz + aux_thr
)

obj = add_obj(assembly,"CassiniUltraHeavy_Integrated_Extended")
color(obj,(0.7,0.95,0.85))  # mint argón

# ---------------- VISTA ----------------
doc.recompute()
try:
    Gui.SendMsgToActiveView("ViewFit")
    Gui.ActiveDocument.ActiveView.viewAxonometric()
except: pass