AMejorarAmpliarBlindaHex.py
import FreeCAD as App
import FreeCADGui as Gui
import Part, math, os

# ---------------------------------
# Documento y configuración
# ---------------------------------
DOC_NAME = "HexSat_Metallic_Fusion_Realistic"
EXPORT_STEP = False
STEP_PATH = os.path.join(App.getUserAppDataDir(), DOC_NAME + ".step")

# Cierra documento previo
if App.ActiveDocument and App.ActiveDocument.Label == DOC_NAME:
    doc = App.ActiveDocument
    for o in list(doc.Objects):
        try: doc.removeObject(o.Name)
        except: pass
else:
    for n, d in list(App.listDocuments().items()):
        if d.Label == DOC_NAME: App.closeDocument(n)
    doc = App.newDocument(DOC_NAME)

# ---------------------------------
# Parámetros (métricos, en metros)
# ---------------------------------
P = {
    # Bus: cilindro + cono
    "body_R": 0.55,             # radio cuerpo
    "body_L": 2.40,             # longitud cuerpo
    "hull_th": 0.004,           # espesor casco ~ 4 mm
    "cone_L": 0.85,             # longitud cono inferior
    "cone_Rtop": 0.55,          # radio unión cono-cuerpo
    "cone_Rbase": 0.09,         # radio base del cono (boquilla/sensor)

    # Flanges/anillos de montaje
    "collar_h": 0.10,
    "collar_t": 0.015,
    "mount_ring_w": 0.10,
    "mount_ring_t": 0.04,
    "mount_bolts": 16,
    "bolt_R": 0.006,
    "bolt_head_H": 0.006,       # altura cabeza
    "bolt_head_D": 0.014,       # diámetro cabeza

    # Núcleo estructural (hex estilizado interno)
    "core_flat": 1.70,
    "core_h": 2.50,
    "core_wall": 0.060,

    # Paneles solares (4 en cruz)
    "panel_L": 1.90,            # largo
    "panel_W": 0.85,            # ancho
    "panel_T": 0.020,           # espesor
    "panel_frame": 0.045,       # marco perimetral
    "panel_rows": 8,
    "panel_cols": 16,
    "hinge_R": 0.020,           # radio bisagra
    "hinge_L": 0.08,            # longitud bisagra
    "panel_arm_L": 0.40,
    "panel_mount_offset": 0.60, # desde eje del cuerpo

    # Radiadores y aletas
    "radiator_W": 1.20,
    "radiator_H": 0.75,
    "radiator_T": 0.018,
    "fin_T": 0.004,
    "fin_gap": 0.020,
    "radiator_offset": 0.30,

    # Antena parabólica y mástil + feed
    "dish_R": 0.80,
    "dish_depth": 0.18,
    "dish_t": 0.006,
    "mast_R": 0.040,
    "mast_L": 0.85,
    "feed_R": 0.030,
    "feed_L": 0.20,

    # Sensores
    "sun_sensor_D": 0.030,
    "sun_sensor_H": 0.010,
    "star_tracker_D": 0.060,
    "star_tracker_L": 0.14,

    # Propulsión RCS (thrusters)
    "rcs_R": 0.020,
    "rcs_L": 0.10,
    "rcs_count_per_side": 2,

    # Payload interno tipo CubeSat
    "add_cubesat": True,
    "cubesat_L": 0.30,
    "cubesat_W": 0.20,
    "cubesat_H": 0.12,
    "cubesat_wall": 0.006,

    # Ruedas de reacción (inerciales)
    "rw_R": 0.10,
    "rw_H": 0.05,
    "rw_count": 3,

    # MLI (aislamiento térmico) con costuras
    "insul_from": 0.65,
    "insul_to": 1.85,
    "insul_th": 0.003,
    "insul_wave_amp": 0.002,
    "insul_wave_freq": 7,
    "mli_seam_w": 0.012,        # ancho costura

    # Colores
    "col_metal": (0.75,0.75,0.78),
    "col_dark": (0.20,0.22,0.26),
    "col_gold": (0.85,0.75,0.35),
    "col_bracket": (0.68,0.70,0.74),
}

# Conversión a mm
def mm(v_m): return v_m * 1000.0

