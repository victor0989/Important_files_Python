CorregirStarSatFusion.py
# Macro: StarSat_Fusion (Víctor)
# Requiere FreeCAD con Workbench Part
import FreeCAD as App, FreeCADGui as Gui
import Part, math, random

doc = App.newDocument("StarSat_Fusion")
random.seed(42)

# ---------------------------
# PARÁMETROS
# ---------------------------
P = dict(
    # Modos / toggles
    enable_ship_shell=True,
    enable_engines=True,
    enable_turrets=True,
    enable_greebles=True,
    enable_armor=True,
    enable_radiators=True,
    enable_reinforced_panels=True,
    enable_sunshield=True,          # escudo/parasol solar frontal
    enable_hyper_ring=True,
    # Bus base (mm)
    bus_w=60.0, bus_d=60.0, bus_h=80.0,
    # Paneles
    panel_len=180.0, panel_w=50.0, panel_t=2.0,
    panel_segments=3, panel_deploy_deg=35.0,
    # HGA (parábola)
    dish_diameter=60.0, dish_depth=12.0, dish_thickness=1.2, boom_len=45.0,
    # RCS thrusters
    thruster_h=12.0, thruster_r1=4.0, thruster_r2=1.6,
    # Casco nave (geom/estética)
    hull_scale=1.22, prow_len=90.0, stern_len=62.0, deck_thk=3.0,
    fin_span=120.0, fin_t=3.0, fin_sweep=20.0, fin_dihedral=12.0,
    # Motores principales
    engine_count=2, engine_len=95.0, engine_r=14.0,
    # Anillo “hiperdrive” / acoplamientos
    hyper_ring_Do=140.0, hyper_ring_Di=100.0, hyper_ring_t=6.0,
    hyper_n=12, hyper_pcd=120.0, bolt_r=2.0,
    dock_top_Do=80.0, dock_top_Di=56.0, dock_bot_Do=70.0, dock_bot_Di=45.0,
    # Blindaje Whipple / meteoritos
    shield_layers=3, armor_thk=4.0, shield_gap=12.0,
    # Radiadores
    radiator_w=90.0, radiator_h=130.0, radiator_t=3.0, fin_step=6.0, fin_t=1.2,
    # Parasol/escudo solar frontal (+X es Sol)
    sunshield_d=220.0, sunshield_thk=8.0, sunshield_cone=16.0, sunshield_gap=28.0,
    # Reforzado paneles
    panel_frame_over=4.0, coverglass_t=0.6,
    # Torretas (look nave)
    turret_r=8.0, turret_h=10.0, cannon_len=24.0, cannon_r=2.2,
    # Greebles
    greeble_density=0.45,
    # Colores
    col_hull=(0.75,0.76,0.78),
    col_panel=(0.06,0.08,0.20),
    col_metal=(0.70,0.70,0.72),
    col_greeble=(0.55,0.56,0.58),
    col_glow=(0.15,0.40,1.00),
    col_armor=(0.60,0.62,0.65),
    col_radiator=(0.88,0.90,0.95),
)

# ---------------------------
# HELPERS
# ---------------------------
def add_obj(shape, name, color=None, group=None):
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    if color: obj.ViewObject.ShapeColor = color
    if group: group.addObject(obj)
    return obj

def T(shape, v):
    m = App.Matrix(); m.move(App.Vector(*v))
    return shape.transformGeometry(m)

def R(shape, axis, ang, center=(0,0,0)):
    return shape.rotate(App.Vector(*center), App.Vector(*axis), ang)

def centered_box(w,d,h):
    return T(Part.makeBox(w,d,h), (-w/2.0,-d/2.0,-h/2.0))

def cyl(h, r, axis='Z', center=False):
    c = Part.makeCylinder(r, h)
    if axis=='X': c = R(c,(0,1,0),90)
    if axis=='Y': c = R(c,(1,0,0),90)
    if center:
        if axis=='Z': c = T(c,(0,0,-h/2))
        if axis=='X': c = T(c,(-h/2,0,0))
        if axis=='Y': c = T(c,(0,-h/2,0))
    return c

def cone(r1, r2, h, axis='Z', center=False):
    c = Part.makeCone(r1, r2, h)
    if axis=='X': c = R(c,(0,1,0),90)
    if axis=='Y': c = R(c,(1,0,0),90)
    if center:
        if axis=='Z': c = T(c,(0,0,-h/2))
        if axis=='X': c = T(c,(-h/2,0,0))
        if axis=='Y': c = T(c,(0,-h/2,0))
    return c

