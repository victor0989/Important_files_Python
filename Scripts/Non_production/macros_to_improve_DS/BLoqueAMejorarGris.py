BLoqueAMejorarGris.py
import FreeCAD as App, FreeCADGui as Gui, Part, math

DOC_NAME = "ExtremeShield_Probe_Printable"
if App.ActiveDocument is None or App.ActiveDocument.Label != DOC_NAME:
    App.newDocument(DOC_NAME)
doc = App.ActiveDocument

# Parámetros base (inspirados en tu macro)
P = {
    "nose_len": 800.0, "nose_base_d": 1100.0, "nose_cap_d": 520.0,
    "mid_len": 2300.0, "mid_d": 1800.0,
    "rear_len": 1700.0, "rear_d": 2200.0,
    "hull_fillet_r": 20.0,  # fillet moderado para estabilidad de kernel

    # Propulsión
    "reactor_d": 1500.0, "reactor_l": 2100.0, "reactor_cx": 3400.0,
    "nozzle_throat_d": 520.0, "nozzle_exit_d": 2000.0, "nozzle_l": 1900.0,
    "nozzle_cx": 4500.0, "nozzle_fillet_r": 80.0,

    # Blindajes (extremos, macizos)
    "front_tps_r": 1600.0, "front_tps_t": 240.0, "front_tps_bevel": 90.0, "front_tps_gap": 120.0,
    "rear_tps_r": 1400.0, "rear_tps_t": 200.0, "rear_tps_bevel": 80.0, "rear_tps_gap": 80.0,
    "ring_guard_r": 2000.0, "ring_guard_w": 180.0, "ring_guard_t": 140.0,

    # Radiadores reforzados
    "rad_panel_w": 1100.0, "rad_panel_h": 80.0, "rad_panel_t": 28.0, "rad_panel_count": 8, "rad_spacing": 160.0,

    # Refuerzos
    "band_w": 150.0, "band_t": 32.0, "bands_n": 6, "band_fillet_r": 12.0,
    "truss_n": 12, "truss_tube_w": 160.0, "truss_len": 1200.0,

    # Detalles extra (sensores, mástil, antena)
    "mast_l": 1100.0, "mast_r": 48.0,
    "dish_r": 420.0,

    # Unificación final
    "make_unified_solid": True
}

def rot_to_x():
    return App.Rotation(App.Vector(0,1,0), 90)

def add_obj(shape, label, color=(0.70,0.70,0.72)):
    o = doc.addObject("Part::Feature", label)
    o.Shape = shape
    try:
        o.ViewObject.ShapeColor = color
        o.ViewObject.DisplayMode = "Shaded"
    except:
        pass
    return o

def safe_fillet(shape, r):
    try:
        return shape.makeFillet(r, shape.Edges)
    except:
        return shape

def make_cyl_x(d, L, cx=0, cy=0, cz=0):
    c = Part.makeCylinder(d/2.0, L)
    c.Placement = App.Placement(App.Vector(cx - L/2.0, cy, cz), rot_to_x())
    return c

def make_cone_x(d1, d2, L, cx=0, cy=0, cz=0):
    c = Part.makeCone(d1/2.0, d2/2.0, L)
    c.Placement = App.Placement(App.Vector(cx - L/2.0, cy, cz), rot_to_x())
    return c

# Fuselaje macizo (sin offset interno)
def make_nose_loft():
    sections = []
    radii = [P["nose_base_d"]/2.0, 520.0, 300.0, P["nose_cap_d"]/2.0]
    xpos   = [0, P["nose_len"]*0.35, P["nose_len"]*0.7, P["nose_len"]]
    for r, x in zip(radii, xpos):
        sections.append(Part.makeCircle(r, App.Vector(x,0,0), App.Vector(1,0,0)))
    return Part.makeLoft(sections, True)

nose = make_nose_loft()
mid  = make_cyl_x(P["mid_d"], P["mid_len"], cx=P["nose_len"])
rear = make_cyl_x(P["rear_d"], P["rear_len"], cx=P["nose_len"] + P["mid_len"])
fuselage = safe_fillet(nose.fuse(mid).fuse(rear), P["hull_fillet_r"])
hull_obj = add_obj(fuselage, "Hull_Solid")

# Blindaje frontal masivo (disco + bisel)
front_disc  = Part.makeCylinder(P["front_tps_r"], P["front_tps_t"])
front_bevel = Part.makeCone(P["front_tps_r"], P["front_tps_r"] - P["front_tps_bevel"], P["front_tps_bevel"])
front_tps   = front_disc.fuse(front_bevel)
front_tps.Placement = App.Placement(App.Vector(-P["front_tps_t"] - P["front_tps_gap"], 0, 0), rot_to_x())
front_tps = safe_fillet(front_tps, 4.0)
front_tps_obj = add_obj(front_tps, "Front_TPS", color=(0.50,0.52,0.54))

