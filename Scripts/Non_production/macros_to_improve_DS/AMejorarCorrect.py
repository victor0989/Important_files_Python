AMejorarCorrect.py
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
    "tps_thickness_center": 0.11,        # m (núcleo foam + C/C)
    "tps_edge_taper": 0.09,              # m (bisel hacia el borde)
    "tps_facet_count": 16,               # segmentos de bisel (lectura facetada)
    "tps_boss_diameter": 0.35,           # m (buje de sujeción trasero)
    "tps_spoke_count": 6,                # cercha tipo araña

    # Separación TPS -> bus
    "gap_tps_bus": 0.18,                 # m

    # Bus hexagonal (cuerpo central)
    "bus_flat": 1.60,                    # m (flat-to-flat)
    "bus_length": 3.2,                   # m
    "bus_wall": 0.030,                   # m
    "bus_chamfer": 0.025,                # m
    "bus_panel_groove_depth": 0.01,      # m (ranuras de panelado)
    "bus_panel_groove_pitch": 0.25,      # m

    # Módulos internos (cilíndricos)
    "mod_gap": 0.05,
    "mod_fuel_len": 1.6,
    "mod_ctrl_len": 0.7,
    "mod_pwr_len": 1.0,

    # DFD (motor trasero)
    "dfd_outer_dia": 2.5,
    "dfd_length": 1.4,
    "dfd_core_dia": 0.8,
    "dfd_throat_dia": 0.6,
    "dfd_exit_dia": 1.75,
    "dfd_ring_count": 4,
    "dfd_ring_radial": 0.06,
    "dfd_ring_gap": 0.05,

    # Radiadores laterales
    "rad_len": 2.2,
    "rad_root_height": 0.75,
    "rad_tip_height": 0.45,
    "rad_thk": 0.016,
    "rad_rib_pitch": 0.18,
    "rad_rib_depth": 0.006,

    # Arrays solares articulados
    "sa_panel_len": 1.4,
    "sa_panel_w": 0.6,
    "sa_thk": 0.014,
    "sa_boom_len": 0.55,
    "sa_yaw_deg": 35,     # ángulo peek-around máximo (±)
    "sa_pitch_deg": -10,  # inclinación respecto al plano del bus

    # Detalles
    "hga_dia": 0.6,
    "hga_depth": 0.18,
    "rcs_pod_d": 0.16,
    "rcs_pod_len": 0.22,

    # Materiales (densidad kg/m^3)
    "rho_tps": 1700,         # C/C + foam prom.
    "rho_bus": 2700,         # Al
    "rho_modules": 4500,     # mixto
    "rho_dfd": 8200,         # superaleación
    "rho_panel": 1800,       # comp. carbono
    "rho_radiator": 1850,    # grafito
    "rho_misc": 2700,        # Al
}

# -------------------------
# Utilidades
# -------------------------
def add_obj(shape, name, color=None):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    if Gui.Up:
        o.ViewObject.ShapeColor = color if color else P["blue"]
        o.ViewObject.LineWidth = 2
    return o

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

# Z-reference:
# z=0: cara frontal del TPS
# +Z hacia popa

# 1) TPS disco con bisel facetado y araña de soporte
tps_R = P["tps_diameter"]/2
tps_t0 = P["tps_thickness_center"]
tps_tedge = max(0.01, tps_t0 - P["tps_edge_taper"])

# Creamos una corona por loft entre círculo central y borde fino para crear bisel
outer_up = Part.Wire(circ(tps_R).toShape().Edges)
inner_up = Part.Wire(circ(max(0.01, tps_R*0.25)).toShape().Edges)
f_up = Part.Face(outer_up)
# Dos discos, uno grueso central, otro fino en el borde, unidos por una faja facetada
disc_center = Part.makeCylinder(tps_R*0.25, tps_t0)
disc_center = disc_center.translate(App.Vector(0,0,0))
disc_edge = Part.makeCylinder(tps_R, tps_tedge)
disc_edge = disc_edge.translate(App.Vector(0,0,0))

# Facetas del bisel: aproximamos con segmentos radiales
facets = []
for i in range(P["tps_facet_count"]):
    ang0 = 2*math.pi*i/P["tps_facet_count"]
    ang1 = 2*math.pi*(i+1)/P["tps_facet_count"]
    r0 = tps_R*0.25
    # trapezoide radial extruido en altura decreciente
    p0 = App.Vector(r0*math.cos(ang0), r0*math.sin(ang0), tps_t0)
    p1 = App.Vector(tps_R*math.cos(ang0), tps_R*math.sin(ang0), tps_tedge)
    p2 = App.Vector(tps_R*math.cos(ang1), tps_R*math.sin(ang1), tps_tedge)
    p3 = App.Vector(r0*math.cos(ang1), r0*math.sin(ang1), tps_t0)
    w = Part.makePolygon([p0,p1,p2,p3,p0])
    f = Part.Face(w)
    facets.append(f.extrude(App.Vector(0,0,0.001)))  # solidify