def ring(h, Do, Di, axis='Z', center=False):
    outer = cyl(h, Do/2.0, axis=axis, center=center)
    inner = cyl(h+0.2, Di/2.0, axis=axis, center=center)
    return outer.cut(inner)

def poly_prism(points, h):  # extrusión centrada en Z
    wire = Part.makePolygon([App.Vector(x,y,0) for (x,y) in points] + [App.Vector(points[0][0],points[0][1],0)])
    face = Part.Face(wire)
    solid = face.extrude(App.Vector(0,0,h))
    return T(solid, (0,0,-h/2.0))

def parabola_dish(d, depth, t, steps=48):
    rmax = d/2.0
    a = depth/(rmax*rmax)
    curve_in = [(r, a*r*r) for r in [rmax*i/steps for i in range(0, steps+1)]]
    curve_out = [(r, a*r*r + t) for r in [rmax*i/steps for i in range(steps, -1, -1)]]
    profile = [(0,0)] + curve_in + curve_out + [(0,t)]
    pts = [App.Vector(x,0,z) for (x,z) in profile]
    wire = Part.makePolygon(pts+[pts[0]])
    face = Part.Face(wire)
    return face.revolve(App.Vector(0,0,0), App.Vector(0,0,1), 360)

def polar(n, radius, start=0.0):
    for i in range(n):
        ang = math.radians(start + i*360.0/n)
        yield (radius*math.cos(ang), radius*math.sin(ang))

def place_about_point(obj, axis_vec, angle_deg, center_vec):
    obj.Placement = App.Placement(App.Vector(*center_vec), App.Rotation(App.Vector(*axis_vec), angle_deg), App.Vector(*center_vec))

def rand(a,b): return a + (b-a)*random.random()

# ---------------------------
# GRUPOS
# ---------------------------
g_root  = doc.addObject("App::DocumentObjectGroup", "StarSat_Fusion")
g_bus   = doc.addObject("App::DocumentObjectGroup", "Bus_and_Systems"); g_root.addObject(g_bus)
g_ship  = doc.addObject("App::DocumentObjectGroup", "ShipShell"); g_root.addObject(g_ship)
g_weap  = doc.addObject("App::DocumentObjectGroup", "Turrets"); g_root.addObject(g_weap)
g_acpl  = doc.addObject("App::DocumentObjectGroup", "Acoplamientos"); g_root.addObject(g_acpl)
g_pan   = doc.addObject("App::DocumentObjectGroup", "SolarArrays"); g_root.addObject(g_pan)
g_gree  = doc.addObject("App::DocumentObjectGroup", "Greebles"); g_root.addObject(g_gree)
g_armor = doc.addObject("App::DocumentObjectGroup", "Armor_and_Shields"); g_root.addObject(g_armor)
g_therm = doc.addObject("App::DocumentObjectGroup", "Thermal"); g_root.addObject(g_therm)

# ---------------------------
# 1) BUS CENTRAL
# ---------------------------
bus = add_obj(centered_box(P['bus_w'], P['bus_d'], P['bus_h']), "Bus", P['col_hull'], g_bus)

# ---------------------------
# 2) CASCO/ALA ESTILO NAVE
# ---------------------------
if P['enable_ship_shell']:
    half_w = P['bus_w']*P['hull_scale']/2.0
    half_d = P['bus_d']*P['hull_scale']/2.0
    hull_h = P['bus_h']*P['hull_scale']

    prow = poly_prism([
        (-P['prow_len']*0.2, -half_d*0.60),
        ( P['prow_len']*0.8,  -half_d*0.15),
        ( P['prow_len']*0.8,   half_d*0.15),
        (-P['prow_len']*0.2,   half_d*0.60),
    ], hull_h)
    stern = poly_prism([
        (-P['stern_len']*0.6, -half_d*0.50),
        ( P['stern_len']*0.6, -half_d*0.35),
        ( P['stern_len']*0.6,  half_d*0.35),
        (-P['stern_len']*0.6,  half_d*0.50),
    ], hull_h)
    prow  = T(prow,  ( P['bus_w']/2.0 + 10.0, 0, 0))
    stern = T(stern, (-P['bus_w']/2.0 - 10.0, 0, 0))
    deck  = centered_box(P['bus_w']*P['hull_scale']+P['prow_len']+P['stern_len'], P['bus_d']*P['hull_scale']*0.9, P['deck_thk'])
    hull  = Part.makeCompound([prow, stern, deck])
    add_obj(hull, "Ship_Hull", P['col_hull'], g_ship)

    # Aletas
    fin_points = [
        (0, -P['fin_span']/2.0),
        (P['fin_span']*0.45, -P['fin_span']*0.12),
        (P['fin_span']*0.55,  P['fin_span']*0.12),
        (0,  P['fin_span']/2.0),
    ]
    fin = poly_prism(fin_points, P['fin_t'])
    fin = R(fin, (0,1,0), P['fin_sweep'])
    fin = R(fin, (1,0,0), P['fin_dihedral'])
    finL = T(fin, ( P['bus_w']/2.0, 0, 0))
    finR = T(R(fin,(0,0,1),180), (-P['bus_w']/2.0, 0, 0))
    add_obj(finL, "Fin_Left", P['col_hull'], g_ship)
    add_obj(finR, "Fin_Right", P['col_hull'], g_ship)

