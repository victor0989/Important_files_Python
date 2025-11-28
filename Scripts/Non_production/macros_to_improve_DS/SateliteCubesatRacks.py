SateliteCubesatRacks.py
import math
import FreeCAD as App
import Part

# ===================== Parámetros (mm) =====================
# Bus principal
p_bus_w = 160.0
p_bus_d = 90.0
p_bus_h = 120.0
bus_skin_t = 2.0

# Escudo frontal (TPS) y cortina lateral segmentada (Whipple/Kevlar/Flex)
shield_d = 240.0
shield_thk = 14.0
shield_cone = 26.0
shield_gap = 34.0
shield_back_standoff = 12.0

shield_rad_len   = p_bus_w * 1.7       # longitud de cortina en +X→-X (se despliega hacia -X)
shield_gap_side  = 45.0                # distancia radial del bus a la cortina
shield_cc_t      = 3.0                 # capa cerámica / C-C
shield_kevl_t    = 6.0                 # capa kevlar/Nextel
shield_flex_t    = 2.5                 # flexible/multi-layer
shield_seg_count = 28                  # número de segmentos de cortina
shield_support_rods = 12               # puntales a la cortina
shield_slot_w    = 2.2                 # ancho de las ranuras de segmentación

# Paddles (paneles solares)
paddle_len = 95.0
paddle_root_w = 46.0
paddle_tip_w = 28.0
paddle_t = 2.0
paddle_y_offset = p_bus_d/2.0 - 8.0
paddle_tilt_deg = 22.0

# Radiadores con aletas
radiator_w = 90.0
radiator_h = 130.0
radiator_t = 2.2
radiator_back_offset = 50.0
radiator_fin_pitch = 12.0
radiator_fin_w = 1.2
radiator_fin_len = 10.0  # sobresale hacia -X

# Antenas/brazos
faraday_len = 52.0
faraday_r   = 12.0
whip_len = 180.0
whip_r   = 0.9

back_dish_d      = 130.0
back_dish_depth  = 28.0
steps_profile    = 84
t_bumper_ring    = 1.4
boom_len_back = 95.0
boom_r        = 1.8
boom_tip_r    = 4.0

# Tanques / control de actitud / RCS
tank_radius = 18.0
tank_length = 120.0
rwheel_r = 18.0
rwheel_t = 20.0
rcs_cone_r1 = 5.0
rcs_cone_r2 = 1.2
rcs_cone_h  = 18.0

# Propulsión iónica compacta (anillo trasero)
ion_body_r   = 22.0
ion_body_L   = 38.0
ion_grid_r_o = 26.0
ion_grid_r_i = 18.0
ion_grid_t   = 2.0
ion_nozzle_r1 = 20.0
ion_nozzle_r2 = 8.0
ion_nozzle_L  = 18.0
ion_count     = 8
ion_ring_R    = 42.0

# Exportación
export_path = App.getUserAppDataDir() + "Satellite_Complex.step"
export_as_single_compound = False

# ===================== Funciones utilitarias =====================
def parabola_r(z, d, depth):
    if depth <= 0: return 0.0
    f = (d*d) / (16.0*depth)
    val = 4.0*f*z
    return math.sqrt(val) if val > 0 else 0.0

def make_revolved_solid_from_diameter(d, depth, steps=72, z0_eps_factor=1.0):
    if d <= 0 or depth <= 0: return None
    steps = max(24, int(steps))
    z0 = depth / (steps * z0_eps_factor)
    p_axis_bot = App.Vector(0,0,z0)
    p_axis_top = App.Vector(0,0,depth)
    e_axis = Part.makeLine(p_axis_bot, p_axis_top)
    r_max = parabola_r(depth, d, depth)
    p_top_out = App.Vector(r_max, 0, depth)
    e_top = Part.makeLine(p_axis_top, p_top_out)
    outer_pts = []
    for i in range(steps+1):
        z = depth - (depth - z0) * (i/steps)
        r = parabola_r(z, d, depth)
        outer_pts.append(App.Vector(r,0,z))
    e_curve = Part.makePolygon(outer_pts)
    p_bot_out = outer_pts[-1]
    e_bot = Part.makeLine(p_bot_out, p_axis_bot)
    wire = Part.Wire([e_axis, e_top, e_curve, e_bot])
    face = Part.Face(wire)
    return face.revolve(App.Vector(0,0,0), App.Vector(0,0,1), 360)