tps = disc_edge.fuse(disc_center)
for f in facets:
    tps = tps.fuse(f)

# Boss y araña
boss = Part.makeCylinder(P["tps_boss_diameter"]/2, 0.08).translate(App.Vector(0,0,tps_tedge))
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

# 2) Bus hexagonal con chaflanes y panelado
bus_apothem = P["bus_flat"]/2
R_vertex = bus_apothem / math.cos(math.radians(30))
# prisma hexagonal
pts = []
for i in range(6):
    ang = math.radians(60*i + 30)
    pts.append(App.Vector(R_vertex*math.cos(ang), R_vertex*math.sin(ang), 0))
wire = Part.makePolygon(pts + [pts[0]])
face = Part.Face(wire)
bus = face.extrude(App.Vector(0,0,P["bus_length"]))
# chaflanes
try:
    bus = bus.makeChamfer(P["bus_chamfer"], bus.Edges)
except Exception:
    pass
# hueco interno (pared)
bus_inner = face.scaled(App.Vector(0,0,0), 1 - P["bus_wall"]/bus_apothem).extrude(App.Vector(0,0,P["bus_length"] - 2*P["bus_wall"]))
bus_inner = bus_inner.translate(App.Vector(0,0,P["gap_tps_bus"] + tps_tedge + P["bus_wall"]))
bus_shell = bus.cut(bus_inner)

# ranuras de panelado
grooves = []
z0 = P["gap_tps_bus"] + tps_tedge + 0.12
while z0 < P["gap_tps_bus"] + P["bus_length"] - 0.12:
    g = Part.makeBox(P["bus_flat"]*1.2, P["bus_flat"]*1.2, P["rad_rib_depth"]*2)
    g = g.translate(App.Vector(-P["bus_flat"]*0.6, -P["bus_flat"]*0.6, z0))
    grooves.append(g)
    z0 += P["bus_panel_groove_pitch"]
for g in grooves:
    bus_shell = bus_shell.cut(g)

# posicionar bus tras TPS
bus_shell = bus_shell.translate(App.Vector(0,0,tps_tedge + P["gap_tps_bus"]))
bus_obj = add_obj(bus_shell, "Bus_Hex", (0.10,0.40,0.85))
assign_props(bus_obj, P["rho_bus"], "Al Structure")

# 3) Módulos internos cilíndricos apilados
mods = []
z_cursor = tps_tedge + P["gap_tps_bus"] + P["bus_wall"]
usable = P["bus_length"] - 2*P["bus_wall"]
mod_specs = [("Mod_Fuel", P["mod_fuel_len"]), ("Mod_Ctrl", P["mod_ctrl_len"]), ("Mod_Power", P["mod_pwr_len"])]
mod_radius = (P["bus_flat"]/2) * 0.85  # cabe dentro del hex
for name, L in mod_specs:
    if usable <= 0: break
    Luse = min(L, usable)
    m = Part.makeCylinder(mod_radius, Luse).translate(App.Vector(0,0,z_cursor))
    m_obj = add_obj(m, name, (0.25,0.60,0.95))
    assign_props(m_obj, P["rho_modules"], "Internal Module")
    mods.append(m_obj)
    z_cursor += Luse + P["mod_gap"]
    usable -= (Luse + P["mod_gap"])

# 4) DFD motor trasero por revolución + anillos
dfd_R = P["dfd_outer_dia"]/2
dfd_z0 = P["length_total"] - P["dfd_length"]
# Perfil de tobera (r,z) alrededor del eje Z
r_throat = P["dfd_throat_dia"]/2
r_exit = P["dfd_exit_dia"]/2
profile = [
    (dfd_R*0.60, dfd_z0 + 0.10),
    (r_throat,   dfd_z0 + P["dfd_length"]*0.35),
    (r_exit,     dfd_z0 + P["dfd_length"]),
    (r_exit+0.05,dfd_z0 + P["dfd_length"]),
    (r_throat+0.06, dfd_z0 + P["dfd_length"]*0.35),
    (dfd_R*0.65, dfd_z0 + 0.10),
]
# Convertimos a (x,z) para revolve alrededor del eje Z; usamos X como radio
prof_pts = [(0,profile[0][1])]  # arrancamos en eje para cerrar
for r,z in profile:
    prof_pts.append((r, z))