# ---------------------------
# 3) SISTEMAS SATELITALES (PANELES, HGA, RCS)
# ---------------------------
# Paneles solares con refuerzo
seg_len = P['panel_len']/float(P['panel_segments'])
seg_core  = centered_box(seg_len, P['panel_w'], P['panel_t'])
skin      = centered_box(seg_len-3, P['panel_w']-3, P['panel_t']/2.0)
skin      = T(skin, (0,0, -P['panel_t']/2.0 + P['panel_t']/8.0))
parts = [seg_core, skin]
if P['enable_reinforced_panels']:
    frame = centered_box(seg_len+P['panel_frame_over'], P['panel_w']+P['panel_frame_over'], P['panel_t']/2.0)
    cover = centered_box(seg_len-2, P['panel_w']-2, P['coverglass_t'])
    cover = T(cover, (0,0, P['panel_t']/2.0 + P['coverglass_t']/2.0))
    parts.extend([frame, cover])
segment = Part.Compound(parts)

wing = Part.makeCompound([T(segment, (i*(seg_len+1.5)+seg_len/2.0, 0, 0)) for i in range(P['panel_segments'])])
hinge = cyl(5.0, 2.8, axis='X', center=True)
wing  = Part.Compound([wing, T(hinge, (-2.0, 0, 0))])

pivotL = (-P['bus_w']/2.0, 0, 0)
pivotR = ( P['bus_w']/2.0, 0, 0)
wingL = T(wing, (-1.0 - P['bus_w']/2.0, 0, 0))
wingR = T(wing, ( 1.0 + P['bus_w']/2.0, 0, 0))
objL = add_obj(wingL, "Solar_Left", P['col_panel'], g_pan)
objR = add_obj(wingR, "Solar_Right", P['col_panel'], g_pan)
place_about_point(objL, (0,1,0),  P['panel_deploy_deg'], pivotL)
place_about_point(objR, (0,1,0), -P['panel_deploy_deg'], pivotR)

# HGA: boom + cardán + plato parabólico + parasol local
boom = T(cyl(P['boom_len'], 1.8, axis='X', center=False), (P['bus_w']/2.0, 0, 0))
add_obj(boom, "HGA_Boom", P['col_metal'], g_bus)
g1 = ring(3.0, 34.0, 34.0-5.0, axis='Z', center=True)
g2 = ring(3.0, 28.0, 28.0-5.0, axis='X', center=True)
gimbal = T(Part.Compound([g1,g2]), (P['bus_w']/2.0 + P['boom_len'], 0, 0))
add_obj(gimbal, "HGA_Gimbal", P['col_metal'], g_bus)
dish = parabola_dish(P['dish_diameter'], P['dish_depth'], P['dish_thickness'])
dish = R(dish, (0,1,0), -18)
dish = T(dish, (P['bus_w']/2.0 + P['boom_len'], 0, 0))
add_obj(dish, "HGA_Dish", (1,1,1), g_bus)
# parasol local (aros finos delante del plato)
shade = ring(1.8, P['dish_diameter']*0.75, P['dish_diameter']*0.70, axis='Z', center=True)
shade = T(shade, (P['bus_w']/2.0 + P['boom_len']+2.0, 0, P['dish_diameter']*0.15))
add_obj(shade, "HGA_Sunshade", (0.2,0.2,0.22), g_therm)

