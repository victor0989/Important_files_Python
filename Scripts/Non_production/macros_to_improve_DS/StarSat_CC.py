# StarSat_CC_Advanced — Satélite / nave modular con capas Carbon‑Carbon, ablativos y protección radiológica con blindaje fuerte

import FreeCAD as App, FreeCADGui as Gui, Part, math, random
doc = App.newDocument("StarSat_CC_Advanced")

# ---------------------------
# PARÁMETROS (mantengo estructura similar al original)
# ---------------------------
P = dict(
    mode="hybrid",   # "hybrid","sat","ship"
    # Bus base (units arbitrary consistent with original StarSat values) - SCALED UP x1.5
    bus_w=90.0, bus_d=90.0, bus_h=120.0,
    hull_scale=1.2, hull_facets=12,
    prow_len=135.0, stern_len=90.0, deck_thk=4.5,
    prow_round=0.45, stern_taper=0.15,
    fin_span=180.0, fin_t=4.5, fin_sweep=22.0, fin_dihedral=12.0,
    engine_count=4, engine_len=135.0, engine_r=21.0, engine_ring_t=4.5,
    hyper_ring_Do=210.0, hyper_ring_Di=150.0, hyper_ring_t=9.0,
    panel_len=270.0, panel_w=75.0, panel_t=3.0, panel_segments=3, panel_deploy_deg=35.0, panel_roll_deg=6.0,
    dish_diameter=90.0, dish_depth=18.0, dish_thickness=1.8, boom_len=67.5,
    thruster_h=18.0, thruster_r1=6.0, thruster_r2=2.4,
    turret_r=12.0, turret_h=15.0, cannon_len=36.0, cannon_r=3.3,
    turret_positions=[(15.0,27.0,"top"),(-15.0,-27.0,"top"),(-30.0,0.0,"bot")],
    greeble_density=0.45, greeble_h=(1.8,6.0), greeble_a=(1.8,9.0),
    # Carbon-Carbon / ablative specifics (informational)
    cc_density_g_cm3=1.87,  # g/cm3 -> 1870 kg/m3
    cc_Tmax=2500.0,         # °C
    ablative_density_g_cm3=0.32, # ~PICA like
    pe_shield_thk=0.50,     # polyethylene storm shelter thickness (m equivalent) - increased for stronger radiation protection
    armor_thk=2.0,          # additional armor plating thickness
    whipple_gap=5.0,        # gap in Whipple shield
    col_hull=(0.0,0.0,0.0), col_panel=(0.0,0.0,0.0), col_metal=(0.0,0.0,0.0),
    col_greeble=(0.0,0.0,0.0), col_glow=(0.15,0.4,1.0)
)
random.seed(42)

# ---------------------------
# MATERIAL DB (informativo)
# densities in kg/m3, emissivity, k (W/mK), thermoelastic: E (GPa), nu, CTE (1/K)
# ---------------------------
MATS = {
    "C_C_3D_CVI": {"name":"C/C_3D_CVI","density":1870.0,"emissivity":0.65,"k":40.0,"Tmax":2500.0,"E":150.0,"nu":0.15,"CTE":1e-6},
    "C_C_PITCH": {"name":"C/C_PITCH","density":1900.0,"emissivity":0.70,"k":45.0,"Tmax":2500.0,"E":120.0,"nu":0.18,"CTE":2e-6},
    "ABLATOR_PICA": {"name":"PICA_like","density":320.0,"emissivity":0.88,"k":0.12,"Tmax":1800.0,"E":0.5,"nu":0.3,"CTE":1e-4},
    "MLI": {"name":"MLI","density":1420.0,"emissivity":0.02,"k":0.02,"E":0.1,"nu":0.35,"CTE":5e-5},
    "AL7075": {"name":"Al_7075","density":2700.0,"emissivity":0.09,"k":130.0,"E":71.0,"nu":0.33,"CTE":23e-6},
    "POLY": {"name":"Polyethylene","density":950.0,"emissivity":0.9,"k":0.42,"E":1.0,"nu":0.4,"CTE":200e-6},
    "TUNGSTEN": {"name":"Tungsten","density":19300.0,"emissivity":0.35,"k":173.0,"Tmax":3422.0,"E":411.0,"nu":0.28,"CTE":4.5e-6},
    "BORON_CARBIDE": {"name":"B4C","density":2520.0,"emissivity":0.85,"k":30.0,"Tmax":2450.0,"E":460.0,"nu":0.17,"CTE":4.5e-6},
    "NEXTEL": {"name":"Nextel_Af700","density":3200.0,"emissivity":0.85,"k":0.5,"Tmax":1200.0,"E":150.0,"nu":0.25,"CTE":3e-6}
}