# ---------------------------------
# Utilidades geométricas
# ---------------------------------
X_AXIS = App.Vector(1,0,0)
Y_AXIS = App.Vector(0,1,0)
Z_AXIS = App.Vector(0,0,1)

def rot_to_x(): return App.Rotation(Y_AXIS, 90)

def add_part(shape, name, color=(0.8,0.8,0.85)):
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    try:
        obj.ViewObject.ShapeColor = color
        obj.ViewObject.LineColor = (0.3,0.3,0.3)
    except: pass
    return obj

def mk_cyl_x(R, L, x0=0, y=0, z=0):
    c = Part.makeCylinder(mm(R), mm(L))
    c.Placement = App.Placement(App.Vector(mm(x0), mm(y), mm(z)), rot_to_x())
    return c

def mk_cone_x(R1, R2, L, x0=0, y=0, z=0):
    c = Part.makeCone(mm(R1), mm(R2), mm(L))
    c.Placement = App.Placement(App.Vector(mm(x0), mm(y), mm(z)), rot_to_x())
    return c

def mk_box(w,d,h, x=0, y=0, z=0, center=True):
    b = Part.makeBox(mm(w), mm(d), mm(h))
    if center:
        b.Placement = App.Placement(App.Vector(mm(x - w/2.0), mm(y - d/2.0), mm(z - h/2.0)), App.Rotation())
    else:
        b.Placement = App.Placement(App.Vector(mm(x), mm(y), mm(z)), App.Rotation())
    return b

def mk_ring(Ro, Ri, L, x0=0, y=0, z=0):
    out = Part.makeCylinder(mm(Ro), mm(L))
    inn = Part.makeCylinder(mm(Ri), mm(L + 0.0002))  # un pelo más largo para robustez
    ring = out.cut(inn)
    ring.Placement = App.Placement(App.Vector(mm(x0), mm(y), mm(z)), rot_to_x())
    return ring

# ---------------------------------
# Construcción del bus (cono + cuerpo + casco hueco)
# ---------------------------------
cone = mk_cone_x(P["cone_Rtop"], P["cone_Rbase"], P["cone_L"], x0=0)
body = mk_cyl_x(P["body_R"], P["body_L"], x0=P["cone_L"])
outer = cone.fuse(body)

# Casco hueco robusto por sustracción (evitar offsets problemáticos)
inner_body = mk_cyl_x(P["body_R"] - P["hull_th"], P["body_L"] - P["hull_th"]*0.2, x0=P["cone_L"] + P["hull_th"]*0.1)
inner_cone = mk_cone_x(P["cone_Rtop"] - P["hull_th"], max(0.01, P["cone_Rbase"] - P["hull_th"]),
                       P["cone_L"] - P["hull_th"]*0.1, x0=P["hull_th"]*0.05)
inner_all = inner_body.fuse(inner_cone)
hull_shell = outer.cut(inner_all)
hull_obj = add_part(hull_shell, "Hull_Shell", color=P["col_metal"])

# Flange en unión y anillo de montaje con pernos + cabeza de perno
collar = mk_ring(P["cone_Rtop"] + P["collar_t"], P["cone_Rtop"], P["collar_h"], x0=P["cone_L"] - P["collar_h"]/2.0)
add_part(collar, "Collar", color=P["col_bracket"])

mount_ring = mk_ring(P["body_R"] + P["mount_ring_t"], P["body_R"] + P["mount_ring_t"] - P["mount_ring_w"], P["mount_ring_t"],
                     x0=P["cone_L"] + P["body_L"]*0.20)
add_part(mount_ring, "Mount_Ring", color=P["col_bracket"])

for i in range(P["mount_bolts"]):
    ang = 2*math.pi * i / P["mount_bolts"]
    br = P["body_R"] + P["mount_ring_t"] - P["mount_ring_w"]/2.0
    bx = P["cone_L"] + P["body_L"]*0.20
    by = math.cos(ang) * br
    bz = math.sin(ang) * br
    shank = mk_cyl_x(P["bolt_R"], P["mount_ring_t"], x0=bx, y=by, z=bz)
    add_part(shank, f"Bolt_{i}_Shank", color=(0.55,0.55,0.58))
    head = mk_cyl_x(P["bolt_head_D"]/2.0, P["bolt_head_H"], x0=bx + P["mount_ring_t"]/2.0, y=by, z=bz)
    add_part(head, f"Bolt_{i}_Head", color=(0.60,0.60,0.62))