# RCS en esquinas superior e inferior
corners = [(1,1),(1,-1),(-1,1),(-1,-1)]
for i,(sx,sy) in enumerate(corners):
    thr = cone(P['thruster_r1'], P['thruster_r2'], P['thruster_h'], axis='X', center=False)
    housing = cyl(P['thruster_h']+4, P['thruster_r1']+2, axis='X', center=False)
    thr_top = T(thr,     (sx*P['bus_w']/2.0, sy*P['bus_d']/2.0,  P['bus_h']/2.0))
    hous_t  = T(housing, (sx*P['bus_w']/2.0, sy*P['bus_d']/2.0,  P['bus_h']/2.0))
    thr_bot = T(R(thr,(1,0,0),180),     (sx*P['bus_w']/2.0, sy*P['bus_d']/2.0, -P['bus_h']/2.0))
    hous_b  = T(housing, (sx*P['bus_w']/2.0, sy*P['bus_d']/2.0, -P['bus_h']/2.0))
    add_obj(hous_t, f"RCS_Housing_T_{i+1}", (0.5,0.5,0.52), g_bus)
    add_obj(thr_top, f"RCS_Top_{i+1}", P['col_metal'], g_bus)
    add_obj(hous_b, f"RCS_Housing_B_{i+1}", (0.5,0.5,0.52), g_bus)
    add_obj(thr_bot, f"RCS_Bot_{i+1}", P['col_metal'], g_bus)

# ---------------------------
# 4) ACOPLAMIENTOS (anillos y pernos)
# ---------------------------
if P['enable_hyper_ring']:
    hyper = ring(P['hyper_ring_t'], P['hyper_ring_Do'], P['hyper_ring_Di'], axis='Y', center=True)
    hyper = T(hyper, (P['bus_w']/2.0 + P['prow_len'] + 15.0, 0, 0))
    add_obj(hyper, "HyperRing", P['col_metal'], g_acpl)
    bolts = []
    for (y,z) in polar(P['hyper_n'], P['hyper_pcd']/2.0, start=0.0):
        b = cyl(6.0, P['bolt_r'], axis='Y', center=True)
        bolts.append(T(b, (P['bus_w']/2.0 + P['prow_len'] + 15.0, y, z)))
    add_obj(Part.makeCompound(bolts), "HyperRing_Bolts", P['col_metal'], g_acpl)

# Puerto superior e inferior
dock_top = ring(4.0, P['dock_top_Do'], P['dock_top_Di'], axis='Z', center=True)
dock_top = T(dock_top, (0,0,P['bus_h']/2.0+4.0))
add_obj(dock_top, "Dock_Top", P['col_metal'], g_acpl)
dock_bot = ring(4.0, P['dock_bot_Do'], P['dock_bot_Di'], axis='Z', center=True)
dock_bot = T(dock_bot, (0,0,-P['bus_h']/2.0-6.0))
add_obj(dock_bot, "Dock_Bottom", P['col_metal'], g_acpl)

# ---------------------------
# 5) BLINDAJE WHIPPLE Y ESCUDO SOLAR
# ---------------------------
if P['enable_armor']:
    # Capas whipple alrededor del bus
    for i in range(P['shield_layers']):
        off = P['shield_gap']*(i+1)
        outer = centered_box(P['bus_w']+2*off, P['bus_d']+2*off, P['bus_h']+2*off)
        inner = centered_box(P['bus_w']+2*off-P['armor_thk'],
                             P['bus_d']+2*off-P['armor_thk'],
                             P['bus_h']+2*off-P['armor_thk'])
        shell = outer.cut(inner)
        add_obj(shell, f"Whipple_Layer_{i+1}", P['col_armor'], g_armor)

if P['enable_sunshield']:
    # Escudo solar frontal estilo frustum, mirando a +X (lado Sol)
    R1 = P['sunshield_d']/2.0
    R2 = R1 - P['sunshield_cone']
    shield = cone(R1, R2, P['sunshield_thk'], axis='X', center=False)
    shield = T(shield, (P['bus_w']/2.0 + P['sunshield_gap'], 0, 0))
    add_obj(shield, "SunShield_Front", (0.08,0.08,0.09), g_armor)