# Blindaje trasero (disco + bisel) alrededor de la tobera
rear_disc  = Part.makeCylinder(P["rear_tps_r"], P["rear_tps_t"])
rear_bevel = Part.makeCone(P["rear_tps_r"], P["rear_tps_r"] - P["rear_tps_bevel"], P["rear_tps_bevel"])
rear_tps   = rear_disc.fuse(rear_bevel)
rear_x = P["nose_len"] + P["mid_len"] + P["rear_len"] + P["rear_tps_gap"]
rear_tps.Placement = App.Placement(App.Vector(rear_x, 0, 0), rot_to_x())
rear_tps = safe_fillet(rear_tps, 4.0)
rear_tps_obj = add_obj(rear_tps, "Rear_TPS", color=(0.50,0.52,0.54))

# Anillo protector alrededor del rear
ring_outer = Part.makeCylinder(P["ring_guard_r"], P["ring_guard_w"])
ring_inner = Part.makeCylinder(P["ring_guard_r"] - P["ring_guard_t"], P["ring_guard_w"] + 0.2)
ring = ring_outer.cut(ring_inner)
ring.Placement = App.Placement(App.Vector(P["nose_len"] + P["mid_len"] + P["rear_len"] - P["ring_guard_w"]/2.0, 0, 0), rot_to_x())
ring_obj = add_obj(ring, "Rear_Guard_Ring", color=(0.58,0.60,0.62))

# Propulsión (garganta + tobera) maciza
throat = make_cyl_x(P["nozzle_throat_d"], 260.0, cx=P["nozzle_cx"] - P["nozzle_l"]/2.0 - 130.0)
cone   = make_cone_x(P["nozzle_throat_d"], P["nozzle_exit_d"], P["nozzle_l"], cx=P["nozzle_cx"])
cone   = safe_fillet(cone, P["nozzle_fillet_r"])
nozzle = throat.fuse(cone)
nozzle_obj = add_obj(nozzle, "Main_Nozzle", color=(0.68,0.70,0.72))

reactor_core = make_cyl_x(P["reactor_d"], P["reactor_l"], cx=P["reactor_cx"])
reactor_obj  = add_obj(reactor_core, "Reactor_Core", color=(0.66,0.68,0.70))

# Radiadores laterales reforzados (placas macizas)
rads = []
for i in range(P["rad_panel_count"]):
    z = -P["rad_panel_h"]/2.0 + i*P["rad_spacing"]
    r = Part.makeBox(P["rad_panel_w"], P["rad_panel_t"], P["rad_panel_h"])
    r.Placement = App.Placement(App.Vector(P["nose_len"] + P["mid_len"] + 80.0, -P["rear_d"]/2.0 - 90.0, z), App.Rotation())
    rads.append(safe_fillet(r, 2.0))
rad_union = rads[0]
for r in rads[1:]:
    rad_union = rad_union.fuse(r)
rad_obj = add_obj(rad_union, "Radiator_Panels", color=(0.62,0.64,0.68))

# Bandas estructurales
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
bands_obj  = add_obj(band_union, "Structural_Bands", color=(0.64,0.64,0.66))

# Truss simplificado (volumen macizo)
truss_parts = []
for _ in range(P["truss_n"]):
    t = Part.makeBox(P["truss_len"], P["truss_tube_w"], P["truss_tube_w"])
    truss_parts.append(t)
truss_shape = truss_parts[0]
for t in truss_parts[1:]:
    truss_shape = truss_shape.fuse(t)
truss_obj = add_obj(truss_shape, "Truss_Armor", color=(0.58,0.58,0.60))

# Mástil y antena (macizos)
mast = make_cyl_x(P["mast_r"]*2, P["mast_l"], cx=P["nose_len"] + P["mid_len"]/2.0)
mast_obj = add_obj(mast, "Mast", color=(0.60,0.62,0.64))

dish = Part.makeCone(0, P["dish_r"], 50.0)
dish.Placement = App.Placement(App.Vector(P["nose_len"] + P["mid_len"]/2.0 + P["mast_l"], 0, 0), rot_to_x())
dish_obj = add_obj(dish, "Antenna_Dish", color=(0.65,0.67,0.70))

# Unificación final en un único sólido
if P["make_unified_solid"]:
    objs = [hull_obj, front_tps_obj, rear_tps_obj, ring_obj,
            reactor_obj, nozzle_obj, rad_obj, bands_obj, truss_obj, mast_obj, dish_obj]
    final = objs[0].Shape
    for o in objs[1:]:
        final = final.fuse(o.Shape)
    final_obj = add_obj(final, "Unified_ExtremeShield_Probe", color=(0.72,0.72,0.74))

doc.recompute()
