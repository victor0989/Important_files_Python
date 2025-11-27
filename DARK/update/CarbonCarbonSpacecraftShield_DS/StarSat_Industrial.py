import FreeCAD as App
import FreeCADGui as Gui
import Part, math, random

doc = App.newDocument("StarSat_Industrial")

P = dict(
    mode="hybrid",   # "hybrid", "sat", "ship"
    wall_thk=2.0,
    chamfer_val=0.8,

    # Bus base
    bus_w=60.0, bus_d=60.0, bus_h=80.0,

    # Casco
    prow_len=80.0, stern_len=60.0, deck_thk=3.0,
    hull_scale=1.15,

    # Alas
    fin_span=110.0, fin_t=3.0,

    # Motores
    engine_count=2, engine_len=80.0, engine_r=14.0,
    engine_ring_t=3.0,

    # Paneles solares
    panel_len=160.0, panel_w=50.0, panel_t=2.5, panel_segments=3,
    panel_deploy_deg=25.0,

    # HGA
    dish_diameter=55.0, dish_depth=10.0, dish_thickness=1.5, boom_len=40.0,

    # Colores
    col_hull=(0.75,0.76,0.78),
    col_panel=(0.06,0.08,0.20),
    col_metal=(0.70,0.70,0.72),
    col_glow=(0.15,0.4,1.0),
    col_detail=(0.5,0.5,0.5)
)

random.seed(42)

# --- HELPERS ---
def add_obj(shape, name, color=None, group=None):
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    if color:
        try: obj.ViewObject.ShapeColor = color
        except: pass
    if group: group.addObject(obj)
    return obj

def T(shape, v):
    m = App.Matrix(); m.move(App.Vector(*v)); return shape.transformGeometry(m)

def R(shape, axis, ang, center=(0,0,0)):
    return shape.rotate(App.Vector(*center), App.Vector(*axis), ang)

def centered_box(w,d,h):
    return T(Part.makeBox(w,d,h), (-w/2,-d/2,-h/2))

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
    inner = cyl(h+0.1, Di/2.0, axis=axis, center=center)
    return outer.cut(inner)

def chamfer(shape, val):
    try:
        edges = [e for e in shape.Edges]
        return shape.makeChamfer(val, edges)
    except:
        return shape

# --- GRUPOS ---
g_root  = doc.addObject("App::DocumentObjectGroup", "StarSat")
g_bus   = doc.addObject("App::DocumentObjectGroup", "Bus_and_Systems"); g_root.addObject(g_bus)
g_ship  = doc.addObject("App::DocumentObjectGroup", "ShipShell"); g_root.addObject(g_ship)
g_pan   = doc.addObject("App::DocumentObjectGroup", "SolarArrays"); g_root.addObject(g_pan)
g_acpl  = doc.addObject("App::DocumentObjectGroup", "Acoplamientos"); g_root.addObject(g_acpl)
g_weap  = doc.addObject("App::DocumentObjectGroup", "Details"); g_root.addObject(g_weap)

# --- MÓDULOS ---
def make_bus():
    outer = centered_box(P['bus_w'], P['bus_d'], P['bus_h'])
    inner = centered_box(P['bus_w']-2*P['wall_thk'], P['bus_d']-2*P['wall_thk'], P['bus_h']-2*P['wall_thk'])
    bus = chamfer(outer.cut(inner), P['chamfer_val'])
    return add_obj(bus, "Bus", P['col_hull'], g_bus)

def make_deck():
    hull_len = P['bus_w']*P['hull_scale'] + P['prow_len'] + P['stern_len']
    hull_w   = P['bus_d']*P['hull_scale']
    deck = centered_box(hull_len, hull_w, P['deck_thk'])
    return add_obj(chamfer(deck, P['chamfer_val']), "Deck", P['col_hull'], g_ship)

def make_proa():
    c = cone(P['bus_d']*P['hull_scale']/2.0, 4.0, P['prow_len'], axis='X', center=True)
    return add_obj(chamfer(T(c, (P['bus_w']/2.0 + P['prow_len']/2.0, 0, 0)), P['chamfer_val']), "Proa", P['col_hull'], g_ship)

def make_popa():
    c = cyl(P['stern_len'], P['bus_d']*P['hull_scale']/2.5, axis='X', center=True)
    return add_obj(chamfer(T(c, (-P['bus_w']/2.0 - P['stern_len']/2.0, 0, 0)), P['chamfer_val']), "Popa", P['col_hull'], g_ship)

