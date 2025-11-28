UtilidadCohete3DNOIMP.py
import math
import FreeCAD as App
import Part

# ===================== Parámetros globales (mm) =====================
# Escala general
scale = 0.7  # compacta por defecto; ajusta 0.4–1.0

# Núcleo presurizado tipo “estación”
core_L = 14000.0 * scale   # longitud del hábitat (antes 18000)
core_R = 2000.0  * scale   # radio exterior (antes 2200)
hull_t = 28.0    * scale   # grosor del casco (antes 35)

# Escudo Whipple (micrometeoritos)
whipple_layers = 3           # número de capas
whipple_gap    = 90.0*scale  # separación entre capas
whipple_thk    = 6.0*scale   # grosor de cada bumper
whipple_extra_L = 300.0*scale  # sobresalir respecto al hábitat

# Escudo frontal tipo bumper / TPS (dirección +X)
tps_D   = 1.6 * (2.0*core_R)  # diámetro del disco frontal
tps_thk = 60.0 * scale
tps_standoff = 600.0 * scale  # separación respecto al casco

# Nodo de atraque frontal
node_L = 1800.0 * scale
node_R = 1400.0 * scale
port_R = 600.0  * scale
port_t = 40.0   * scale
docking_ports = 4            # 4 puertos radiales

# Cúpula y ventanas
cupola_R      = 700.0  * scale
cupola_thk    = 10.0   * scale
window_R      = 200.0  * scale
window_count  = 8

# Esclusa (lateral)
airlock_L = 2000.0 * scale
airlock_R = 800.0  * scale

# Estructura de celosía (backbone corto)
truss_L = 16000.0 * scale
truss_W = 3200.0  * scale
truss_H = 3200.0  * scale
beam_w  = 180.0   * scale

# Alas solares (retraíbles conceptualmente)
sa_span       = 12000.0 * scale   # semienvergadura cada ala
sa_chord      = 4200.0  * scale
sa_thk        = 50.0    * scale
sa_panel_divs = 5

# Radiadores
rad_W   = 9000.0 * scale
rad_H   = 3400.0 * scale
rad_thk = 35.0   * scale
rad_sep = 1800.0 * scale

# Tanques esféricos exteriores
tank_R     = 700.0  * scale
tank_rows  = 2
tank_cols  = 3
tank_ax_dx = 3600.0 * scale
tank_y_off = 2200.0 * scale

# Comunicación
hga_dish_D    = 3600.0 * scale
hga_dish_dep  = 700.0  * scale
hga_boom_L    = 2400.0 * scale
mga_dish_D    = 1400.0 * scale
mga_dish_dep  = 260.0  * scale

# Propulsión química (cluster)
chem_noz_R1 = 800.0  * scale
chem_noz_R2 = 180.0  * scale
chem_noz_L  = 1500.0 * scale
chem_count  = 4
chem_ring_R = 1500.0 * scale

# Propulsión iónica (anillo)
ion_body_r   = 460.0  * scale
ion_body_L   = 800.0  * scale
ion_grid_r_o = 620.0  * scale
ion_grid_r_i = 460.0  * scale
ion_grid_t   = 36.0   * scale
ion_noz_r1   = 460.0  * scale
ion_noz_r2   = 160.0  * scale
ion_noz_L    = 360.0  * scale
ion_count    = 8
ion_ring_R   = 2200.0 * scale

# Brazos robóticos
arm_seg_L = 2200.0 * scale
arm_seg_R = 160.0  * scale
arm_base_R = 240.0 * scale

# Exportación
try:
    user_dir = App.getUserAppDataDir()
except Exception:
    user_dir = ""
export_path = user_dir + "MiniISS_ParkerProbe.step"
export_as_single_compound = False

# ===================== Utilidades =====================
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

def make_ring(r_outer, r_inner, h, axis=App.Vector(1,0,0), base=App.Vector(0,0,0)):
    cyl_o = Part.makeCylinder(r_outer, h, base, axis)
    cyl_i = Part.makeCylinder(r_inner, h, base, axis)
    return cyl_o.cut(cyl_i)

def fuse_safely(shapes):
    shapes = [s for s in shapes if s is not None]
    if not shapes: return None
    acc = shapes[0]
    for s in shapes[1:]:
        try:
            acc = acc.fuse(s)
        except Exception:
            try:
                acc = acc.compound([acc, s])
            except Exception:
                pass
    return acc

def cut_safely(a, b):
    try:
        return a.cut(b)
    except Exception:
        return a