# ---------------------------
# HELPERS GEOMÉTRICOS Y MATERIALES
# ---------------------------
def add_obj(shape, name, color=None, group=None, alpha=0.0):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    try:
        if color: o.ViewObject.ShapeColor = color
        o.ViewObject.Transparency = int(alpha*100)
    except Exception:
        pass
    if group:
        try: group.addObject(o)
        except Exception: pass
    return o

def tag_material_props(o, matname, density=None, emissivity=None, k=None, Tmax=None, E=None, nu=None, CTE=None):
    try:
        if not hasattr(o, "Material"): o.addProperty("App::PropertyString","Material","Meta","Material")
        o.Material = str(matname)
        if density is not None and not hasattr(o, "Density"):
            o.addProperty("App::PropertyFloat","Density","Meta","Density"); o.Density = float(density)
        if emissivity is not None and not hasattr(o, "Emissivity"):
            o.addProperty("App::PropertyFloat","Emissivity","Meta","Emissivity"); o.Emissivity = float(emissivity)
        if k is not None and not hasattr(o, "ThermalConductivity"):
            o.addProperty("App::PropertyFloat","ThermalConductivity","Meta","ThermalConductivity"); o.ThermalConductivity = float(k)
        if Tmax is not None and not hasattr(o, "Tmax"):
            o.addProperty("App::PropertyFloat","Tmax","Meta","Tmax"); o.Tmax = float(Tmax)
        if E is not None and not hasattr(o, "YoungsModulus"):
            o.addProperty("App::PropertyFloat","YoungsModulus","Meta","Young's Modulus (GPa)"); o.YoungsModulus = float(E)
        if nu is not None and not hasattr(o, "PoissonsRatio"):
            o.addProperty("App::PropertyFloat","PoissonsRatio","Meta","Poisson's Ratio"); o.PoissonsRatio = float(nu)
        if CTE is not None and not hasattr(o, "ThermalExpansionCoeff"):
            o.addProperty("App::PropertyFloat","ThermalExpansionCoeff","Meta","CTE (1/K)"); o.ThermalExpansionCoeff = float(CTE)
    except Exception:
        pass

def T(shape, v):
    m = App.Matrix(); m.move(App.Vector(*v)); return shape.transformGeometry(m)

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

def cone(r1,r2,h,axis='Z',center=False):
    c = Part.makeCone(r1,r2,h)
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

def poly_prism(points, h):
    wire = Part.makePolygon([App.Vector(x,y,0) for (x,y) in points] + [App.Vector(points[0][0],points[0][1],0)])
    face = Part.Face(wire); solid = face.extrude(App.Vector(0,0,h))
    return T(solid, (0,0,-h/2.0))

def parabola_dish(d, depth, t, steps=48):
    rmax = d/2.0; a = depth/(rmax*rmax)
    curve_in = [(r, a*r*r) for r in [rmax*i/steps for i in range(0, steps+1)]]
    curve_out = [(r, a*r*r + t) for r in [rmax*i/steps for i in range(steps, -1, -1)]]
    profile = [(0,0)] + curve_in + curve_out + [(0,t)]
    pts = [App.Vector(x,0,z) for (x,z) in profile]
    wire = Part.makePolygon(pts+[pts[0]]); face = Part.Face(wire)
    return face.revolve(App.Vector(0,0,0), App.Vector(0,0,1), 360)

def rect_face_yz(hy, hz):
    pts = [App.Vector(0,-hy,-hz), App.Vector(0,hy,-hz), App.Vector(0,hy,hz), App.Vector(0,-hy,hz), App.Vector(0,-hy,-hz)]
    return Part.Face(Part.makePolygon(pts))

# ---------------------------
# GRUPOS
# ---------------------------
g_root = doc.addObject("App::DocumentObjectGroup", "StarSat")
g_bus  = doc.addObject("App::DocumentObjectGroup", "Bus_and_Systems"); g_root.addObject(g_bus)
g_ship = doc.addObject("App::DocumentObjectGroup", "ShipShell"); g_root.addObject(g_ship)
g_pan  = doc.addObject("App::DocumentObjectGroup", "SolarArrays"); g_root.addObject(g_pan)
g_weap = doc.addObject("App::DocumentObjectGroup", "Turrets"); g_root.addObject(g_weap)
g_acpl = doc.addObject("App::DocumentObjectGroup", "Acoplamientos"); g_root.addObject(g_acpl)
g_gree = doc.addObject("App::DocumentObjectGroup", "Greebles"); g_root.addObject(g_gree)
g_shld = doc.addObject("App::DocumentObjectGroup", "Shielding"); g_root.addObject(g_shld)
g_therm= doc.addObject("App::DocumentObjectGroup", "Thermal"); g_root.addObject(g_therm)
g_int  = doc.addObject("App::DocumentObjectGroup", "Internal"); g_root.addObject(g_int)

