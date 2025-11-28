SateliteSmallPrintableGrisMejorar.py
import FreeCAD as App, FreeCADGui as Gui, Part, math

DOC_NAME = "ParkerProbe_Printable"
if App.ActiveDocument is None or App.ActiveDocument.Label != DOC_NAME:
    App.newDocument(DOC_NAME)
doc = App.ActiveDocument

P = {
    # Fuselaje
    "nose_len": 420.0, "nose_base_d": 1350.0, "nose_cap_d": 620.0,
    "mid_len": 1450.0, "mid_d": 1500.0,
    "rear_len": 900.0,  "rear_d": 1650.0,
    "hull_fillet_r": 20.0,  # fillet reducido para robustez

    # Antena y mástil
    "mast_l": 900.0, "mast_r": 60.0,
    "dish_r": 520.0, "dish_offset": 180.0,

    # Escudo térmico
    "tps_r": 1100.0, "tps_t": 85.0,
    "tps_gap": 80.0, "tps_bevel": 24.0,
    "tps_bolt_r": 26.0, "tps_bolt_n": 16,

    # Paneles solares
    "sa_panel_w": 900.0, "sa_panel_h": 1300.0, "sa_panel_t": 24.0,
    "sa_cell_w": 80.0, "sa_cell_h": 80.0, "sa_cell_gap": 6.0,
    "sa_pitch_deg": 18.0,

    # Radiadores
    "rad_w": 1200.0, "rad_h": 40.0, "rad_t": 20.0, "rad_n": 6, "rad_spacing": 140.0,

    # Propulsión
    "reactor_d": 1100.0, "reactor_l": 1200.0, "reactor_cx": 2200.0,
    "nozzle_throat_d": 420.0, "nozzle_exit_d": 1100.0, "nozzle_l": 1100.0,
    "nozzle_cx": 3100.0, "nozzle_fillet_r": 80.0,

    # Refuerzos
    "band_w": 110.0, "band_t": 20.0, "bands_n": 4, "band_fillet_r": 12.0,
    "truss_n": 8, "truss_tube_w": 120.0, "truss_len": 900.0,

    # Unificación final
    "make_unified_solid": True
}

def rot_to_x(): return App.Rotation(App.Vector(0,1,0),90)
def add_obj(shape,label,color=(0.70,0.70,0.72)):
    o=doc.addObject("Part::Feature",label);o.Shape=shape
    try:o.ViewObject.ShapeColor=color;o.ViewObject.DisplayMode="Shaded"
    except:pass;return o
def safe_fillet(shape,r):
    try:return shape.makeFillet(r,shape.Edges)
    except:return shape
def make_cyl_x(d,L,cx=0,cy=0,cz=0):
    c=Part.makeCylinder(d/2.0,L)
    c.Placement=App.Placement(App.Vector(cx-L/2.0,cy,cz),rot_to_x());return c
def make_cone_x(d1,d2,L,cx=0,cy=0,cz=0):
    c=Part.makeCone(d1/2.0,d2/2.0,L)
    c.Placement=App.Placement(App.Vector(cx-L/2.0,cy,cz),rot_to_x());return c

# Panel solar con mosaico de celdas en rebaje
def make_panel_mosaic(w,h,t,cell_w,cell_h,gap,recess=0.6):
    nx=int((w-gap)/(cell_w+gap));ny=int((h-gap)/(cell_h+gap))
    panel=Part.makeBox(w,t,h)
    for i in range(nx):
        for j in range(ny):
            x=gap+i*(cell_w+gap);z=gap+j*(cell_h+gap)
            cell=Part.makeBox(cell_w,recess,cell_h)
            cell.Placement=App.Placement(App.Vector(x,t-recess,z),App.Rotation())
            panel=panel.cut(cell)
    return panel

# --- Construcción ---
# Fuselaje macizo
sections=[];radii=[P["nose_base_d"]/2.0,560.0,360.0,P["nose_cap_d"]/2.0]
xpos=[0,P["nose_len"]*0.38,P["nose_len"]*0.75,P["nose_len"]]
for r,x in zip(radii,xpos):
    sections.append(Part.makeCircle(r,App.Vector(x,0,0),App.Vector(1,0,0)))
nose=Part.makeLoft(sections,True)
mid=make_cyl_x(P["mid_d"],P["mid_len"],cx=P["nose_len"])
rear=make_cyl_x(P["rear_d"],P["rear_len"],cx=P["nose_len"]+P["mid_len"])
fuse=safe_fillet(nose.fuse(mid).fuse(rear),P["hull_fillet_r"])
hull=fuse
hull_obj=add_obj(hull,"Hull")