# Núcleo hex estilizado (simplificado robusto)
hex_body = mk_box(P["core_flat"], P["core_flat"], P["core_h"], x=P["cone_L"] + P["body_L"]/2.0, y=0, z=0, center=True)
inner_hex = mk_box(P["core_flat"] - 2*P["core_wall"], P["core_flat"] - 2*P["core_wall"],
                   P["core_h"] - 2*P["core_wall"], x=P["cone_L"] + P["body_L"]/2.0, y=0, z=0, center=True)
hex_shell = hex_body.cut(inner_hex)
add_part(hex_shell, "Hex_Core", color=(0.70,0.72,0.76))

# ---------------------------------
# Antena parabólica, mástil y feed
# ---------------------------------
dish = mk_cone_x(P["dish_R"], P["dish_R"] - P["dish_depth"], P["dish_depth"],
                 x0=P["cone_L"] + P["body_L"]*0.88, y=0, z=P["body_R"] + 0.12)
add_part(dish, "Dish", color=P["col_metal"])

mast = mk_cyl_x(P["mast_R"], P["mast_L"],
                x0=P["cone_L"] + P["body_L"]*0.88 - P["mast_L"]/2.0, y=0, z=P["body_R"] + 0.12)
add_part(mast, "Dish_Mast", color=P["col_bracket"])

feed = mk_cyl_x(P["feed_R"], P["feed_L"],
                x0=P["cone_L"] + P["body_L"]*0.88 + P["dish_depth"]/2.0 - P["feed_L"]/2.0,
                y=0, z=P["body_R"] + 0.12)
add_part(feed, "Dish_Feed", color=(0.68,0.70,0.74))

# ---------------------------------
# Paneles solares en cruz con bisagras y marcos
# ---------------------------------
def make_panel_with_frame(L, W, T, rows, cols, frame):
    plate = mk_box(L, T, W, x=0, y=0, z=0, center=False)
    frame_box = mk_box(L + 2*frame, T, W + 2*frame, x=-frame, y=0, z=-frame, center=False)
    panel = frame_box.cut(plate)
    # ranuras del mosaico (evitar self-intersection: ranuras finas)
    cell_w = L / cols
    cell_h = W / rows
    groove = max(0.0015, T * 0.25)
    for i in range(1, cols):
        cut = mk_box(0.004, groove, W, x=i*cell_w, y=(T-groove)/2.0, z=0, center=False)
        panel = panel.cut(cut)
    for j in range(1, rows):
        cut = mk_box(L, groove, 0.004, x=0, y=(T-groove)/2.0, z=j*cell_h, center=False)
        panel = panel.cut(cut)
    return panel

panel_base = make_panel_with_frame(P["panel_L"], P["panel_W"], P["panel_T"], P["panel_rows"], P["panel_cols"], P["panel_frame"])

def place_panel(name, axis='Y+', offset=P["panel_mount_offset"] + P["body_R"]):
    p = panel_base.copy()
    cx = P["cone_L"] + P["body_L"]/2.0
    if axis == 'Y+':
        p.Placement = App.Placement(App.Vector(mm(cx), mm(offset), 0), App.Rotation())
    elif axis == 'Y-':
        p.Placement = App.Placement(App.Vector(mm(cx), mm(-offset), 0), App.Rotation())
    elif axis == 'Z+':
        p.Placement = App.Placement(App.Vector(mm(cx), 0, mm(offset)), App.Rotation())
    elif axis == 'Z-':
        p.Placement = App.Placement(App.Vector(mm(cx), 0, mm(-offset)), App.Rotation())
    return add_part(p, name, color=P["col_dark"])