# ---------------------------
# CONSTRUCTORES (manteniendo estructura del script original)
# ---------------------------
def make_bus():
    return add_obj(centered_box(P['bus_w'], P['bus_d'], P['bus_h']), "Bus", P['col_hull'], g_bus)

def make_deck_and_hull():
    half_w = P['bus_w']*P['hull_scale']/2.0
    half_d = P['bus_d']*P['hull_scale']/2.0
    hull_h = P['bus_h']*P['hull_scale']
    deck_len = P['bus_w']*P['hull_scale'] + P['prow_len'] + P['stern_len']
    deck_w   = P['bus_d']*P['hull_scale']*0.9
    deck = centered_box(deck_len, deck_w, P['deck_thk'])
    x_bus_front = P['bus_w']/2.0
    f0 = rect_face_yz(hy=half_d*0.50, hz=hull_h*0.48); f1 = rect_face_yz(hy=half_d*P['prow_round']*0.40, hz=hull_h*P['prow_round']*0.35)
    f0 = T(f0, (x_bus_front + 8.0, 0, 0)); f1 = T(f1, (x_bus_front + P['prow_len'] + 15.0, 0, 0))
    prow = Part.makeLoft([f0, f1], True, False)
    x_bus_back = -P['bus_w']/2.0
    b0 = rect_face_yz(hy=half_d*0.48, hz=hull_h*0.46); b1 = rect_face_yz(hy=half_d*(1.0 - P['stern_taper']), hz=hull_h*(0.65 - P['stern_taper']*0.5))
    b0 = T(b0, (x_bus_back - 8.0,0,0)); b1 = T(b1, (x_bus_back - P['stern_len'] - 15.0,0,0))
    stern = Part.makeLoft([b0,b1], True, False)
    hull = Part.makeCompound([prow, stern, deck])
    hull_o = add_obj(hull, "Ship_Hull", P['col_hull'], g_ship)
    # tag hull layers: outer C/C skin (informative property)
    tag_material_props(hull_o, MATS["C_C_3D_CVI"]["name"], density=MATS["C_C_3D_CVI"]["density"], emissivity=MATS["C_C_3D_CVI"]["emissivity"], k=MATS["C_C_3D_CVI"]["k"], Tmax=MATS["C_C_3D_CVI"]["Tmax"], E=MATS["C_C_3D_CVI"]["E"], nu=MATS["C_C_3D_CVI"]["nu"], CTE=MATS["C_C_3D_CVI"]["CTE"])
    return hull_o

def make_fins():
    fin_pts = [(0,-P['fin_span']/2.0),(P['fin_span']*0.45,-P['fin_span']*0.12),(P['fin_span']*0.55,P['fin_span']*0.12),(0,P['fin_span']/2.0)]
    fin = poly_prism(fin_pts, P['fin_t']); fin = R(fin,(0,1,0),P['fin_sweep']); fin = R(fin,(1,0,0),P['fin_dihedral'])
    finL = T(fin, (P['bus_w']/2.0, 0, 0)); finR = T(R(fin,(0,0,1),180), (-P['bus_w']/2.0,0,0))
    add_obj(finL, "Fin_Left", P['col_hull'], g_ship); add_obj(finR, "Fin_Right", P['col_hull'], g_ship)

def make_hyper_ring():
    hyper = ring(P['hyper_ring_t'], P['hyper_ring_Do'], P['hyper_ring_Di'], axis='Y', center=True)
    hyper = T(hyper, (P['bus_w']/2.0 + P['prow_len'] + 15.0, 0, 0)); add_obj(hyper, "HyperRing", P['col_metal'], g_acpl)

def make_dock_port():
    port = ring(4.0, 80.0, 56.0, axis='Z', center=True); add_obj(T(port, (0,0,P['bus_h']/2.0+4.0)), "Dock_Top", P['col_metal'], g_acpl)