# TPS
tps_disc=Part.makeCylinder(P["tps_r"],P["tps_t"])
tps_bevel=Part.makeCone(P["tps_r"],P["tps_r"]-P["tps_bevel"],P["tps_bevel"])
tps=tps_disc.fuse(tps_bevel)
tps.Placement=App.Placement(App.Vector(-P["tps_t"]-P["tps_gap"],0,0),rot_to_x())
for k in range(P["tps_bolt_n"]):
    ang=2*math.pi*k/P["tps_bolt_n"]
    by=(P["tps_r"]-120.0)*math.cos(ang);bz=(P["tps_r"]-120.0)*math.sin(ang)
    bolt=make_cyl_x(P["tps_bolt_r"]*2,28.0,cx=-P["tps_gap"]-18.0,cy=by,cz=bz)
    tps=tps.fuse(bolt)
tps_obj=add_obj(tps,"TPS")

# Mástil y antena
mast=make_cyl_x(P["mast_r"]*2,P["mast_l"],cx=P["nose_len"]*0.35)
mast_obj=add_obj(mast,"Mast")
dish=Part.makeCone(0,P["dish_r"],60.0)
dish.Placement=App.Placement(App.Vector(P["nose_len"]*0.35+P["mast_l"]+P["dish_offset"],0,0),rot_to_x())
dish_obj=add_obj(dish,"Dish")

# Paneles solares
hinge_x=P["nose_len"]+P["mid_len"]*0.45
panel_L=make_panel_mosaic(P["sa_panel_w"],P["sa_panel_h"],P["sa_panel_t"],
                          P["sa_cell_w"],P["sa_cell_h"],P["sa_cell_gap"])
panel_R=panel_L.copy()
rot_pitch=App.Rotation(App.Vector(0,0,1),P["sa_pitch_deg"])
panel_L.Placement=App.Placement(App.Vector(hinge_x,-P["mid_d"]/2.0-30.0,-P["sa_panel_h"]/2.0),rot_pitch)
panel_R.Placement=App.Placement(App.Vector(hinge_x,+P["mid_d"]/2.0+30.0,-P["sa_panel_h"]/2.0),rot_pitch)
sa_L_obj=add_obj(panel_L,"SolarArray_L",(0.24,0.26,0.30))
sa_R_obj=add_obj(panel_R,"SolarArray_R",(0.24,0.26,0.30))

# Radiadores
rads=[]
for i in range(P["rad_n"]):
    z=-P["rad_h"]/2.0+i*P["rad_spacing"]
    r=Part.makeBox(P["rad_w"],P["rad_t"],P["rad_h"])
    r.Placement=App.Placement(App.Vector(P["nose_len"]+P["mid_len"]+60.0,-P["rear_d"]/2.0-80.0,z),App.Rotation())
    rads.append(safe_fillet(r,2.0))
rad_union=rads[0]
for r in rads[1:]: rad_union=rad_union.fuse(r)
rad_obj=add_obj(rad_union,"Radiators",(0.62,0.64,0.68))

# Propulsión
throat = make_cyl_x(P["nozzle_throat_d"], 220.0,
                    cx=P["nozzle_cx"] - P["nozzle_l"]/2.0 - 110.0)
cone = make_cone_x(P["nozzle_throat_d"], P["nozzle_exit_d"], P["nozzle_l"],
                   cx=P["nozzle_cx"])
cone = safe_fillet(cone, P["nozzle_fillet_r"])
nozzle = throat.fuse(cone)
nozzle_obj = add_obj(nozzle, "Main_Nozzle", color=(0.74,0.74,0.76))

reactor_core = make_cyl_x(P["reactor_d"], P["reactor_l"], cx=P["reactor_cx"])
reactor_obj = add_obj(reactor_core, "Reactor_Core", color=(0.68,0.70,0.72))

# Refuerzos: bandas
bands = []
pitch = (P["mid_len"] + P["rear_len"] - 2*P["band_w"]) / max(1, P["bands_n"])
for i in range(P["bands_n"]):
    b = Part.makeCylinder(P["mid_d"]/2.0 + P["band_t"], P["band_w"])
    b.Placement = App.Placement(App.Vector(P["nose_len"] + i*pitch, 0, 0), rot_to_x())
    bands.append(b)
band_union = bands[0]
for b in bands[1:]:
    band_union = band_union.fuse(b)
band_union = safe_fillet(band_union, P["band_fillet_r"])
bands_obj = add_obj(band_union, "Structural_Bands", color=(0.64,0.64,0.66))

# Refuerzos: truss simplificado
truss_parts = []
for _ in range(P["truss_n"]):
    t = Part.makeBox(P["truss_len"], P["truss_tube_w"], P["truss_tube_w"])
    truss_parts.append(t)
truss = truss_parts[0]
for t in truss_parts[1:]:
    truss = truss.fuse(t)
truss_obj = add_obj(truss, "Truss_Armor", color=(0.58,0.58,0.60))

# --- Unificación final ---
if P["make_unified_solid"]:
    objs = [hull_obj, tps_obj, mast_obj, dish_obj,
            sa_L_obj, sa_R_obj, rad_obj,
            nozzle_obj, reactor_obj, bands_obj, truss_obj]
    final = objs[0].Shape
    for o in objs[1:]:
        final = final.fuse(o.Shape)
    final_obj = add_obj(final, "Unified_Probe", color=(0.72,0.72,0.74))

doc.recompute()