prof_pts.append((0, profile[-1][1]))
nozzle = make_revolved_profile(prof_pts)

# cárter cilíndrico delantero
casing = Part.makeCylinder(dfd_R, P["dfd_length"]).translate(App.Vector(0,0,dfd_z0))
core = Part.makeCylinder(P["dfd_core_dia"]/2, P["dfd_length"]).translate(App.Vector(0,0,dfd_z0))
engine = casing.fuse(nozzle).cut(core)

# Anillos concéntricos (tori seccionados)
rings = []
r_cur = dfd_R - P["dfd_ring_radial"]*1.2
for i in range(P["dfd_ring_count"]):
    tor = Part.makeTorus(r_cur, P["dfd_ring_radial"]/2, App.Vector(0,0,dfd_z0 + P["dfd_length"]*0.42), App.Vector(0,0,1))
    slab = Part.makeCylinder(dfd_R+0.2, P["dfd_length"]).translate(App.Vector(0,0,dfd_z0))
    ring = tor.common(slab)
    rings.append(ring)
    r_cur -= (P["dfd_ring_radial"] + P["dfd_ring_gap"])
for r in rings:
    engine = engine.fuse(r)

dfd_obj = add_obj(engine, "DFD_Engine", (0.15,0.30,0.70))
assign_props(dfd_obj, P["rho_dfd"], "High-Temp Alloy")

# 5) Radiadores afilados con costillas
def radiator(side=1):
    # sección trapecial extruida
    h0 = P["rad_root_height"]; h1 = P["rad_tip_height"]
    L = P["rad_len"]; t = P["rad_thk"]
    # base en X (ancho), Y (espesor), Z (long)
    base = Part.makeBox(h0, t, L)
    tip = Part.makeBox(h1, t, L*0.75).translate(App.Vector((h0-h1)/2, 0, L*0.25))
    solid = base.fuse(tip)
    # costillas
    z = 0.12
    while z < L-0.12:
        rib = Part.makeBox(h1*0.9, P["rad_rib_depth"], t*4).translate(App.Vector((h0-h1)/2 + h1*0.05, -P["rad_rib_depth"], z))
        solid = solid.fuse(rib)
        z += P["rad_rib_pitch"]
    # posicionar a los lados del bus
    yoff = (side)*(bus_apothem + 0.08)
    zoff = tps_tedge + P["gap_tps_bus"] + 0.35
    solid = solid.translate(App.Vector(-h0/2, yoff, zoff))
    return solid

radL = radiator(+1)
radR = radiator(-1)
radL_obj = add_obj(radL, "Radiator_L", (0.20,0.65,0.85))
radR_obj = add_obj(radR, "Radiator_R", (0.20,0.65,0.85))
assign_props(radL_obj, P["rho_radiator"], "Graphite Radiator")
assign_props(radR_obj, P["rho_radiator"], "Graphite Radiator")

# 6) Arrays solares peek-around con gimbals
def solar_array(side=1):
    # boom
    boom = Part.makeCylinder(0.025, P["sa_boom_len"])
    boom = boom.rotate(App.Vector(0,0,0), App.Vector(0,1,0), 90)  # orientar en X
    # panel
    panel = Part.makeBox(P["sa_panel_w"], 0.012, P["sa_panel_len"])
    panel = panel.translate(App.Vector(-P["sa_panel_w"]/2, 0.006, P["sa_boom_len"]))  # justo al final del boom
    sa = boom.fuse(panel)
    # orientación
    yaw = P["sa_yaw_deg"] * side
    pitch = P["sa_pitch_deg"]
    # pivot: canto del bus, delante del centro
    pivot = App.Vector(0, side*(bus_apothem+0.04), tps_tedge + P["gap_tps_bus"] + 0.50)
    sa = sa.translate(pivot)
    sa = sa.rotate(pivot, App.Vector(0,0,1), yaw)
    sa = sa.rotate(pivot, App.Vector(1,0,0), pitch)
    return sa

saL = solar_array(+1)
saR = solar_array(-1)
saL_obj = add_obj(saL, "SolarArray_L", (0.10,0.55,0.90))
saR_obj = add_obj(saR, "SolarArray_R", (0.10,0.55,0.90))
assign_props(saL_obj, P["rho_panel"], "Solar Panel")
assign_props(saR_obj, P["rho_panel"], "Solar Panel")

# 7) HGA y pods RCS
hga = Part.makeCone(P["hga_dia"]/2, P["hga_dia"]/4, P["hga_depth"])
hga = hga.translate(App.Vector(0,0, tps_tedge + P["gap_tps_bus"] + P["bus_length"]*0.65))
hga_obj = add_obj(hga, "HGA", (0.10,0.40,0.85))
assign_props(hga_obj, P["rho_misc"], "Al/CFRP")