def make_solar_arrays():
    seg_len = P['panel_len']/float(P['panel_segments'])
    segment = centered_box(seg_len, P['panel_w'], P['panel_t'])
    skin = centered_box(seg_len-3, P['panel_w']-3, P['panel_t']/2.0); skin = T(skin,(0,0,-P['panel_t']/2.0+P['panel_t']/8.0))
    segment = Part.Compound([segment, skin])
    wing = Part.Compound([T(segment,(i*(seg_len+1.5)+seg_len/2.0,0,0)) for i in range(P['panel_segments'])])
    hinge = cyl(5.0, 2.8, axis='X', center=True); wing = Part.Compound([wing, T(hinge,(-2.0,0,0))])
    pivotL = (-P['bus_w']/2.0,0,0); pivotR = (P['bus_w']/2.0,0,0)
    wingL = T(wing, (-1.0-P['bus_w']/2.0,0,0)); wingR = T(wing, (1.0+P['bus_w']/2.0,0,0))
    objL = add_obj(wingL, "Solar_Left", P['col_panel'], g_pan); objR = add_obj(wingR, "Solar_Right", P['col_panel'], g_pan)
    rotL = App.Rotation(App.Vector(0,1,0), P['panel_deploy_deg']).multiply(App.Rotation(App.Vector(0,0,1), P['panel_roll_deg']))
    rotR = App.Rotation(App.Vector(0,1,0), -P['panel_deploy_deg']).multiply(App.Rotation(App.Vector(0,0,1), -P['panel_roll_deg']))
    objL.Placement = App.Placement(App.Vector(*pivotL), rotL, App.Vector(*pivotL)); objR.Placement = App.Placement(App.Vector(*pivotR), rotR, App.Vector(*pivotR))

def make_HGA():
    boom = cyl(P['boom_len'], 1.8, axis='X', center=False); boom = T(boom, (P['bus_w']/2.0, 0, 0)); add_obj(boom, "HGA_Boom", P['col_metal'], g_bus)
    g1 = ring(3.0, 34.0, 29.0, axis='Z', center=True); g2 = ring(3.0, 28.0, 23.0, axis='X', center=True); gimbal = Part.Compound([g1,g2])
    gimbal = T(gimbal, (P['bus_w']/2.0 + P['boom_len'], 0, 0)); add_obj(gimbal, "HGA_Gimbal", P['col_metal'], g_bus)
    dish = parabola_dish(P['dish_diameter'], P['dish_depth'], P['dish_thickness']); dish = R(dish, (0,1,0), -18); dish = T(dish, (P['bus_w']/2.0 + P['boom_len'], 0, 0))
    add_obj(dish, "HGA_Dish", (0.0,0.0,0.0), g_bus)

def make_RCS():
    corners = [(1,1),(1,-1),(-1,1),(-1,-1)]
    for i,(sx,sy) in enumerate(corners):
        thr_top = cone(P['thruster_r1'], P['thruster_r2'], P['thruster_h'], axis='X', center=False)
        thr_top = T(thr_top, (sx*P['bus_w']/2.0, sy*P['bus_d']/2.0, P['bus_h']/2.0)); add_obj(thr_top, f"RCS_Top_{i+1}", P['col_metal'], g_bus)
        thr_bot = cone(P['thruster_r1'], P['thruster_r2'], P['thruster_h'], axis='X', center=False)
        thr_bot = T(thr_bot, (sx*P['bus_w']/2.0, sy*P['bus_d']/2.0, -P['bus_h']/2.0)); add_obj(thr_bot, f"RCS_Bot_{i+1}", P['col_metal'], g_bus)

def make_engine_unit(k, x0, y0):
    nozzle = cone(P['engine_r']*1.15, P['engine_r']*0.65, P['engine_len']*0.35, axis='X', center=False)
    tube = cyl(P['engine_len']*0.60, P['engine_r'], axis='X', center=False)
    ring1 = ring(P['engine_ring_t'], P['engine_r']*2.25, P['engine_r']*1.8, axis='X', center=True)
    eng = Part.Compound([T(nozzle,(0,0,0)), T(tube,(P['engine_len']*0.35,0,0)), T(ring1,(P['engine_len']*0.25,0,0))])
    eng = T(eng, (x0, y0, 0)); add_obj(eng, f"MainEngine_{k+1}", P['col_metal'], g_ship)
    glow = cyl(P['engine_len']*0.22, P['engine_r']*0.7, axis='X', center=False); glow = T(glow, (x0 + P['engine_len']*0.10, y0, 0)); add_obj(glow, f"EngineGlow_{k+1}", P['col_glow'], g_ship)

