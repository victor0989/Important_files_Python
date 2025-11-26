import FreeCAD as App, FreeCADGui as Gui, Part, math, random
doc = App.newDocument("StarSat_CC_Advanced")

# ---------------------------
# PARÁMETROS (mantengo estructura similar al original)
# ---------------------------
P = dict(
    mode="hybrid",   # "hybrid","sat","ship"
    # Bus base (units arbitrary consistent with original StarSat values)
    bus_w=60.0, bus_d=60.0, bus_h=80.0,
    hull_scale=1.2, hull_facets=12,
    prow_len=90.0, stern_len=60.0, deck_thk=3.0,
    prow_round=0.45, stern_taper=0.15,
    fin_span=120.0, fin_t=3.0, fin_sweep=22.0, fin_dihedral=12.0,
    engine_count=2, engine_len=90.0, engine_r=14.0, engine_ring_t=3.0,
    hyper_ring_Do=140.0, hyper_ring_Di=100.0, hyper_ring_t=6.0,
    panel_len=180.0, panel_w=50.0, panel_t=2.0, panel_segments=3, panel_deploy_deg=35.0, panel_roll_deg=6.0,
    dish_diameter=60.0, dish_depth=12.0, dish_thickness=1.2, boom_len=45.0,
    thruster_h=12.0, thruster_r1=4.0, thruster_r2=1.6,
    turret_r=8.0, turret_h=10.0, cannon_len=24.0, cannon_r=2.2,
    turret_positions=[(10.0,18.0,"top"),(-10.0,-18.0,"top"),(-20.0,0.0,"bot")],
    greeble_density=0.45, greeble_h=(1.2,4.0), greeble_a=(1.2,6.0),
    # Carbon-Carbon / ablative specifics (informational)
    cc_density_g_cm3=1.87,  # g/cm3 -> 1870 kg/m3
    cc_Tmax=2500.0,         # °C
    ablative_density_g_cm3=0.32, # ~PICA like
    pe_shield_thk=0.20,     # polyethylene storm shelter thickness (m equivalent)
    col_hull=(0.75,0.76,0.78), col_panel=(0.06,0.08,0.20), col_metal=(0.70,0.70,0.72),
    col_greeble=(0.55,0.56,0.58), col_glow=(0.15,0.4,1.0)
)
random.seed(42)

# ---------------------------
# MATERIAL DB (informativo)
# densities in kg/m3, emissivity, k (W/mK)
# ---------------------------
MATS = {
    "C_C_3D_CVI": {"name":"C/C_3D_CVI","density":1870.0,"emissivity":0.65,"k":40.0,"Tmax":2500.0},
    "C_C_PITCH": {"name":"C/C_PITCH","density":1900.0,"emissivity":0.70,"k":45.0,"Tmax":2500.0},
    "ABLATOR_PICA": {"name":"PICA_like","density":320.0,"emissivity":0.88,"k":0.12,"Tmax":1800.0},
    "MLI": {"name":"MLI","density":1420.0,"emissivity":0.02,"k":0.02},
    "AL7075": {"name":"Al_7075","density":2700.0,"emissivity":0.09,"k":130.0},
    "POLY": {"name":"Polyethylene","density":950.0,"emissivity":0.9,"k":0.42}
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

def tag_material_props(o, matname, density=None, emissivity=None, k=None, Tmax=None):
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
    tag_material_props(hull_o, MATS["C_C_3D_CVI"]["name"], density=MATS["C_C_3D_CVI"]["density"], emissivity=MATS["C_C_3D_CVI"]["emissivity"], k=MATS["C_C_3D_CVI"]["k"], Tmax=MATS["C_C_3D_CVI"]["Tmax"])
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
    add_obj(dish, "HGA_Dish", (1,1,1), g_bus)

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
# ...existing code...
def build_shielding():
    # Outer continuous skin + fused nose -> único sólido para impresión
    W,D,H = P['bus_w'], P['bus_d'], P['bus_h']
    # piel exterior algo sobredimensionada para cubrir todo (sin cortes por paneles)
    outer_shell = centered_box(W + 4.0, D + 4.0, H + 4.0)
    # ablative nose (suavizado) en +X
    nose = cone(D/2.0 + 2.0, 2.0, P['prow_len']*0.25, axis='X', center=False)
    nose = T(nose, (P['bus_w']/2.0 + (P['prow_len']*0.12), 0, 0))
    # MLI y Graded-Z serán sólo propiedades informativas (no crean huecos en la malla final)
    # fusionar nose con piel exterior para obtener un único sólido
    try:
        skin_solid = outer_shell.fuse(nose)
    except Exception:
        # si falla la fusión por geometría, fallback: usar outer_shell para impresión
        skin_solid = outer_shell
    skin_o = add_obj(skin_solid, "CC_OuterSkin_Solid", (0.12,0.12,0.12), g_shld)
    tag_material_props(skin_o, MATS["C_C_PITCH"]["name"], density=MATS["C_C_PITCH"]["density"], emissivity=MATS["C_C_PITCH"]["emissivity"], k=MATS["C_C_PITCH"]["k"], Tmax=MATS["C_C_PITCH"]["Tmax"])
    # añadir MLI/GradedZ como marcas (propiedades) pero no cortan el sólido
    gz_plate = box(20.0, 10.0, 0.8, (P['bus_w']/2.0 + 5.0, -5.0, -4.0))
    gz_o = add_obj(gz_plate, "GradedZ_Patch_Marker", (0.45,0.45,0.48), g_shld)
    tag_material_props(gz_o, "GradedZ", density=18000.0, emissivity=0.18, k=40.0)
    # MLI como placa ligera informativa (no huecos)
    mli = box(P['bus_w']-4.0, P['bus_d']-4.0, 0.5, (- (P['bus_w']-4.0)/2.0, - (P['bus_d']-4.0)/2.0, P['bus_h']/2.0 - 0.25))
    mli_o = add_obj(mli, "MLI_Blanket_Marker", (1.0,1.0,0.92),  g_shld, alpha=0.8)
    tag_material_props(mli_o, MATS["MLI"]["name"], density=MATS["MLI"]["density"], emissivity=MATS["MLI"]["emissivity"], k=MATS["MLI"]["k"])
    return True
# ...existing code...
def build_starsat(mode):
    make_bus()
    if mode in ("ship","hybrid"):
        make_deck_and_hull()
        make_fins(); make_hyper_ring(); make_turrets(); make_engines(); make_greebles()
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

# simple assembly warnings (bounded)
def simple_warning_report():
    outer_min = App.Vector(-P['bus_w'], -P['bus_d'], -P['bus_h']); outer_max = App.Vector(P['bus_w'], P['bus_d'], P['bus_h'])
    for o in doc.Objects:
        try:
            bb = o.Shape.BoundBox
            if bb.XMin < outer_min.x or bb.XMax > outer_max.x or bb.YMin < outer_min.y or bb.YMax > outer_max.y or bb.ZMin < outer_min.z or bb.ZMax > outer_max.z:
                # permit intentional external items
                if any(pref in o.Name for pref in ("Engine","Radiator","Ablative","HyperRing","Solar","HGA")):
                    continue
                print("Assembly warning:", o.Name, "outside bounds")
        except Exception:
            pass

simple_warning_report()
try:
    Gui.activeView().viewAxonometric(); Gui.SendMsgToActiveView("ViewFit")
except Exception:
    pass

print("StarSat_CC_Advanced creado: multilayer C/C, ablativo, Graded‑Z, PE shelter, radiadores y heatpipes.")
# ...existing code...