def make_dish_layer_solid(d, depth, t, steps=72):
    outer = make_revolved_solid_from_diameter(d, depth, steps)
    d_inner = d - 2.0*t
    if d_inner <= 0.1: return outer
    inner = make_revolved_solid_from_diameter(d_inner, depth, steps)
    return outer.cut(inner)

def make_ring(r_outer, r_inner, h, base=App.Vector(0,0,0), axis=App.Vector(1,0,0)):
    return Part.makeCylinder(r_outer, h, base, axis).cut(Part.makeCylinder(r_inner, h, base, axis))

def place_shape(shape, pos=App.Vector(0,0,0), rot_axis=App.Vector(0,1,0), rot_deg=0):
    sh = shape.copy()
    pl = App.Placement()
    pl.Rotation = App.Rotation(rot_axis, rot_deg)
    pl.Base = pos
    sh.Placement = pl
    return sh

def add_part(doc, shape, name, color=(0.8,0.8,0.8), transparency=0):
    if shape is None: return None
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    try:
        obj.ViewObject.ShapeColor = color
        obj.ViewObject.Transparency = int(max(0, min(100, round(transparency*100))))
    except Exception:
        pass
    return obj

def make_trapezoid_plate(len_x, w_root, w_tip, t_y):
    pts = [
        App.Vector(0,0,-w_root/2.0),
        App.Vector(0,0,w_root/2.0),
        App.Vector(len_x,0,w_tip/2.0),
        App.Vector(len_x,0,-w_tip/2.0),
        App.Vector(0,0,-w_root/2.0)
    ]
    face = Part.Face(Part.Wire(Part.makePolygon(pts)))
    solid = face.extrude(App.Vector(0, t_y, 0))
    return place_shape(solid, pos=App.Vector(0,-t_y/2.0,0))

def fuse_safely(shapes):
    shapes = [s for s in shapes if s is not None]
    if not shapes: return None
    acc = shapes[0]
    for s in shapes[1:]:
        try: acc = acc.fuse(s)
        except Exception: pass
    return acc

def cut_safely(a, b):
    try: return a.cut(b)
    except Exception: return a

# ===================== Bus estructural =====================
def build_bus(doc):
    objs = []
    # Caja exterior
    box = Part.makeBox(p_bus_w, p_bus_d, p_bus_h)
    box.translate(App.Vector(-p_bus_w/2.0, -p_bus_d/2.0, -p_bus_h/2.0))
    # Hueco interior (piel)
    inner = Part.makeBox(p_bus_w-2*bus_skin_t, p_bus_d-2*bus_skin_t, p_bus_h-2*bus_skin_t)
    inner.translate(App.Vector(- (p_bus_w-2*bus_skin_t)/2.0, - (p_bus_d-2*bus_skin_t)/2.0, - (p_bus_h-2*bus_skin_t)/2.0))
    shell = box.cut(inner)
    objs.append(add_part(doc, shell, "BusShell", color=(0.35,0.35,0.40)))

    # Marcos internos longitudinales
    frame_thickness = 1.5
    frame_length = p_bus_d - 12.0
    frame_height = p_bus_h - 12.0
    for idx, xi in enumerate((-p_bus_w/4.0, 0.0, p_bus_w/4.0)):
        fr = Part.makeBox(frame_length, frame_thickness, frame_height)
        fr.translate(App.Vector(-frame_length/2.0, -frame_thickness/2.0, -frame_height/2.0))
        fr = place_shape(fr, pos=App.Vector(xi, 0, 0), rot_axis=App.Vector(0,0,1), rot_deg=90)
        objs.append(add_part(doc, fr, f"BusFrame_{idx}", color=(0.45,0.45,0.48), transparency=0.6))

    # Railes superiores/inferiores
    rail_w = 6.0
    for idx, z in enumerate((-p_bus_h/2.0 + 10.0, p_bus_h/2.0 - 10.0)):
        rail = Part.makeBox(p_bus_w - 12.0, rail_w, rail_w)
        rail.translate(App.Vector(-(p_bus_w - 12.0)/2.0, -rail_w/2.0, z - rail_w/2.0))
        objs.append(add_part(doc, rail, f"BusRail_{idx}", color=(0.50,0.50,0.55), transparency=0.3))

    # Placa de montaje frontal para escudo térmico
    ring_mount = make_ring(r_outer=(shield_d/2.0 - 22.0), r_inner=(shield_d/2.0 - 28.0), h=3.0,
                           base=App.Vector(p_bus_w/2.0 - 1.0, 0, 0), axis=App.Vector(1,0,0))
    objs.append(add_part(doc, ring_mount, "BusFrontMount", color=(0.65,0.65,0.68)))
    return [o for o in objs if o]