def make_engines():
    base_x = -P['bus_w']/2.0 - P['stern_len'] - 25.0
    for k in range(P['engine_count']):
        off = (k-(P['engine_count']-1)/2.0) * (P['engine_r']*2.6)
        make_engine_unit(k, base_x, off)

def make_turrets():
    z_top = P['bus_h']/2.0 + P['deck_thk']/2.0; z_bot = -P['bus_h']/2.0 - P['deck_thk']/2.0
    for i,(x_off,y_off,side) in enumerate(P['turret_positions']):
        z = z_top if side=="top" else z_bot
        base = cyl(P['turret_h'], P['turret_r'], axis='Z', center=True); base = T(base, (x_off,y_off,z + (P['turret_h']/2.0 if side=="top" else -P['turret_h']/2.0)))
        add_obj(base, f"TurretBase_{i+1}", P['col_metal'], g_weap)
        mount = cyl(4.0, P['turret_r']*0.75, axis='Z', center=True); mount = T(mount, (x_off,y_off,z + (6.0 if side=="top" else -6.0))); add_obj(mount, f"TurretMount_{i+1}", P['col_metal'], g_weap)
        sep = P['turret_r']*0.6
        for j,dy in enumerate([-sep/2.0, sep/2.0]):
            barrel = cyl(P['cannon_len'], P['cannon_r'], axis='X', center=False); barrel = T(barrel, (x_off + P['turret_r']*0.8, y_off + dy, z + (2.0 if side=="top" else -2.0)))
            tip = cone(P['cannon_r']*1.2, P['cannon_r']*0.7, 4.0, axis='X', center=False); tip = T(tip, (x_off + P['turret_r']*0.8 + P['cannon_len'], y_off + dy, z + (2.0 if side=="top" else -2.0)))
            add_obj(Part.Compound([barrel, tip]), f"Cannon_{i+1}_{j+1}", P['col_metal'], g_weap)

def make_cc_reinforcements():
    # Internal C/C reinforcements for thermoelastic strength
    rib_w = P['bus_w'] * 0.8; rib_d = 5.0; rib_h = P['bus_h'] * 0.9
    rib = centered_box(rib_w, rib_d, rib_h)
    rib = T(rib, (0, 0, 0))
    rib_o = add_obj(rib, "CC_Internal_Rib", P['col_hull'], g_int)
    tag_material_props(rib_o, MATS["C_C_PITCH"]["name"], density=MATS["C_C_PITCH"]["density"], emissivity=MATS["C_C_PITCH"]["emissivity"], k=MATS["C_C_PITCH"]["k"], Tmax=MATS["C_C_PITCH"]["Tmax"], E=MATS["C_C_PITCH"]["E"], nu=MATS["C_C_PITCH"]["nu"], CTE=MATS["C_C_PITCH"]["CTE"])
    # Add cross ribs
    cross_rib = centered_box(rib_d, rib_w, rib_h)
    cross_rib = T(cross_rib, (0, 0, 0))
    cross_o = add_obj(cross_rib, "CC_Cross_Rib", P['col_hull'], g_int)
    tag_material_props(cross_o, MATS["C_C_PITCH"]["name"], density=MATS["C_C_PITCH"]["density"], emissivity=MATS["C_C_PITCH"]["emissivity"], k=MATS["C_C_PITCH"]["k"], Tmax=MATS["C_C_PITCH"]["Tmax"], E=MATS["C_C_PITCH"]["E"], nu=MATS["C_C_PITCH"]["nu"], CTE=MATS["C_C_PITCH"]["CTE"])

def make_honeycomb_shield():
    # Impact-resistant honeycomb panel
    hc_w = P['bus_w'] - 20.0; hc_d = 10.0; hc_h = P['bus_h'] - 20.0
    # Simplified honeycomb as a solid with pattern (for CAD, use solid)
    honeycomb = centered_box(hc_w, hc_d, hc_h)
    honeycomb = T(honeycomb, (0, P['bus_d']/2.0 + hc_d/2.0, 0))
    hc_o = add_obj(honeycomb, "Honeycomb_Shield", (0.0, 0.0, 0.0), g_shld)
    tag_material_props(hc_o, MATS["C_C_3D_CVI"]["name"], density=MATS["C_C_3D_CVI"]["density"], emissivity=MATS["C_C_3D_CVI"]["emissivity"], k=MATS["C_C_3D_CVI"]["k"], Tmax=MATS["C_C_3D_CVI"]["Tmax"], E=MATS["C_C_3D_CVI"]["E"], nu=MATS["C_C_3D_CVI"]["nu"], CTE=MATS["C_C_3D_CVI"]["CTE"])