def rcs_pod(angle_deg):
    pod = Part.makeCylinder(P["rcs_pod_d"]/2, P["rcs_pod_len"])
    pod = pod.rotate(App.Vector(0,0,0), App.Vector(0,1,0), 90)  # apunta ±X
    # montar en vértices del hex
    ang = math.radians(angle_deg)
    vx = R_vertex*math.cos(ang)
    vy = R_vertex*math.sin(ang)
    z = tps_tedge + P["gap_tps_bus"] + P["bus_length"]*0.25
    pod = pod.translate(App.Vector(vx, vy, z))
    return pod

rcs_angles = [0, 120, 240]
rcs_list = []
for ang in rcs_angles:
    rcs_list.append(rcs_pod(ang))
    rcs_list.append(rcs_pod(ang+60))
rcs_solid = rcs_list[0]
for s in rcs_list[1:]:
    rcs_solid = rcs_solid.fuse(s)
rcs_obj = add_obj(rcs_solid, "RCS_Pods", (0.10,0.40,0.85))
assign_props(rcs_obj, P["rho_misc"], "Al Thruster Pods")

# 8) Ensamblaje y masa total
grp = doc.addObject("App::DocumentObjectGroup", "Assembly")
for o in [tps_obj, bus_obj, dfd_obj, radL_obj, radR_obj, saL_obj, saR_obj, hga_obj, rcs_obj] + mods:
    grp.addObject(o)
if "TotalMass" not in grp.PropertiesList:
    grp.addProperty("App::PropertyFloat", "TotalMass", "Physics", "kg")
grp.TotalMass = sum(getattr(o, "Mass", 0.0) for o in grp.Group)

# -------------------------
# TechDraw: ortográficas y sección del DFD
# -------------------------
page = doc.addObject('TechDraw::DrawPage', 'Blueprint')
tmpl = doc.addObject('TechDraw::DrawSVGTemplate', 'Template')
tmpl.Template = TechDraw.getStandardTemplate('A3_LandscapeTD.svg')
page.Template = tmpl

def add_view(name, dir_vec, x, y, scale=0.10):
    v = doc.addObject('TechDraw::DrawViewPart', name)
    v.Source = [grp]
    v.Direction = App.Vector(*dir_vec)
    v.X = x; v.Y = y; v.Scale = scale
    v.LineWidth = 0.25
    v.LineColor = (25,102,217)
    page.addView(v)
    return v

v_front = add_view('Front', (0,-1,0), 85, 165, 0.10)
v_top   = add_view('Top',   (0,0,-1), 215, 165, 0.10)
v_side  = add_view('Side',  (-1,0,0), 345, 165, 0.10)

# Sección longitudinal del DFD
v_sec = doc.addObject('TechDraw::DrawViewPart', 'Section_DFD')
v_sec.Source = [dfd_obj]
v_sec.Direction = App.Vector(-1,0,0)
v_sec.X = 215; v_sec.Y = 60; v_sec.Scale = 0.16
v_sec.Hatch = True
page.addView(v_sec)

def add_dim(name, view, x1,y1,x2,y2, kind="Distance"):
    d = doc.addObject('TechDraw::DrawViewDimension', name)
    d.Type = kind
    d.References2D = [(view, f"XY({x1},{y1})"), (view, f"XY({x2},{y2})")]
    page.addView(d)
    return d

# Cotas clave (colocación aproximada sobre la hoja)
add_dim("Dim_TotalLen", v_side, 10, 10, 380, 10)
add_dim("Dim_TPS_Dia", v_front, 85, 210, 85, 120)
add_dim("Dim_DFD_Dia", v_front, 300, 205, 300, 145)

# Notas
def note(txt, x, y):
    n = doc.addObject('TechDraw::DrawViewAnnotation', 'Note')
    n.Text = txt; n.X = x; n.Y = y
    page.addView(n)
note(f"TPS Ø {P['tps_diameter']:.2f} m, t_center {P['tps_thickness_center']*1000:.0f} mm (facetado {P['tps_facet_count']} seg.)", 25, 38)
note(f"DFD Ø {P['dfd_outer_dia']:.2f} m, throat Ø {P['dfd_throat_dia']:.2f} m", 25, 30)
note(f"Longitud total {P['length_total']:.2f} m", 25, 22)

doc.recompute()
if Gui.Up:
    v = Gui.ActiveDocument.ActiveView
    v.viewIsometric(); v.fitAll()