# ===================== Escudo térmico frontal (TPS) =====================
def build_heat_shield(doc):
    objs = []
    r0 = shield_d/2.0
    r1 = shield_d/2.0 - shield_cone*0.25
    r2 = shield_d/2.0 - shield_cone*0.85
    r3 = shield_d/2.0 - shield_cone
    h_front = 1.8
    h_core = max(1.0, shield_thk - 3.6)
    h_back = max(1.0, shield_thk - (h_front + h_core))
    x0 = p_bus_w/2.0 + shield_gap

    frontX = place_shape(Part.makeCone(r0, r1, h_front), pos=App.Vector(x0,0,0), rot_axis=App.Vector(0,1,0), rot_deg=90)
    coreX  = place_shape(Part.makeCone(r1, r2, h_core),  pos=App.Vector(x0+h_front,0,0), rot_axis=App.Vector(0,1,0), rot_deg=90)
    backX  = place_shape(Part.makeCone(r2, r3, h_back),  pos=App.Vector(x0+h_front+h_core,0,0), rot_axis=App.Vector(0,1,0), rot_deg=90)

    objs += [
        add_part(doc, frontX, "TPS_Front", color=(0.98,0.98,0.98)),
        add_part(doc, coreX,  "TPS_Core",  color=(0.40,0.40,0.40)),
        add_part(doc, backX,  "TPS_Back",  color=(0.05,0.05,0.05)),
    ]

    # Anillo soporte con aligeramientos
    ring_Z = make_ring(r_outer=(shield_d/2.0 - 12.0), r_inner=(shield_d/2.0 - 18.0), h=3.0)
    hole_r = 2.2
    hole_count = 12
    for i in range(hole_count):
        a = math.radians(360.0/hole_count * i)
        y = (shield_d/2.0 - 15.0) * math.cos(a)
        z = (shield_d/2.0 - 15.0) * math.sin(a)
        hole_cyl = Part.makeCylinder(hole_r, 4.0, App.Vector(0, y, z), App.Vector(1,0,0))
        ring_Z = ring_Z.cut(hole_cyl)
    ring_X = place_shape(ring_Z, pos=App.Vector(x0 - shield_back_standoff, 0, 0), rot_axis=App.Vector(0,1,0), rot_deg=90)
    objs.append(add_part(doc, ring_X, "TPS_SupportRing", color=(0.75,0.75,0.75)))

    # Puntales radiales al bus
    for a in range(0,360,60):
        cyl = Part.makeCylinder(2.6, shield_back_standoff + 6.0, App.Vector(0,0,0), App.Vector(1,0,0))
        cyl = place_shape(cyl, rot_axis=App.Vector(0,1,0), rot_deg=90)
        y = (shield_d/2.0 - 18.0) * math.cos(math.radians(a))
        z = (shield_d/2.0 - 18.0) * math.sin(math.radians(a))
        cyl.translate(App.Vector(x0 - shield_back_standoff, y, z))
        objs.append(add_part(doc, cyl, f"TPS_Strut_{a}", color=(0.75,0.75,0.75)))
    return [o for o in objs if o]