def make_whipple_shield():
    # Whipple shield for micrometeorite protection
    bumper_thk = 0.5  # thin outer bumper
    bumper = centered_box(P['bus_w'] + 10.0, P['bus_d'] + 10.0, bumper_thk)
    bumper = T(bumper, (0, 0, P['bus_h']/2.0 + bumper_thk/2.0 + P['whipple_gap']))
    bumper_o = add_obj(bumper, "Whipple_Bumper", (0.0, 0.0, 0.0), g_shld)
    tag_material_props(bumper_o, MATS["AL7075"]["name"], density=MATS["AL7075"]["density"], emissivity=MATS["AL7075"]["emissivity"], k=MATS["AL7075"]["k"])
    # Rear wall
    rear_thk = 2.0
    rear_wall = centered_box(P['bus_w'] + 5.0, P['bus_d'] + 5.0, rear_thk)
    rear_wall = T(rear_wall, (0, 0, P['bus_h']/2.0 + rear_thk/2.0))
    rear_o = add_obj(rear_wall, "Whipple_Rear_Wall", (0.0, 0.0, 0.0), g_shld)
    tag_material_props(rear_o, MATS["AL7075"]["name"], density=MATS["AL7075"]["density"], emissivity=MATS["AL7075"]["emissivity"], k=MATS["AL7075"]["k"])

def make_armor_plating():
    # Heavy armor plating on sides
    armor_w = P['bus_w'] + 20.0; armor_h = P['bus_h'] + 20.0; armor_d = P['armor_thk']
    # Front armor
    front_armor = centered_box(armor_w, armor_d, armor_h)
    front_armor = T(front_armor, (P['bus_w']/2.0 + armor_d/2.0 + 10.0, 0, 0))
    front_o = add_obj(front_armor, "Front_Armor", (0.0, 0.0, 0.0), g_shld)
    tag_material_props(front_o, MATS["TUNGSTEN"]["name"], density=MATS["TUNGSTEN"]["density"], emissivity=MATS["TUNGSTEN"]["emissivity"], k=MATS["TUNGSTEN"]["k"], Tmax=MATS["TUNGSTEN"]["Tmax"], E=MATS["TUNGSTEN"]["E"], nu=MATS["TUNGSTEN"]["nu"], CTE=MATS["TUNGSTEN"]["CTE"])
    # Side armors
    side_armor = centered_box(armor_d, P['bus_d'] + 20.0, armor_h)
    left_armor = T(side_armor, (-P['bus_w']/2.0 - armor_d/2.0 - 10.0, 0, 0))
    left_o = add_obj(left_armor, "Left_Armor", (0.0, 0.0, 0.0), g_shld)
    tag_material_props(left_o, MATS["BORON_CARBIDE"]["name"], density=MATS["BORON_CARBIDE"]["density"], emissivity=MATS["BORON_CARBIDE"]["emissivity"], k=MATS["BORON_CARBIDE"]["k"], Tmax=MATS["BORON_CARBIDE"]["Tmax"], E=MATS["BORON_CARBIDE"]["E"], nu=MATS["BORON_CARBIDE"]["nu"], CTE=MATS["BORON_CARBIDE"]["CTE"])
    right_armor = T(side_armor, (P['bus_w']/2.0 + armor_d/2.0 + 10.0, 0, 0))
    right_o = add_obj(right_armor, "Right_Armor", (0.0, 0.0, 0.0), g_shld)
    tag_material_props(right_o, MATS["BORON_CARBIDE"]["name"], density=MATS["BORON_CARBIDE"]["density"], emissivity=MATS["BORON_CARBIDE"]["emissivity"], k=MATS["BORON_CARBIDE"]["k"], Tmax=MATS["BORON_CARBIDE"]["Tmax"], E=MATS["BORON_CARBIDE"]["E"], nu=MATS["BORON_CARBIDE"]["nu"], CTE=MATS["BORON_CARBIDE"]["CTE"])

def make_radiation_layers():
    # Additional polyethylene layers for radiation protection
    layer1 = centered_box(P['bus_w'] - 5.0, P['bus_d'] - 5.0, 0.2)
    layer1 = T(layer1, (0, 0, P['bus_h']/2.0 + 0.1))
    l1_o = add_obj(layer1, "PE_Layer1", (0.0, 0.0, 0.0), g_shld, alpha=0.6)
    tag_material_props(l1_o, MATS["POLY"]["name"], density=MATS["POLY"]["density"], emissivity=MATS["POLY"]["emissivity"], k=MATS["POLY"]["k"])
    layer2 = centered_box(P['bus_w'] - 10.0, P['bus_d'] - 10.0, 0.2)
    layer2 = T(layer2, (0, 0, -P['bus_h']/2.0 - 0.1))
    l2_o = add_obj(layer2, "PE_Layer2", (0.0, 0.0, 0.0), g_shld, alpha=0.6)
    tag_material_props(l2_o, MATS["POLY"]["name"], density=MATS["POLY"]["density"], emissivity=MATS["POLY"]["emissivity"], k=MATS["POLY"]["k"])