def make_paraboloid(d, depth, steps=96):
    if d <= 0 or depth <= 0: return None
    pts = []
    rmax = d/2.0
    f = (rmax*rmax)/(4.0*depth)
    for i in range(steps+1):
        z = depth * i/steps
        r = math.sqrt(max(0.0, 4.0*f*z))
        pts.append(App.Vector(r, 0, z))
    wire = Part.Wire(Part.makePolygon([App.Vector(0,0,0)] + pts + [App.Vector(0,0,depth)]))
    face = Part.Face(wire)
    return face.revolve(App.Vector(0,0,0), App.Vector(0,0,1), 360)

# ===================== Módulos =====================
def build_habitat_shell():
    # Casco cilíndrico hueco + tapas esféricas interiores
    cyl_o = Part.makeCylinder(core_R, core_L, App.Vector(-core_L/2.0, 0, 0), App.Vector(1,0,0))
    cyl_i = Part.makeCylinder(core_R - hull_t, core_L - 2*hull_t, App.Vector(-core_L/2.0 + hull_t, 0, 0), App.Vector(1,0,0))
    shell = cyl_o.cut(cyl_i)

    sph_R = core_R - hull_t
    cap_front = Part.makeSphere(sph_R, App.Vector(core_L/2.0 - hull_t, 0, 0))
    cap_back  = Part.makeSphere(sph_R,  App.Vector(-core_L/2.0 + hull_t, 0, 0))

    big = 10*max(core_L, core_R)
    box_front = Part.makeBox(big, big, big, App.Vector(core_L/2.0 - hull_t - big, -big/2.0, -big/2.0))
    box_back  = Part.makeBox(big, big, big, App.Vector(-core_L/2.0 + hull_t, -big/2.0, -big/2.0))
    cap_front = cap_front.common(box_front)
    cap_back  = cap_back.common(box_back)

    pressure_vessel = fuse_safely([shell, cap_front, cap_back])

    # Ventanas: taladros cilíndricos
    win_positions = []
    for i in range(window_count):
        theta = 2*math.pi * i / window_count
        y = (core_R - hull_t - 200.0*scale) * math.cos(theta)
        z = (core_R - hull_t - 200.0*scale) * math.sin(theta)
        x = 0
        win_positions.append((x, y, z))

    for (x, y, z) in win_positions:
        cutter = Part.makeCylinder(window_R, core_L + 2*hull_t, App.Vector(-core_L/2.0 - hull_t, y, z), App.Vector(1,0,0))
        pressure_vessel = cut_safely(pressure_vessel, cutter)

    # Cúpula inferior
    cup_center = App.Vector(0, 0, -(core_R - hull_t))
    cup = Part.makeSphere(cupola_R, cup_center)
    cup_cut_box = Part.makeBox(4*cupola_R, 4*cupola_R, 4*cupola_R, App.Vector(-2*cupola_R, -2*cupola_R, cup_center.z))
    cup = cup.common(cup_cut_box)

    return pressure_vessel, cup

def build_whipple_shield():
    # Capas concéntricas (cyl + hemi) exteriores al hábitat
    layers = []
    base_R = core_R + 0.5*whipple_gap
    total_L = core_L + whipple_extra_L
    for i in range(whipple_layers):
        r_o = base_R + i*(whipple_gap)
        # cilindro fino
        shell_o = Part.makeCylinder(r_o, total_L, App.Vector(-total_L/2.0, 0, 0), App.Vector(1,0,0))
        shell_i = Part.makeCylinder(r_o - whipple_thk, total_L - 2*whipple_thk,
                                    App.Vector(-total_L/2.0 + whipple_thk, 0, 0), App.Vector(1,0,0))
        shell_layer = shell_o.cut(shell_i)
        # tapas hemisféricas finas
        sph_Ro = r_o
        sph_Ri = r_o - whipple_thk
        cap_f_o = Part.makeSphere(sph_Ro, App.Vector(total_L/2.0 - whipple_thk, 0, 0))
        cap_b_o = Part.makeSphere(sph_Ro, App.Vector(-total_L/2.0 + whipple_thk, 0, 0))
        cap_f_i = Part.makeSphere(sph_Ri, App.Vector(total_L/2.0 - whipple_thk, 0, 0))
        cap_b_i = Part.makeSphere(sph_Ri, App.Vector(-total_L/2.0 + whipple_thk, 0, 0))
        big = 10*max(total_L, r_o)
        box_front = Part.makeBox(big, big, big, App.Vector(total_L/2.0 - whipple_thk - big, -big/2.0, -big/2.0))
        box_back  = Part.makeBox(big, big, big, App.Vector(-total_L/2.0 + whipple_thk, -big/2.0, -big/2.0))
        cap_f = (cap_f_o.common(box_front)).cut(cap_f_i.common(box_front))
        cap_b = (cap_b_o.common(box_back )).cut(cap_b_i.common(box_back ))
        layer = fuse_safely([shell_layer, cap_f, cap_b])
        layers.append(layer)
    return fuse_safely(layers)