# ===================== Cortina lateral segmentada (protección micrometeoritos) =====================
def build_side_curtain(doc):
    objs = []
    total_t = shield_cc_t + shield_kevl_t + shield_flex_t
    r_outer = max(p_bus_d, p_bus_h)/2.0 + shield_gap_side
    x_base  = p_bus_w/2.0 - 2.0  # arranque justo detrás del bus frontal
    # Anillo continuo
    ring = make_ring(r_outer, r_outer - total_t, shield_rad_len,
                     base=App.Vector(x_base - shield_rad_len, 0, 0), axis=App.Vector(1,0,0))
    # Segmentación: ranuras tangenciales
    slit_len = shield_rad_len + 2.0
    slab_h = 2.2 * r_outer
    for i in range(shield_seg_count):
        ang = 360.0 * i / shield_seg_count
        slot = Part.makeBox(slit_len, shield_slot_w, slab_h,
                            App.Vector(x_base - shield_rad_len, -shield_slot_w/2.0, -slab_h/2.0))
        slot = place_shape(slot, rot_axis=App.Vector(1,0,0), rot_deg=ang)
        ring = cut_safely(ring, slot)
    objs.append(add_part(doc, ring, "SideCurtain", color=(0.55,0.58,0.62), transparency=0.25))
    # Puntales de soporte desde caras ±Y de bus a la cortina
    for j in range(shield_support_rods):
        ang = 360.0 * j / shield_support_rods
        y = r_outer * math.cos(math.radians(ang))
        z = r_outer * math.sin(math.radians(ang))
        rod = Part.makeCylinder(1.6, shield_rad_len * 0.45, App.Vector(x_base - shield_rad_len*0.45, y, z), App.Vector(1,0,0))
        objs.append(add_part(doc, rod, f"CurtainRod_{j}", color=(0.7,0.7,0.72)))
    return objs

# ===================== Panel solar con bisagras =====================
def build_paddle(doc, side=+1):
    objs = []
    plate = make_trapezoid_plate(paddle_len, paddle_root_w, paddle_tip_w, paddle_t)
    hinge = Part.makeCylinder(2.4, 6.0, App.Vector(0,0,0), App.Vector(1,0,0))
    hinge = place_shape(hinge, rot_axis=App.Vector(0,1,0), rot_deg=90)
    arm_len = 15.0
    arm_r = 1.5
    arm = Part.makeCylinder(arm_r, arm_len, App.Vector(0,0,0), App.Vector(1,0,0))
    arm = place_shape(arm, pos=App.Vector(-arm_len/2.0, 0, 0), rot_axis=App.Vector(0,0,1), rot_deg=side*10)

    tilt = paddle_tilt_deg * (1 if side>0 else -1)
    plate_rot = place_shape(plate, rot_axis=App.Vector(0,0,1), rot_deg=tilt)
    hinge_rot = place_shape(hinge, rot_axis=App.Vector(0,0,1), rot_deg=tilt)
    arm_rot   = place_shape(arm,   rot_axis=App.Vector(0,0,1), rot_deg=tilt)

    x = p_bus_w/2.0 - 6.0
    y = side*(paddle_y_offset + paddle_t/2.0 + 2.0)
    z = 0.0
    for sh in (plate_rot, hinge_rot, arm_rot):
        sh.translate(App.Vector(x, y, z))

    # Soporte en el bus
    bracket = Part.makeBox(6.0, 8.0, 12.0)
    bracket.translate(App.Vector(p_bus_w/2.0 - 6.0, y - 4.0, -6.0))

    objs += [
        add_part(doc, plate_rot, f"PaddlePlate_{'R' if side>0 else 'L'}", color=(0.16,0.36,0.76)),
        add_part(doc, hinge_rot, f"PaddleHinge_{'R' if side>0 else 'L'}", color=(0.6,0.6,0.6)),
        add_part(doc, arm_rot,   f"PaddleArm_{'R' if side>0 else 'L'}",   color=(0.5,0.5,0.5)),
        add_part(doc, bracket,   f"PaddleBracket_{'R' if side>0 else 'L'}", color=(0.45,0.45,0.48)),
    ]
    return objs