def make_greebles():
    density = P['greeble_density']; 
    if density <= 0: return
    deck_len = P['bus_w']*P['hull_scale'] + P['prow_len'] + P['stern_len']; x_min = -deck_len/2.0 + 8.0; x_max = deck_len/2.0 - 8.0
    y_min = -P['bus_d']*0.35; y_max = P['bus_d']*0.35; z = P['bus_h']/2.0 + P['deck_thk']/2.0 + 0.6
    area = (x_max-x_min)*(y_max-y_min); n = int(area * 0.0025 * density)
    for i in range(n):
        w = random.uniform(*P['greeble_a']); d = random.uniform(*P['greeble_a'])*0.6; h = random.uniform(*P['greeble_h'])
        x = random.uniform(x_min,x_max); y = random.uniform(y_min,y_max)
        if abs(y) < 6.0 and abs(x) < 10.0: continue
        g = centered_box(w,d,h); g = T(g,(x,y,z + h/2.0))
        if random.random() < 0.25:
            c = cyl(h*0.9, min(w,d)*0.35, axis='Z', center=True); c = T(c,(x + (w*0.15*(1 if random.random()<0.5 else -1)), y, z + h + h*0.45))
            add_obj(Part.Compound([g,c]), f"GreebleCyl_{i}", P['col_greeble'], g_gree)
        else:
            add_obj(g, f"Greeble_{i}", P['col_greeble'], g_gree)

# ...existing code...
def box(w,d,h, p=(0,0,0)): 
    # helper faltante: caja posicionada en p
    return Part.makeBox(w, d, h, App.Vector(*p))
def build_radiators_and_heatpipes():
    # Advanced thermal management: radiators and heatpipes
    rad_len = P['bus_w'] * 1.5; rad_w = P['bus_d'] * 0.8; rad_t = 2.0
    radiator = centered_box(rad_len, rad_w, rad_t)
    radiator = T(radiator, (0, 0, -P['bus_h']/2.0 - rad_t/2.0 - 5.0))
    rad_o = add_obj(radiator, "Radiator_Panel", (0.0, 0.0, 0.0), g_therm)
    tag_material_props(rad_o, MATS["AL7075"]["name"], density=MATS["AL7075"]["density"], emissivity=MATS["AL7075"]["emissivity"], k=MATS["AL7075"]["k"])
    # Heatpipes: cylindrical tubes
    hp_len = P['bus_w'] * 0.8; hp_r = 1.5
    heatpipe = cyl(hp_len, hp_r, axis='X', center=True)
    heatpipe = T(heatpipe, (0, P['bus_d']/2.0 + hp_r + 2.0, 0))
    hp_o = add_obj(heatpipe, "Heatpipe", (0.0, 0.0, 0.0), g_therm)
    tag_material_props(hp_o, MATS["AL7075"]["name"], density=MATS["AL7075"]["density"], emissivity=MATS["AL7075"]["emissivity"], k=MATS["AL7075"]["k"])
    return True

def build_storm_shelter():
    # Polyethylene storm shelter for radiation protection
    shelter = centered_box(P['bus_w'] - 10.0, P['bus_d'] - 10.0, P['pe_shield_thk'])
    shelter = T(shelter, (0, 0, P['bus_h']/2.0 + P['pe_shield_thk']/2.0 + 2.0))
    shelter_o = add_obj(shelter, "PE_Storm_Shelter", (0.0, 0.0, 0.0), g_shld, alpha=0.5)
    tag_material_props(shelter_o, MATS["POLY"]["name"], density=MATS["POLY"]["density"], emissivity=MATS["POLY"]["emissivity"], k=MATS["POLY"]["k"])
    return True