def build_front_tps():
    # Disco frontal desplazado (dirección +X), con soporte de brazos
    disc_R = tps_D/2.0
    disc = Part.makeCylinder(disc_R, tps_thk, App.Vector(core_L/2.0 + tps_standoff, -disc_R, -disc_R), App.Vector(1,0,0))
    # 4 puntales de soporte
    struts = []
    for ang in [0, 90, 180, 270]:
        a = math.radians(ang)
        y = (core_R * 0.7) * math.cos(a)
        z = (core_R * 0.7) * math.sin(a)
        Ls = tps_standoff
        rod = Part.makeCylinder(120.0*scale, Ls, App.Vector(core_L/2.0, y, z), App.Vector(1,0,0))
        struts.append(rod)
    return fuse_safely([disc] + struts)

def build_docking_node():
    body = Part.makeCylinder(node_R, node_L, App.Vector(core_L/2.0 + node_L*(-0.5), 0, 0), App.Vector(1,0,0))
    # Puerto axial
    axial_cut = Part.makeCylinder(port_R, node_L + 2*port_t, App.Vector(core_L/2.0 - port_t, 0, 0), App.Vector(1,0,0))
    body = cut_safely(body, axial_cut)
    # Puertos radiales
    cuts = []
    for i in range(docking_ports):
        theta = 2*math.pi*i/docking_ports
        y = (node_R - port_R - port_t) * math.cos(theta)
        z = (node_R - port_R - port_t) * math.sin(theta)
        cutr = Part.makeCylinder(port_R, 2*node_R + 2*port_t, App.Vector(core_L/2.0 - node_L/2.0, y - node_R - port_t, z), App.Vector(0,1,0))
        cuts.append(cutr)
    for c in cuts:
        body = cut_safely(body, c)
    # Aro de refuerzo
    flange = make_ring(node_R+60.0*scale, node_R-60.0*scale, 200.0*scale, App.Vector(1,0,0),
                       App.Vector(core_L/2.0 - 100.0*scale, 0, 0))
    return fuse_safely([body, flange])

def build_airlock():
    # Cilindro lateral con eje Z -> X rotado
    body = Part.makeCylinder(airlock_R, airlock_L, App.Vector(0, core_R, -airlock_L/2.0), App.Vector(0,0,1))
    # Unión al casco: boquilla de transición (anillo)
    sleeve = make_ring(airlock_R+60.0*scale, airlock_R-40.0*scale, 200.0*scale, App.Vector(0,0,1),
                       App.Vector(0, core_R, -100.0*scale))
    return fuse_safely([body, sleeve])

def build_truss():
    # 4 vigas longitudinales + diagonales simplificadas
    beams = []
    for sy in [-1, 1]:
        for sz in [-1, 1]:
            base = App.Vector(-truss_L/2.0, sy*(truss_W/2.0 - beam_w/2.0), sz*(truss_H/2.0 - beam_w/2.0))
            beam = Part.makeBox(truss_L, beam_w, beam_w, base)
            beams.append(beam)
    # Diagonales por tramos
    segments = 6
    segL = truss_L/segments
    for k in range(segments):
        x0 = -truss_L/2.0 + k*segL
        # diagonales en plano YZ=+ y -= - (dos caras)
        diag1 = Part.makeBox(segL, beam_w, beam_w, App.Vector(x0, -truss_W/2.0, -truss_H/2.0))
        diag1.Placement.Rotation = App.Rotation(App.Vector(1,0,0), 0)
        diag1 = place_shape(diag1, App.Vector(0,0,0), App.Vector(0,1,0), 0)
        beams.append(diag1)
    return fuse_safely(beams)

def build_solar_arrays():
    # Dos alas a ±Y
    panels = []
    for sy in [-1, 1]:
        base = App.Vector(0, sy*(core_R + 300.0*scale), -sa_thk/2.0)
        panel = Part.makeBox(sa_span, sa_chord, sa_thk, base)
        panel = place_shape(panel, App.Vector(-sa_span/2.0, 0, 0))
        # "bisagra" simple
        hinge = Part.makeCylinder(140.0*scale, 400.0*scale, App.Vector(0, sy*(core_R+100.0*scale), -200.0*scale), App.Vector(1,0,0))
        panels += [panel, hinge]
    return fuse_safely(panels)

