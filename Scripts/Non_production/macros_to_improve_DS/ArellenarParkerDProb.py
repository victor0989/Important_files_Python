ArellenarParkerDProb.py
# FreeCAD 0.20+ | Workbenches: Part, TechDraw
# DFD spacecraft con TPS estilo Parker Solar Probe, ortográficas con cotas y sección.
# Víctor: ajusta PARAMS y ejecuta; volúmenes/masas y vistas se recalculan.

import FreeCAD as App
import FreeCADGui as Gui
import Part, math
import TechDraw

DOC = "DFD_Parker_Improved"
try:
    App.closeDocument(DOC)
except Exception:
    pass
doc = App.newDocument(DOC)

# -------------------------
# PARAMS
# -------------------------
P = {
    # Global
    "length_total": 7.5,                 # m
    "blue": (0.10, 0.40, 0.85),

    # TPS (Thermal Protection System) estilo Parker
    "tps_diameter": 3.5,                 # m (circular)
    "tps_thickness_center": 0.11,        # m
    "tps_edge_taper": 0.09,              # m
    "tps_facet_count": 16,               # segmentos de bisel
    "tps_boss_diameter": 0.35,           # m
    "tps_spoke_count": 6,                # cercha tipo araña

    # Separación TPS -> bus
    "gap_tps_bus": 0.18,                 # m

    # Bus hexagonal
    "bus_flat": 1.60,                    # m
    "bus_length": 3.2,                   # m
    "bus_wall": 0.030,                    # m
    "bus_chamfer": 0.025,                # m
    "bus_panel_groove_depth": 0.01,      # m
    "bus_panel_groove_pitch": 0.25,      # m

    # Módulos internos
    "mod_gap": 0.05,
    "mod_fuel_len": 1.6,
    "mod_ctrl_len": 0.7,
    "mod_pwr_len": 1.0,

    # DFD
    "dfd_outer_dia": 2.5,
    "dfd_length": 1.4,
    "dfd_core_dia": 0.8,
    "dfd_throat_dia": 0.6,
    "dfd_exit_dia": 1.75,
    "dfd_ring_count": 4,
    "dfd_ring_radial": 0.06,
    "dfd_ring_gap": 0.05,

    # Radiadores
    "rad_len": 2.2,
    "rad_root_height": 0.75,
    "rad_tip_height": 0.45,
    "rad_thk": 0.016,
    "rad_rib_pitch": 0.18,
    "rad_rib_depth": 0.006,

    # Arrays solares
    "sa_panel_len": 1.4,
    "sa_panel_w": 0.6,
    "sa_thk": 0.014,
    "sa_boom_len": 0.55,
    "sa_yaw_deg": 35,
    "sa_pitch_deg": -10,

    # Detalles
    "hga_dia": 0.6,
    "hga_depth": 0.18,
    "rcs_pod_d": 0.16,
    "rcs_pod_len": 0.22,

    # Materiales
    "rho_tps": 1700,
    "rho_bus": 2700,
    "rho_modules": 4500,
    "rho_dfd": 8200,
    "rho_panel": 1800,
    "rho_radiator": 1850,
    "rho_misc": 2700,
}

# -------------------------
# Utilidades
# -------------------------
def add_obj(shape, name, color=None):
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    try:
        if App.GuiUp:
            if color:
                obj.ViewObject.ShapeColor = color
            else:
                obj.ViewObject.ShapeColor = P["blue"]
            obj.ViewObject.LineWidth = 2
    except Exception:
        pass
    return obj

def assign_props(o, rho, mat):
    vol = o.Shape.Volume
    mass = vol * rho
    for (prop, typ, grp, desc) in [
        ("Material", "App::PropertyString", "Physics", "Material"),
        ("Density", "App::PropertyFloat", "Physics", "kg/m^3"),
        ("Volume", "App::PropertyFloat", "Physics", "m^3"),
        ("Mass", "App::PropertyFloat", "Physics", "kg"),
    ]:
        if prop not in o.PropertiesList:
            o.addProperty(typ, prop, grp, desc)
    o.Material = mat
    o.Density = rho
    o.Volume = vol
    o.Mass = mass

def circ(r):
    return Part.Circle(App.Vector(0,0,0), App.Vector(0,0,1), r)

def make_revolved_profile(points):
    wire = Part.makePolygon([App.Vector(*p) for p in points] + [App.Vector(*points[0])])
    face = Part.Face(wire)
    rev = face.revolve(App.Vector(0,0,0), App.Vector(0,1,0), 360)
    return rev

# -------------------------
# Construcción
# -------------------------

# 1) TPS disco con bisel facetado y araña
tps_R = P["tps_diameter"]/2
tps_t0 = P["tps_thickness_center"]
tps_tedge = max(0.01, tps_t0 - P["tps_edge_taper"])
disc_center = Part.makeCylinder(tps_R*0.25, tps_t0)
disc_edge = Part.makeCylinder(tps_R, tps_tedge)
facets = []
for i in range(P["tps_facet_count"]):
    ang0 = 2*math.pi*i/P["tps_facet_count"]
    ang1 = 2*math.pi*(i+1)/P["tps_facet_count"]
    r0 = tps_R*0.25
    p0 = App.Vector(r0*math.cos(ang0), r0*math.sin(ang0), tps_t0)
    p1 = App.Vector(tps_R*math.cos(ang0), tps_R*math.sin(ang0), tps_tedge)
    p2 = App.Vector(tps_R*math.cos(ang1), tps_R*math.sin(ang1), tps_tedge)
    p3 = App.Vector(r0*math.cos(ang1), r0*math.sin(ang1), tps_t0)
    w = Part.makePolygon([p0,p1,p2,p3,p0])
    f = Part.Face(w)
    facets.append(f.extrude(App.Vector(0,0,0.001)))
tps = disc_edge.fuse(disc_center)
for f in facets:
    tps = tps.fuse(f)
boss = Part.makeCylinder(P["tps_boss_diameter"]/2, 0.08)
spokes = []
for i in range(P["tps_spoke_count"]):
    a = 2*math.pi*i/P["tps_spoke_count"]
    L = tps_R*0.92
    rod = Part.makeCylinder(0.02, L)
    rod = rod.rotate(App.Vector(0,0,0), App.Vector(0,1,0), 90)
    rod = rod.rotate(App.Vector(0,0,0), App.Vector(0,0,1), math.degrees(a))
    rod = rod.translate(App.Vector(0,0,tps_tedge+0.02))
    spokes.append(rod)
tps_all = tps.fuse(boss)
for s in spokes:
    tps_all = tps_all.fuse(s)
tps_obj = add_obj(tps_all, "TPS_Disk", (0.05,0.55,0.90))
assign_props(tps_obj, P["rho_tps"], "C/C TPS")

# 2) Bus hexagonal
bus_apothem = P["bus_flat"]/2
R_vertex = bus_apothem / math.cos(math.radians(30))
pts = []
for i in range(6):
    ang = math.radians(60*i + 30)
    pts.append(App.Vector(R_vertex*math.cos(ang), R_vertex*math.sin(ang), 0))
wire = Part.makePolygon(pts + [pts[0]])
face = Part.Face(wire)
bus = face.extrude(App.Vector(0,0,P["bus_length"]))
try:
    bus = bus.makeChamfer(P["bus_chamfer"], bus.Edges)
except Exception:
    pass
bus_inner