def make_fins():
    fin = centered_box(P['fin_span'], P['fin_t']*2.0, P['fin_t'])
    finL = T(fin, (0, P['bus_d']/2.0 + P['fin_t'], 0))
    finR = T(fin, (0, -P['bus_d']/2.0 - P['fin_t'], 0))
    add_obj(finL, "Ala_Izq", P['col_hull'], g_ship)
    add_obj(finR, "Ala_Der", P['col_hull'], g_ship)

def make_motores():
    base_x = -P['bus_w']/2.0 - P['stern_len']
    for k in range(P['engine_count']):
        yoff = (k-(P['engine_count']-1)/2.0)* (P['engine_r']*3.0)
        cuerpo = cyl(P['engine_len'], P['engine_r'], axis='X', center=True)
        anillo = ring(P['engine_ring_t'], P['engine_r']*2.2, P['engine_r']*1.6, axis='X', center=True)
        motor = Part.makeCompound([cuerpo, anillo])
        motor = T(motor, (base_x - P['engine_len']/2.0, yoff, 0))
        add_obj(chamfer(motor, 0.5), f"Motor_{k+1}", P['col_metal'], g_ship)

def make_paneles():
    seg_len = P['panel_len'] / P['panel_segments']
    segmento = centered_box(seg_len, P['panel_w'], P['panel_t'])
    panel_comp = Part.makeCompound([
        T(segmento, (i * (seg_len + 1.5), 0, 0))
        for i in range(P['panel_segments'])
    ])
    hinge = cyl(5.0, 3.0, axis='X', center=True)
    panel_full = Part.makeCompound([panel_comp, hinge])

    # Puntos de pivote
    pivotL = (-P['bus_w'] / 2.0, 0, 0)
    pivotR = ( P['bus_w'] / 2.0, 0, 0)

    # Colocación de paneles a izquierda y derecha
    wingL = T(panel_full, (-P['bus_w']/2.0 - seg_len/2.0 - 2.0, 0, 0))
    wingR = T(panel_full, ( P['bus_w']/2.0 + seg_len/2.0 + 2.0, 0, 0))

    objL = add_obj(wingL, "Panel_Izq", P['col_panel'], g_pan)
    objR = add_obj(wingR, "Panel_Der", P['col_panel'], g_pan)

    # Rotación para desplegar
    objL.Placement = App.Placement(
        App.Vector(*pivotL),
        App.Rotation(App.Vector(0,1,0), P['panel_deploy_deg']),
        App.Vector(*pivotL)
    )
    objR.Placement = App.Placement(
        App.Vector(*pivotR),
        App.Rotation(App.Vector(0,1,0), -P['panel_deploy_deg']),
        App.Vector(*pivotR)
    )

def make_HGA():
    # Brazo
    boom = cyl(P['boom_len'], 2.0, axis='X', center=False)
    boom = T(boom, (P['bus_w']/2.0, 0, 0))
    add_obj(boom, "HGA_Brazo", P['col_metal'], g_bus)

    # Plato parabólico simplificado (metal-friendly)
    bowl_outer = Part.makeSphere(P['dish_diameter']/2.0)
    cut_plane = centered_box(P['dish_diameter'], P['dish_diameter'], P['dish_diameter']/2.0)
    bowl = bowl_outer.cut(T(cut_plane, (0,0,P['dish_diameter']/4.0)))
    bowl = T(bowl, (P['bus_w']/2.0 + P['boom_len'], 0, 0))
    add_obj(bowl, "HGA_Plato", P['col_metal'], g_bus)

def make_dock_port():
    port = ring(4.0, 80.0, 56.0, axis='Z', center=True)
    add_obj(T(port, (0, 0, P['bus_h']/2.0 + 4.0)), "Dock_Top", P['col_metal'], g_acpl)

# ---------------------------
# ENSAMBLADOR
# ---------------------------
def build_starsat(mode):
    make_bus()

    if mode in ("ship", "hybrid"):
        make_deck()
        make_proa()
        make_popa()
        make_fins()
        make_motores()

    if mode in ("sat", "hybrid"):
        make_paneles()
        make_HGA()
        make_dock_port()

# ---------------------------
# EJECUCIÓN
# ---------------------------
build_starsat(P['mode'])
doc.recompute()

try:
    Gui.ActiveDocument.ActiveView.viewIsometric()
    Gui.SendMsgToActiveView("ViewFit")
except:
    pass