def build_radiators():
    # Dos radiadores a ±Z
    plates = []
    for sz in [-1, 1]:
        base = App.Vector(-rad_W/2.0, rad_sep, sz*(core_R + 400.0*scale))
        plate = Part.makeBox(rad_W, rad_H, rad_thk, base)
        # soporte
        strut = Part.makeBox(600.0*scale, 200.0*scale, 200.0*scale, App.Vector(-300.0*scale, rad_sep - 200.0*scale, sz*(core_R + 300.0*scale)))
        plates += [plate, strut]
    return fuse_safely(plates)

def build_tanks():
    tanks = []
    dx0 = - (tank_cols-1)*tank_ax_dx/2.0
    for i in range(tank_cols):
        for j in range(tank_rows):
            x = dx0 + i*tank_ax_dx
            y = tank_y_off * (1 if j%2==0 else -1)
            s = Part.makeSphere(tank_R, App.Vector(x, y, 0))
            tanks.append(s)
    return fuse_safely(tanks)

def build_comms():
    # HGA en brazo lateral +X, +Y
    dish = make_paraboloid(hga_dish_D, hga_dish_dep)
    dish = place_shape(dish, App.Vector(core_L/2.0 - 800.0*scale, core_R + 1200.0*scale, 0), App.Vector(0,1,0), 90)
    boom = Part.makeCylinder(120.0*scale, hga_boom_L, App.Vector(core_L/2.0 - hga_boom_L, core_R + 1200.0*scale, 0), App.Vector(1,0,0))
    # MGA en el lado opuesto
    dish2 = make_paraboloid(mga_dish_D, mga_dish_dep)
    dish2 = place_shape(dish2, App.Vector(0, -(core_R + 1100.0*scale), 0), App.Vector(0,1,0), 90)
    return fuse_safely([dish, boom, dish2])

def make_truncated_cone(r1, r2, h, axis=App.Vector(1,0,0), base=App.Vector(0,0,0)):
    # Cono truncado por revolución
    p1 = App.Vector(0, 0, 0)
    p2 = App.Vector(h, 0, 0)
    # modelamos con sólidos: usar Part API directly
    cone = Part.makeCone(r1, r2, h, base, axis)
    return cone

def build_chemical_propulsion():
    # Cluster en la popa (-X)
    engines = []
    x0 = -core_L/2.0 - 400.0*scale
    for i in range(chem_count):
        ang = 2*math.pi*i/chem_count
        y = chem_ring_R*math.cos(ang)
        z = chem_ring_R*math.sin(ang)
        noz = make_truncated_cone(chem_noz_R1, chem_noz_R2, chem_noz_L, App.Vector(1,0,0), App.Vector(x0 - chem_noz_L, y, z))
        engines.append(noz)
    plate = Part.makeCylinder(chem_ring_R+600.0*scale, 80.0*scale, App.Vector(x0 - 80.0*scale, 0, 0), App.Vector(1,0,0))
    return fuse_safely([plate] + engines)

def build_ion_ring():
    # Anillo de thrusters iónicos en popa
    parts = []
    x0 = -core_L/2.0 + 600.0*scale
    ring = make_ring(ion_ring_R+160.0*scale, ion_ring_R-160.0*scale, 200.0*scale, App.Vector(1,0,0), App.Vector(x0-100.0*scale, 0, 0))
    parts.append(ring)
    for i in range(ion_count):
        ang = 2*math.pi*i/ion_count
        y = ion_ring_R*math.cos(ang)
        z = ion_ring_R*math.sin(ang)
        body = Part.makeCylinder(ion_body_r, ion_body_L, App.Vector(x0, y, z), App.Vector(1,0,0))
        grid_o = Part.makeCylinder(ion_grid_r_o, ion_grid_t, App.Vector(x0+ion_body_L, y, z), App.Vector(1,0,0))
        grid_i = Part.makeCylinder(ion_grid_r_i, ion_grid_t, App.Vector(x0+ion_body_L, y, z), App.Vector(1,0,0))
        grid = grid_o.cut(grid_i)
        noz  = make_truncated_cone(ion_noz_r1, ion_noz_r2, ion_noz_L, App.Vector(1,0,0), App.Vector(x0-ion_noz_L, y, z))
        parts += [body, grid, noz]
    return fuse_safely(parts)