# Bisagra (cilindro) + brazo corto entre cuerpo y panel
def add_hinge_and_bracket(axis='Y+', name="Hinge"):
    cx = P["cone_L"] + P["body_L"]/2.0
    # bisagra en el borde del cuerpo
    hy = 0; hz = 0
    if axis == 'Y+': hy = P["body_R"]
    if axis == 'Y-': hy = -P["body_R"]
    if axis == 'Z+': hz = P["body_R"]
    if axis == 'Z-': hz = -P["body_R"]
    hinge = mk_cyl_x(P["hinge_R"], P["hinge_L"], x0=cx, y=hy, z=hz)
    add_part(hinge, f"{name}_{axis}", color=P["col_bracket"])
    # brazo intermedio
    arm = mk_cyl_x(0.018, P["panel_arm_L"], x0=cx - P["panel_arm_L"]/2.0, y=hy, z=hz)
    add_part(arm, f"Bracket_{axis}", color=P["col_bracket"])

panel_E = place_panel("Panel_E", axis='Y+')
panel_W = place_panel("Panel_W", axis='Y-')
panel_N = place_panel("Panel_N", axis='Z+')
panel_S = place_panel("Panel_S", axis='Z-')

add_hinge_and_bracket('Y+', "Hinge")
add_hinge_and_bracket('Y-', "Hinge")
add_hinge_and_bracket('Z+', "Hinge")
add_hinge_and_bracket('Z-', "Hinge")

# Struts diagonales (tubos) hacia cada panel
def add_strut(axis='Y+', name="Strut"):
    cx = P["cone_L"] + P["body_L"]/2.0
    ty = 0; tz = 0
    off = P["panel_mount_offset"] + P["body_R"]
    if axis == 'Y+': ty = off
    if axis == 'Y-': ty = -off
    if axis == 'Z+': tz = off
    if axis == 'Z-': tz = -off
    L = math.sqrt((off)**2 + (off)**2)
    strut = mk_cyl_x(0.016, L, x0=cx - L/2.0, y=ty/2.0, z=tz/2.0)
    add_part(strut, f"{name}_{axis}", color=P["col_bracket"])

add_strut('Y+'); add_strut('Y-'); add_strut('Z+'); add_strut('Z-')

# ---------------------------------
# Radiadores con aletas
# ---------------------------------
def make_radiator_with_fins(W, H, T, fin_T, fin_gap):
    base = mk_box(W, T, H, x=0, y=0, z=0, center=False)
    # aletas longitudinales (en Z)
    n_fins = int(H / (fin_gap + fin_T))
    z0 = 0.0
    for i in range(n_fins):
        fin = mk_box(W, fin_T, fin_gap, x=0, y=T, z=z0, center=False)
        base = base.fuse(fin)
        z0 += fin_gap + fin_T
    return base

rad_R = make_radiator_with_fins(P["radiator_W"], P["radiator_H"], P["radiator_T"], P["fin_T"], P["fin_gap"])
rad_R.Placement = App.Placement(App.Vector(mm(P["cone_L"] + P["body_L"]*0.62), mm(P["body_R"] + P["radiator_offset"]), 0), App.Rotation())
add_part(rad_R, "Radiator_Right", color=(0.62,0.66,0.70))

rad_L = rad_R.copy()
rad_L.Placement = App.Placement(App.Vector(mm(P["cone_L"] + P["body_L"]*0.62), mm(-(P["body_R"] + P["radiator_offset"])), 0), App.Rotation())
add_part(rad_L, "Radiator_Left", color=(0.62,0.66,0.70))

# ---------------------------------
# Sensores: sun sensor y star tracker
# ---------------------------------
sun_sensor = mk_cyl_x(P["sun_sensor_D"]/2.0, P["sun_sensor_H"],
                      x0=P["cone_L"] + P["body_L"]*0.40, y=P["body_R"]*0.95, z=P["body_R"]*0.10)
add_part(sun_sensor, "Sun_Sensor", color=(0.80,0.80,0.82))

star_tracker = mk_cyl_x(P["star_tracker_D"]/2.0, P["star_tracker_L"],
                        x0=P["cone_L"] + P["body_L"]*0.45, y=-P["body_R"]*0.85, z=P["body_R"]*0.20)
add_part(star_tracker, "Star_Tracker", color=(0.72,0.74,0.78))