# ---------------------------
# 6) RADIADORES DE ALTO FLUJO (con aletas)
# ---------------------------
if P['enable_radiators']:
    def make_radiator(w, h, t, fin_step, fin_t):
        plate = centered_box(w, t, h)
        fins = []
        n = int(w/fin_step)
        for i in range(-n//2, n//2+1):
            fin = centered_box(fin_t, t+0.6, h-6.0)
            fin = T(fin, (i*fin_step, 0, 0))
            fins.append(fin)
        return Part.makeCompound([plate] + fins)
    radYp = make_radiator(P['radiator_w'], P['radiator_h'], P['radiator_t'], P['fin_step'], P['fin_t'])
    radYp = T(radYp, (0, P['bus_d']/2.0 + P['radiator_t']/2.0 + 1.0, 0))
    add_obj(radYp, "Radiator_Y+", P['col_radiator'], g_therm)
    radYn = T(radYp, (0, - (P['bus_d'] + P['radiator_t'] + 2.0), 0))
    add_obj(radYn, "Radiator_Y-", P['col_radiator'], g_therm)

# ---------------------------
# 7) MOTORES PRINCIPALES (nave)
# ---------------------------
if P['enable_engines']:
    for k in range(P['engine_count']):
        off = (k-(P['engine_count']-1)/2.0)* (P['engine_r']*2.6)
        nozzle = cone(P['engine_r']*1.15, P['engine_r']*0.65, P['engine_len']*0.35, axis='X', center=False)
        tube   = cyl(P['engine_len']*0.65, P['engine_r'], axis='X', center=False)
        eng = Part.Compound([T(nozzle,(0,0,0)), T(tube,(P['engine_len']*0.35,0,0))])
        eng = T(eng, (-P['bus_w']/2.0 - P['stern_len'] - 25.0, off, 0))
        add_obj(eng, f"MainEngine_{k+1}", P['col_metal'], g_ship)
        glow = cyl(P['engine_len']*0.25, P['engine_r']*0.7, axis='X', center=False)
        glow = T(glow, (-P['bus_w']/2.0 - P['stern_len'] - 25.0 + P['engine_len']*0.10, off, 0))
        add_obj(glow, f"EngineGlow_{k+1}", P['col_glow'], g_ship)

# ---------------------------
# 8) TORRETAS (look nave)
# ---------------------------
if P['enable_turrets']:
    def make_turret(name, base_r, h, cannon_len, cannon_r, pos):
        base = cyl(h, base_r, axis='Z', center=True)
        pod  = centered_box(base_r*1.2, base_r*0.8, h*0.6)
        pod  = T(pod, (base_r*0.6, 0, 0))
        gun1 = cyl(cannon_len, cannon_r, axis='X', center=False)
        gun1 = T(gun1, (base_r*0.6,  cannon_r*1.6, 0))
        gun2 = cyl(cannon_len, cannon_r, axis='X', center=False)
        gun2 = T(gun2, (base_r*0.6, -cannon_r*1.6, 0))
        return T(Part.Compound([base,pod,gun1,gun2]), pos)

    tur_top = make_turret("Turret_Top", P['turret_r'], P['turret_h'], P['cannon_len'], P['cannon_r'], (0,0,P['bus_h']/2.0 + 10.0))
    tur_bot = make_turret("Turret_Bot", P['turret_r'], P['turret_h'], P['cannon_len'], P['cannon_r'], (0,0,-P['bus_h']/2.0 - 10.0))
    add_obj(tur_top, "Turret_Top", P['col_metal'], g_weap)
    add_obj(tur_bot, "Turret_Bot", P['col_metal'], g_weap)

# ---------------------------
# 9) GREEBLES (detalle superficial)
# ---------------------------
if P['enable_greebles']:
    def add_greeble_area(area_w, area_d, count, origin, up=1):
        for _ in range(count):
            w = rand(2.0, area_w*0.18); d = rand(2.0, area_d*0.18); h = rand(1.0, 3.0)
            x = rand(-area_w/2.0, area_w/2.0 - w)
            y = rand(-area_d/2.0, area_d/2.0 - d)
            base = centered_box(w,d,h)
            if up>0:
                base = T(base, (x+w/2.0, y+d/2.0, h/2.0))
            else:
                base = T(base, (x+w/2.0, y+d/2.0, -h/2.0))
            base = T(base, origin)
            add_obj(base, f"G_{random.randint(0,99999)}", P['col_greeble'], g_gree)
    dens = P['greeble_density']
    add_greeble_area(P['bus_w'], P['bus_d'], int(24*dens), (0,0,P['bus_h']/2.0))
    add_greeble_area(P['bus_w'], P['bus_d'], int(18*dens), (0,0,-P['bus_h']/2.0), up=-1)

# ---------------------------
# FINAL
# ---------------------------
doc.recompute()
try: Gui.ActiveDocument.ActiveView.fitAll()
except: pass
print("StarSat_Fusion generado. Ajusta parámetros en P para afinar estética, protección y acoplamientos.")