def build_robotic_arm():
    base = Part.makeCylinder(arm_base_R, 200.0*scale, App.Vector(0, core_R-100.0*scale, core_R-300.0*scale), App.Vector(0,0,1))
    seg1 = Part.makeCylinder(arm_seg_R, arm_seg_L, App.Vector(0, core_R-100.0*scale, core_R-300.0*scale), App.Vector(0,0,1))
    seg2 = Part.makeCylinder(arm_seg_R, arm_seg_L, App.Vector(0, core_R-100.0*scale, core_R-300.0*scale+arm_seg_L), App.Vector(0,1,0))
    claw = Part.makeSphere(arm_seg_R*0.9, App.Vector(arm_seg_L, core_R-100.0*scale, core_R-300.0*scale+arm_seg_L))
    return fuse_safely([base, seg1, seg2, claw])

# ===================== Ensamblado =====================
def build_spacecraft(doc):
    parts = []

    # Hábitat + cúpula
    hull, cup = build_habitat_shell()
    parts.append(add_part(doc, hull, "HabitatHull", color=(0.86,0.86,0.88)))
    parts.append(add_part(doc, cup,  "Cupola",      color=(0.2,0.4,0.9), transparency=0.7))

    # Whipple shield
    shield = build_whipple_shield()
    parts.append(add_part(doc, shield, "WhippleShield", color=(0.55,0.55,0.6), transparency=0.35))

    # Escudo frontal / TPS
    tps = build_front_tps()
    parts.append(add_part(doc, tps, "FrontBumperTPS", color=(0.25,0.25,0.25)))

    # Nodo de atraque frontal
    node = build_docking_node()
    parts.append(add_part(doc, node, "DockingNode", color=(0.8,0.8,0.85)))

    # Esclusa lateral
    airlock = build_airlock()
    parts.append(add_part(doc, airlock, "Airlock", color=(0.78,0.78,0.8)))

    # Truss corto posterior (para radiadores, antenas, tanques)
    truss = build_truss()
    truss = place_shape(truss, App.Vector(-core_L/2.0 - truss_L/2.0 - 400.0*scale, 0, 0))
    parts.append(add_part(doc, truss, "Truss", color=(0.7,0.7,0.72)))

    # Paneles solares
    sa = build_solar_arrays()
    parts.append(add_part(doc, sa, "SolarArrays", color=(0.15,0.25,0.85)))

    # Radiadores
    rads = build_radiators()
    rads = place_shape(rads, App.Vector(-core_L/4.0, 0, 0))
    parts.append(add_part(doc, rads, "Radiators", color=(0.9,0.3,0.2)))

    # Tanques exteriores sobre el truss
    tanks = build_tanks()
    tanks = place_shape(tanks, App.Vector(-core_L/2.0 - truss_L/2.0 - 400.0*scale, 0, 0))
    parts.append(add_part(doc, tanks, "ExternalTanks", color=(0.85,0.85,0.9)))

    # Comunicaciones
    comms = build_comms()
    parts.append(add_part(doc, comms, "Comms", color=(0.6,0.6,0.65)))

    # Propulsión química
    chem = build_chemical_propulsion()
    parts.append(add_part(doc, chem, "ChemProp", color=(0.5,0.5,0.55)))

    # Propulsión iónica
    ion = build_ion_ring()
    parts.append(add_part(doc, ion, "IonProp", color=(0.55,0.6,0.65)))

    # Brazo robótico
    arm = build_robotic_arm()
    parts.append(add_part(doc, arm, "RoboticArm", color=(0.85,0.85,0.6)))

    return [p for p in parts if p is not None]

def export_step(objs, path, as_single=False):
    if not objs: return
    try:
        import ImportGui as IG
    except Exception:
        import Import as IG
    if as_single:
        compound = Part.makeCompound([o.Shape for o in objs])
        tmp = App.ActiveDocument.addObject("Part::Feature", "ExportCompound")
        tmp.Shape = compound
        IG.export([tmp], path)
        try:
            App.ActiveDocument.removeObject(tmp.Name)
        except Exception:
            pass
    else:
        IG.export(objs, path)

# ===================== Ejecutar =====================
def main():
    doc = App.ActiveDocument
    if doc is None:
        doc = App.newDocument("MiniISS_ParkerProbe")
    objs = build_spacecraft(doc)
    doc.recompute()
    export_step(objs, export_path, export_as_single_compound)
    return doc, objs

if __name__ == "__main__":
    main()