# ---------------------------------
# Propulsión RCS: thrusters alrededor del cuerpo
# ---------------------------------
def add_rcs_ring(x_frac=0.30, y_sign=1.0):
    base_x = P["cone_L"] + P["body_L"] * x_frac
    for i in range(P["rcs_count_per_side"]):
        ang = i * (math.pi / (P["rcs_count_per_side"]))
        y = y_sign * (P["body_R"] * 0.95)
        z = math.sin(ang) * (P["body_R"] * 0.70)
        rcs = mk_cyl_x(P["rcs_R"], P["rcs_L"], x0=base_x, y=y, z=z)
        add_part(rcs, f"RCS_{'R' if y_sign>0 else 'L'}_{i}", color=(0.68,0.70,0.74))

add_rcs_ring(0.32, +1.0)
add_rcs_ring(0.32, -1.0)

# ---------------------------------
# Payload interno tipo CubeSat
# ---------------------------------
if P["add_cubesat"]:
    cs = mk_box(P["cubesat_L"], P["cubesat_W"], P["cubesat_H"],
                x=P["cone_L"] + P["body_L"]/2.0, y=0, z=0, center=True)
    inner_cs = mk_box(P["cubesat_L"] - 2*P["cubesat_wall"], P["cubesat_W"] - 2*P["cubesat_wall"],
                      P["cubesat_H"] - 2*P["cubesat_wall"],
                      x=P["cone_L"] + P["body_L"]/2.0, y=0, z=0, center=True)
    cs_shell = cs.cut(inner_cs)
    add_part(cs_shell, "CubeSat_Payload", color=(0.70,0.72,0.76))

# ---------------------------------
# Ruedas de reacción (tres)
# ---------------------------------
rw_positions = [
    (P["cone_L"] + P["body_L"]*0.30, 0.0, P["body_R"]*0.4),
    (P["cone_L"] + P["body_L"]*0.32, P["body_R"]*0.35, -P["body_R"]*0.2),
    (P["cone_L"] + P["body_L"]*0.34, -P["body_R"]*0.35, -P["body_R"]*0.2),
]
for i, (rx, ry, rz) in enumerate(rw_positions):
    rw = mk_cyl_x(P["rw_R"], P["rw_H"], x0=rx, y=ry, z=rz)
    add_part(rw, f"Reaction_Wheel_{i}", color=(0.64,0.66,0.70))

# ---------------------------------
# MLI (banda dorada) con costuras
# ---------------------------------
ins_w = max(0.06, P["insul_to"] - P["insul_from"])
wrap_outer = mk_cyl_x(P["body_R"] + P["insul_th"], ins_w, x0=P["insul_from"])
wrap_inner = mk_cyl_x(max(0.01, P["body_R"] - P["insul_th"]), ins_w + 0.0002, x0=P["insul_from"])
wrap_band = wrap_outer.cut(wrap_inner)

# Ondulación por sustracción y costuras longitudinales (pequeños "cordones")
for i in range(P["insul_wave_freq"]):
    z = math.sin(i * math.pi / P["insul_wave_freq"]) * P["insul_wave_amp"]
    cut = mk_box(ins_w, 0.10, 0.004, x=P["insul_from"] + ins_w/2.0, y=0, z=z, center=True)
    wrap_band = wrap_band.cut(cut)

# Costuras: dos líneas elevadas en Y
seam_y = P["body_R"] * 0.92
seam1 = mk_box(ins_w, P["mli_seam_w"], 0.002, x=P["insul_from"] + ins_w/2.0, y=seam_y, z=0, center=True)
seam2 = mk_box(ins_w, P["mli_seam_w"], 0.002, x=P["insul_from"] + ins_w/2.0, y=-seam_y, z=0, center=True)
wrap_band = wrap_band.fuse(seam1).fuse(seam2)

add_part(wrap_band, "Thermal_Insulation_MLI", color=P["col_gold"])

# ---------------------------------
# Recomputa y exporta
# ---------------------------------
doc.recompute()
if EXPORT_STEP:
    try:
        Part.export([o for o in doc.Objects if hasattr(o, "Shape")], STEP_PATH)
        App.Console.PrintMessage(f"STEP exportado en: {STEP_PATH}\n")
    except Exception as e:
        App.Console.PrintWarning(f"Export STEP failed: {e}\n")

print("Macro HexSat_Metallic_Fusion_Realistic listo: bus cilíndrico-cono, 4 paneles en cruz, detalles espaciales y robustez CAD.")