# ===================== Radiadores con aletas =====================
def build_radiators(doc):
    objs = []
    # Plano base (x detrás del bus, centrado en Y/Z)
    x0 = -p_bus_w/2.0 - radiator_back_offset
    base = Part.makeBox(radiator_w, radiator_t, radiator_h)
    base.translate(App.Vector(x0 - radiator_w/2.0, -radiator_t/2.0, -radiator_h/2.0))
    fins = []
    fin_count = int(radiator_h // radiator_fin_pitch)
    for i in range(fin_count):
        z = -radiator_h/2.0 + i*radiator_fin_pitch
        fin = Part.makeBox(radiator_fin_len, radiator_fin_w, radiator_fin_pitch*0.8)
        fin.translate(App.Vector(x0 - radiator_w/2.0 - radiator_fin_len, -radiator_fin_w/2.0, z - (radiator_fin_pitch*0.8)/2.0))
        fins.append(fin)
    rad = fuse_safely([base] + fins)
    objs.append(add_part(doc, rad, "Radiator_A", color=(0.9,0.3,0.2)))
    # Duplicado desplazado en +Z
    rad2 = rad.copy()
    rad2.translate(App.Vector(0, 0, radiator_h + 22.0))
    objs.append(add_part(doc, rad2, "Radiator_B", color=(0.88,0.32,0.22)))
    return objs

# ===================== Antenas y platos traseros =====================
def build_antennas(doc):
    objs = []
    # Faraday (boom corto lateral +Y)
    far_boom = Part.makeCylinder(faraday_r/3.0, faraday_len, App.Vector(0, p_bus_d/2.0, 0), App.Vector(0,1,0))
    objs.append(add_part(doc, far_boom, "FaradayBoom", color=(0.6,0.6,0.65)))
    # Whip (vertical +Z)
    whip = Part.makeCylinder(whip_r, whip_len, App.Vector(0, 0, p_bus_h/2.0), App.Vector(0,0,1))
    objs.append(add_part(doc, whip, "WhipAntenna", color=(0.2,0.2,0.2)))
    # Plato trasero (paraboloide) con bumper-ring y boom
    dish = make_dish_layer_solid(back_dish_d, back_dish_depth, t=1.4, steps=steps_profile)
    dish = place_shape(dish, pos=App.Vector(-p_bus_w/2.0 - boom_len_back - back_dish_depth, 0, 0),
                       rot_axis=App.Vector(0,1,0), rot_deg=90)
    bumper = make_ring(r_outer=(back_dish_d/2.0), r_inner=(back_dish_d/2.0 - t_bumper_ring), h=t_bumper_ring,
                       base=App.Vector(-p_bus_w/2.0 - boom_len_back - t_bumper_ring, -(back_dish_d/2.0), -(back_dish_d/2.0)),
                       axis=App.Vector(1,0,0))
    boom = Part.makeCylinder(boom_r, boom_len_back, App.Vector(-p_bus_w/2.0 - boom_len_back, 0, 0), App.Vector(1,0,0))
    tip  = Part.makeSphere(boom_tip_r, App.Vector(-p_bus_w/2.0 - boom_len_back - back_dish_depth - 2.0, 0, 0))
    objs += [
        add_part(doc, dish, "BackDish", color=(0.75,0.75,0.78)),
        add_part(doc, bumper, "DishRim", color=(0.5,0.5,0.55)),
        add_part(doc, boom, "DishBoom", color=(0.55,0.55,0.6)),
        add_part(doc, tip, "DishTip", color=(0.3,0.3,0.35)),
    ]
    return objs

# ===================== Tanques, Rueda de reacción, RCS =====================
def build_tanks_and_adcs(doc):
    objs = []
    # Dos tanques cilíndricos laterales en ±Y (eje X)
    x_base = -p_bus_w/2.0 - 10.0
    for sgn in (-1, +1):
        tank = Part.makeCylinder(tank_radius, tank_length, App.Vector(x_base - tank_length, sgn*(p_bus_d/2.0 + tank_radius + 6.0), 0), App.Vector(1,0,0))
        objs.append(add_part(doc, tank, f"Tank_{'P' if sgn<0 else 'S'}", color=(0.82,0.82,0.88)))
    # Rueda de reacción (inside bus, eje X)
    rw = Part.makeCylinder(rwheel_r, rwheel_t, App.Vector(-rwheel_t/2.0, 0, 0), App.Vector(1,0,0))
    objs.append(add_part(doc, rw, "ReactionWheel", color=(0.35,0.35,0.38)))
    # RCS: 6 toberas (±Y y ±Z, en caras)
    # ±Y
    for sgn in (-1, +1):
        base = App.Vector(0, sgn*(p_bus_d/2.0 + 0.5), 0)
        cone = Part.makeCone(rcs_cone_r1, rcs_cone_r2, rcs_cone_h, base, App.Vector(0, sgn, 0))
        objs.append(add_part(doc, cone, f"RCS_Y_{'N' if sgn<0 else 'P'}", color=(0.6,0.6,0.62)))
    # ±Z
    for sgn in (-1, +1):
        base = App.Vector(0, 0, sgn*(p_bus_h/2.0 + 0.5))
        cone = Part.makeCone(rcs_cone_r1, rcs_cone_r2, rcs_cone_h, base, App.Vector(0, 0, sgn))
        objs.append(add_part(doc, cone, f"RCS_Z_{'N' if sgn<0 else 'P'}", color=(0.6,0.6,0.62)))
    return objs

# ===================== Propulsión iónica trasera =====================
def build_ion_ring(doc):
    objs = []
    x0 = -p_bus_w/2.0 - 16.0
    # Aro soporte
    ring = make_ring(ion_ring_R+6.0, ion_ring_R-6.0, 3.0, base=App.Vector(x0-3.0, 0, 0), axis=App.Vector(1,0,0))
    objs.append(add_part(doc, ring, "IonSupportRing", color=(0.55,0.6,0.65)))
    for i in range(ion_count):
        ang = 2*math.pi*i/ion_count
        y = ion_ring_R*math.cos(ang)
        z = ion_ring_R*math.sin(ang)
        body = Part.makeCylinder(ion_body_r, ion_body_L, App.Vector(x0-ion_body_L, y, z), App.Vector(1,0,0))
        grid_o = Part.makeCylinder(ion_grid_r_o, ion_grid_t, App.Vector(x0, y, z), App.Vector(1,0,0))
        grid_i = Part.makeCylinder(ion_grid_r_i, ion_grid_t, App.Vector(x0, y, z), App.Vector(1,0,0))
        grid = cut_safely(grid_o, grid_i)
        noz  = Part.makeCone(ion_nozzle_r1, ion_nozzle_r2, ion_nozzle_L, App.Vector(x0-ion_body_L-ion_nozzle_L, y, z), App.Vector(1,0,0))
        objs += [
            add_part(doc, body, f"IonBody_{i}", color=(0.52,0.55,0.6)),
            add_part(doc, grid, f"IonGrid_{i}", color=(0.62,0.65,0.7)),
            add_part(doc, noz,  f"IonNoz_{i}",  color=(0.45,0.48,0.52)),
        ]
    return objs

# ===================== Ensamblado y exportación =====================
def export_step(objs, path, as_single=False):
    if not objs: return
    try:
        import ImportGui as IG
    except Exception:
        import Import as IG
    if as_single:
        compound = Part.makeCompound([o.Shape for o in objs if hasattr(o, "Shape")])
        tmp = App.ActiveDocument.addObject("Part::Feature", "ExportCompound")
        tmp.Shape = compound
        IG.export([tmp], path)
        try:
            App.ActiveDocument.removeObject(tmp.Name)
        except Exception:
            pass
    else:
        IG.export(objs, path)

def build_spacecraft(doc):
    parts = []
    parts += build_bus(doc)
    parts += build_heat_shield(doc)
    parts += build_side_curtain(doc)
    parts += build_paddle(doc, side=+1)
    parts += build_paddle(doc, side=-1)
    parts += build_radiators(doc)
    parts += build_antennas(doc)
    parts += build_tanks_and_adcs(doc)
    parts += build_ion_ring(doc)
    return [p for p in parts if p is not None]

def main():
    doc = App.ActiveDocument
    if doc is None:
        doc = App.newDocument("Satellite_Compact")
    objs = build_spacecraft(doc)
    doc.recompute()
    export_step(objs, export_path, export_as_single_compound)
    return doc, objs

if __name__ == "__main__":
    main()