# ...existing code...
def build_shielding():
    # Outer continuous skin + fused nose -> único sólido para impresión
    W,D,H = P['bus_w'], P['bus_d'], P['bus_h']
    # piel exterior algo sobredimensionada para cubrir todo (sin cortes por paneles)
    outer_shell = centered_box(W + 4.0, D + 4.0, H + 4.0)
    # ablative nose (thicker for impact resistance) en +X
    nose = cone(D/2.0 + 5.0, 3.0, P['prow_len']*0.5, axis='X', center=False)  # thicker nose
    nose = T(nose, (P['bus_w']/2.0 + (P['prow_len']*0.15), 0, 0))
    # MLI y Graded-Z serán sólo propiedades informativas (no crean huecos en la malla final)
    # fusionar nose con piel exterior para obtener un único sólido
    try:
        skin_solid = outer_shell.fuse(nose)
    except Exception:
        # si falla la fusión por geometría, fallback: usar outer_shell para impresión
        skin_solid = outer_shell
    skin_o = add_obj(skin_solid, "CC_OuterSkin_Solid", (0.0,0.0,0.0), g_shld)
    tag_material_props(skin_o, MATS["C_C_PITCH"]["name"], density=MATS["C_C_PITCH"]["density"], emissivity=MATS["C_C_PITCH"]["emissivity"], k=MATS["C_C_PITCH"]["k"], Tmax=MATS["C_C_PITCH"]["Tmax"])
    # añadir MLI/GradedZ como marcas (propiedades) pero no cortan el sólido
    gz_plate = box(20.0, 10.0, 0.8, (P['bus_w']/2.0 + 5.0, -5.0, -4.0))
    gz_o = add_obj(gz_plate, "GradedZ_Patch_Marker", (0.0,0.0,0.0), g_shld)
    tag_material_props(gz_o, "GradedZ", density=18000.0, emissivity=0.18, k=40.0)
    # MLI como placa ligera informativa (no huecos)
    mli = box(P['bus_w']-4.0, P['bus_d']-4.0, 0.5, (- (P['bus_w']-4.0)/2.0, - (P['bus_d']-4.0)/2.0, P['bus_h']/2.0 - 0.25))
    mli_o = add_obj(mli, "MLI_Blanket_Marker", (0.0,0.0,0.0),  g_shld, alpha=0.8)
    tag_material_props(mli_o, MATS["MLI"]["name"], density=MATS["MLI"]["density"], emissivity=MATS["MLI"]["emissivity"], k=MATS["MLI"]["k"])
    # Add strong armor components
    make_whipple_shield()
    make_armor_plating()
    make_radiation_layers()
    return True
# ...existing code...
def build_starsat(mode):
    make_bus()
    if mode in ("ship","hybrid"):
        make_deck_and_hull()
        make_fins(); make_hyper_ring(); make_turrets(); make_engines(); make_greebles()
        make_cc_reinforcements(); make_honeycomb_shield()  # Added for more C/C and impact resistance
    # no crear paneles solares -> evito huecos en la piel exterior
    if mode in ("sat",):
        # opcional: mantener HGA/RCS/dock sin perforar la piel
        make_HGA(); make_RCS(); make_dock_port()
    # shielding y thermal: la piel exterior será un sólido sin cortes
    build_shielding(); build_radiators_and_heatpipes(); build_storm_shelter()
# ...existing code...
# ---------------------------
# EXECUTE
# ---------------------------
build_starsat(P['mode'])
doc.recompute()

# simple assembly warnings (bounded) - updated for larger size
def simple_warning_report():
    outer_min = App.Vector(-P['bus_w']*1.2, -P['bus_d']*1.2, -P['bus_h']*1.2); outer_max = App.Vector(P['bus_w']*1.2, P['bus_d']*1.2, P['bus_h']*1.2)
    for o in doc.Objects:
        try:
            bb = o.Shape.BoundBox
            if bb.XMin < outer_min.x or bb.XMax > outer_max.x or bb.YMin < outer_min.y or bb.YMax > outer_max.y or bb.ZMin < outer_min.z or bb.ZMax > outer_max.z:
                # permit intentional external items
                if any(pref in o.Name for pref in ("Engine","Radiator","Ablative","HyperRing","Solar","HGA","CC_Internal","Honeycomb")):
                    continue
                print("Assembly warning:", o.Name, "outside bounds")
        except Exception:
            pass

simple_warning_report()
try:
    Gui.activeView().viewAxonometric(); Gui.SendMsgToActiveView("ViewFit")
except Exception:
    pass

print("StarSat_CC_Advanced_Enhanced creado: larger x1.5, multilayer C/C with thermoelastic props, thicker ablative nose, impact-resistant honeycomb, internal CC reinforcements, powerful 4 engines, advanced thermal management, strong armor with Whipple shield, tungsten/boron carbide plating, and enhanced radiation protection.")
# ...existing code...