# -*- coding: utf-8 -*-
# Macro: HybridPlasmaPropulsion_v2_2
# FreeCAD 0.19–0.21 compatible. Unidades: mm (densidades en kg/m^3).
import FreeCAD as App
import FreeCADGui as Gui
import Part, math

DOC_NAME = "HybridPlasmaPropulsion_v22"

# -----------------------------
# PARÁMETROS
# -----------------------------
P = {
    # Cuerpo escalonado [(longitud, diámetro)]
    "body_sections": [
        (520.0, 1200.0),
        (480.0, 1120.0),
        (420.0, 980.0),
        (500.0, 1040.0),
        (600.0, 1150.0),
        (400.0, 1000.0),
    ],
    "body_edge_fillet": 3.0,

    # Chaqueta y canal helicoidal
    "jacket_z0_offset": 260.0,
    "jacket_length": 1600.0,
    "jacket_inner_diam": 1000.0,
    "jacket_outer_diam": 1150.0,
    "helix_pitch": 240.0,
    "helix_turns": 6,
    "helix_channel_radius": 12.0,
    "helix_margin_wall": 3.0,
    "jacket_edge_fillet": 2.0,

    # Boquilla (ion thruster)
    "nozzle_length": 800.0,
    "nozzle_precone_ratio": 0.25,
    "nozzle_main_ratio": 0.55,
    "nozzle_exit_ratio": 0.20,
    "nozzle_throat_diam": 360.0,
    "nozzle_exit_diam": 600.0,
    "nozzle_edge_fillet": 2.0,

    # Brida y tornillería
    "flange_thickness": 25.0,
    "flange_width": 80.0,
    "flange_pcd": 1050.0,
    "bolt_count": 12,
    "bolt_shaft_d": 14.0,
    "bolt_head_d": 24.0,
    "bolt_head_h": 8.0,
    "bolt_len": 45.0,
    "flange_edge_chamfer": 1.2,

    # Anillos radiativos
    "rad_ring_count": 4,
    "rad_ring_outer_diam": 1400.0,
    "rad_ring_width": 80.0,
    "rad_ring_thickness": 5.0,
    "rad_first_offset": 280.0,
    "rad_spacing": 220.0,
    "rad_edge_fillet": 1.0,

    # Tanques laterales
    "tank_diam": 450.0,
    "tank_height": 1200.0,
    "tank_clearance": 60.0,
    "tank_angles_deg": [90.0, 270.0],
    "tank_z_center_offset": 0.0,
    "tank_edge_fillet": 2.0,

    # Módulos “cuánticos”
    "quant_module_diam": 120.0,
    "quant_module_height": 350.0,
    "quant_module_count": 6,
    "quant_radius_offset": 220.0,

    # Conductos térmicos
    "duct_width": 200.0,
    "duct_height": 60.0,
    "duct_length": 900.0,
    "duct_pairs": 4,

    # Materiales y colores
    "mat_body":   {"name": "Al6061-T6",     "density": 2700.0,  "color": (0.70, 0.75, 0.80)},
    "mat_jacket": {"name": "GrapheneComp",  "density": 1600.0,  "color": (0.10, 0.10, 0.10)},
    "mat_nozzle": {"name": "Ti6Al4V",       "density": 4420.0,  "color": (0.55, 0.55, 0.65)},
    "mat_rings":  {"name": "CFRP_Rad",      "density": 1650.0,  "color": (0.20, 0.20, 0.25)},
    "mat_tank":   {"name": "Inconel625",    "density": 8440.0,  "color": (0.45, 0.50, 0.55)},
    "mat_quant":  {"name": "CuW70",         "density": 17250.0, "color": (0.60, 0.40, 0.20)},
    "mat_duct":   {"name": "PyroGraphite",  "density": 2200.0,  "color": (0.15, 0.15, 0.15)},
    "mat_brkt":   {"name": "Ti_Grade5",     "density": 4430.0,  "color": (0.55, 0.55, 0.60)},
    "mat_bolt":   {"name": "A286",          "density": 7900.0,  "color": (0.35, 0.35, 0.35)},

    # Salidas
    "make_techdraw": True,
    "make_step_export": False,
    "step_path": App.getUserAppDataDir() + "HybridPlasmaPropulsion_v22.step",
}

# -----------------------------
# UTILIDADES BASE
# -----------------------------
def get_doc():
    d = App.ActiveDocument
    if d is None or d.Name != DOC_NAME:
        d = App.newDocument(DOC_NAME)
    return d

doc = get_doc()

def set_material(obj, mat):
    if "Density" not in obj.PropertiesList:
        obj.addProperty("App::PropertyFloat", "Density", "Material", "kg/m^3")
    if "MaterialName" not in obj.PropertiesList:
        obj.addProperty("App::PropertyString", "MaterialName", "Material", "Nombre de material")
    obj.Density = float(mat["density"])
    obj.MaterialName = mat["name"]
    obj.ViewObject.ShapeColor = mat["color"]

def mass_kg(obj):
    vol_m3 = obj.Shape.Volume * 1e-9
    dens = obj.Density if "Density" in obj.PropertiesList else 0.0
    return dens * vol_m3

def refine_shape(shape):
    try:
        return shape.removeSplitter()
    except Exception:
        return shape

def fuse_objs(objs, name, mat=None, color=None, parent=None):
    if not objs: return None
    base = objs[0].Shape
    for o in objs[1:]:
        base = base.fuse(o.Shape)
    base = refine_shape(base)
    out = doc.addObject("Part::Feature", name)
    out.Shape = base
    if mat: set_material(out, mat)
    if color: out.ViewObject.ShapeColor = color
    if parent: parent.addObject(out)
    return out

def add_cyl(name, r, h, z0, mat, parent=None):
    s = Part.makeCylinder(r, h, App.Vector(0,0,z0))
    o = doc.addObject("Part::Feature", name)
    o.Shape = s
    set_material(o, mat)
    if parent: parent.addObject(o)
    return o

def add_cone(name, r1, r2, h, z0, mat, parent=None):
    s = Part.makeCone(r1, r2, h, App.Vector(0,0,z0))
    o = doc.addObject("Part::Feature", name)
    o.Shape = s
    set_material(o, mat)
    if parent: parent.addObject(o)
    return o

def add_ring_solid(name, r_out, r_in, t, z0, mat, parent=None):
    outer = Part.makeCylinder(r_out, t, App.Vector(0,0,z0))
    inner = Part.makeCylinder(r_in, t, App.Vector(0,0,z0))
    s = refine_shape(outer.cut(inner))
    o = doc.addObject("Part::Feature", name)
    o.Shape = s
    set_material(o, mat)
    if parent: parent.addObject(o)
    return o

def add_box_centered(name, lx, ly, lz, center_vec, mat, parent=None):
    s = Part.makeBox(lx, ly, lz)
    s.translate(center_vec.sub(App.Vector(lx/2.0, ly/2.0, lz/2.0)))
    o = doc.addObject("Part::Feature", name)
    o.Shape = s
    set_material(o, mat)
    if parent: parent.addObject(o)
    return o

def add_bolt(name, shaft_d, head_d, head_h, length, base_vec, mat, parent=None):
    shaft = Part.makeCylinder(shaft_d/2.0, length, App.Vector(0,0,0))
    head = Part.makeCylinder(head_d/2.0, head_h, App.Vector(0,0,length))
    sh = refine_shape(shaft.fuse(head))
    sh.translate(base_vec)
    o = doc.addObject("Part::Feature", name)
    o.Shape = sh
    set_material(o, mat)
    if parent: parent.addObject(o)
    return o

def horizontal_circular_edges(shape, z_window=None, z_tol=0.5):
    edges = []
    for e in shape.Edges:
        c = getattr(e, "Curve", None)
        if c and c.__class__.__name__ == "Circle":
            ax = c.Axis
            v = App.Vector(ax.x, ax.y, ax.z)
            if v.Length == 0: continue
            vn = v.normalize()
            if abs(vn.dot(App.Vector(0,0,1))) > 0.99:
                if z_window:
                    zc = c.Center.z
                    if not (z_window[0]-z_tol <= zc <= z_window[1]+z_tol):
                        continue
                edges.append(e)
    return edges

def apply_fillet_on_hz_edges(obj, radius, z_window=None):
    if radius <= 0: return
    try:
        edges = horizontal_circular_edges(obj.Shape, z_window=z_window)
        if edges:
            obj.Shape = obj.Shape.makeFillet(radius, edges)
    except Exception:
        pass

def apply_chamfer_on_hz_edges(obj, dist, z_window=None):
    if dist <= 0: return
    try:
        edges = horizontal_circular_edges(obj.Shape, z_window=z_window)
        if edges:
            obj.Shape = obj.Shape.makeChamfer(dist, edges)
    except Exception:
        pass

# -----------------------------
# HELICOIDE ROBUSTO
# -----------------------------
def helix_channel_cut(jacket_obj, r_path, pitch, turns, channel_r, z0, approx_step=40):
    """
    Genera un canal helicoidal sólido y lo resta de la chaqueta.
    Maneja errores comunes de orientación y fallos de BRep.
    """
    height = pitch * float(turns)
    if r_path <= 0 or channel_r <= 0:
        raise ValueError("r_path o channel_r no pueden ser negativos o cero.")

    # Crear hélice y wire de trayectoria
    helix = Part.makeHelix(pitch, height, r_path)
    helix.Placement.Base = App.Vector(0, 0, z0)
    try:
        path_wire = Part.Wire(helix)
    except Exception:
        path_wire = helix

    # Perfil circular (perpendicular al eje Z)
    circ_curve = Part.Circle(App.Vector(r_path,0,z0), App.Vector(0,0,1), channel_r)
    circ_edge = Part.Edge(circ_curve)
    circ_wire = Part.Wire([circ_edge])
    circ_face = Part.Face(circ_wire)

    # PipeShell sólido
    sweep = None
    try:
        sweep = circ_face.makePipeShell([path_wire], True, True)
        sweep = sweep.makeSolid()
    except Exception:
        pass

    if sweep is None:
        try:
            sweep = circ_wire.makePipe(path_wire)
        except Exception:
            sweep = None

    if sweep is None:
        # Fallback: cilindros discretos
        pts = helix.discretize(approx_step*int(turns))
        cyls = []
        seg_len = pitch / approx_step
        for p in pts:
            try:
                c = Part.makeCylinder(channel_r, seg_len, App.Vector(p.x, p.y, p.z))
                cyls.append(c)
            except Exception:
                pass
        if cyls:
            sweep = cyls[0]
            for c in cyls[1:]:
                try:
                    sweep = sweep.fuse(c)
                except Exception:
                    pass
        sweep = refine_shape(sweep)

    # Restar canal
    try:
        jacket_obj.Shape = refine_shape(jacket_obj.Shape.cut(sweep))
    except Exception as e:
        App.Console.PrintError(f"[helix_channel_cut] Error al restar canal: {e}\n")

    return sweep

# -----------------------------
# CONTINUAR CON EL RESTO DEL SCRIPT (constructores y ensamblaje)
# -----------------------------
# ... aquí sigue todo igual desde make_part_container hasta main()
# -----------------------------
# CONSTRUCTORES DE PARTES
# -----------------------------
def make_body(P):
    z0 = 0.0
    body_sections = P["body_sections"]
    cyls = []
    for L, D in body_sections:
        c = Part.makeCylinder(D/2.0, L, App.Vector(0,0,z0))
        cyls.append(c)
        z0 += L
    body_shape = cyls[0]
    for c in cyls[1:]:
        body_shape = body_shape.fuse(c)
    body_shape = refine_shape(body_shape)
    obj = doc.addObject("Part::Feature", "Body")
    obj.Shape = body_shape
    set_material(obj, P["mat_body"])
    apply_fillet_on_hz_edges(obj, P["body_edge_fillet"])
    return obj, z0

def make_jacket(P, z0):
    j_in = P["jacket_inner_diam"]/2.0
    j_out = P["jacket_outer_diam"]/2.0
    h = P["jacket_length"]
    jacket = Part.makeCylinder(j_out, h, App.Vector(0,0,z0))
    inner = Part.makeCylinder(j_in, h, App.Vector(0,0,z0))
    jacket_shape = refine_shape(jacket.cut(inner))
    obj = doc.addObject("Part::Feature", "Jacket")
    obj.Shape = jacket_shape
    set_material(obj, P["mat_jacket"])
    apply_fillet_on_hz_edges(obj, P["jacket_edge_fillet"])
    return obj

def make_nozzle(P, z0):
    r_throat = P["nozzle_throat_diam"]/2.0
    r_exit = P["nozzle_exit_diam"]/2.0
    L = P["nozzle_length"]
    precone = L * P["nozzle_precone_ratio"]
    maincone = L * P["nozzle_main_ratio"]
    exitcone = L * P["nozzle_exit_ratio"]
    # Precone
    c1 = Part.makeCone(r_throat*0.9, r_throat, precone, App.Vector(0,0,z0))
    # Main
    c2 = Part.makeCone(r_throat, r_exit*0.95, maincone, App.Vector(0,0,z0+precone))
    # Exit
    c3 = Part.makeCone(r_exit*0.95, r_exit, exitcone, App.Vector(0,0,z0+precone+maincone))
    nozzle_shape = refine_shape(c1.fuse(c2).fuse(c3))
    obj = doc.addObject("Part::Feature", "Nozzle")
    obj.Shape = nozzle_shape
    set_material(obj, P["mat_nozzle"])
    apply_fillet_on_hz_edges(obj, P["nozzle_edge_fillet"])
    return obj

def make_flange(P, z0):
    r_out = P["flange_pcd"]/2.0
    t = P["flange_thickness"]
    flange = Part.makeCylinder(r_out, t, App.Vector(0,0,z0))
    obj = doc.addObject("Part::Feature", "Flange")
    obj.Shape = flange
    apply_chamfer_on_hz_edges(obj, P["flange_edge_chamfer"])
    set_material(obj, P["mat_brkt"])
    # Añadir tornillos
    bolts = []
    for i in range(P["bolt_count"]):
        angle = 2*math.pi*i/P["bolt_count"]
        x = r_out*math.cos(angle)
        y = r_out*math.sin(angle)
        bolts.append(add_bolt(f"Bolt_{i+1}", P["bolt_shaft_d"], P["bolt_head_d"],
                              P["bolt_head_h"], P["bolt_len"],
                              App.Vector(x,y,z0), P["mat_bolt"]))
    return obj, bolts

def make_rad_rings(P, z0):
    rings = []
    for i in range(P["rad_ring_count"]):
        z = z0 + P["rad_first_offset"] + i*P["rad_spacing"]
        r_out = P["rad_ring_outer_diam"]/2.0
        r_in = r_out - P["rad_ring_width"]
        t = P["rad_ring_thickness"]
        rings.append(add_ring_solid(f"RadRing_{i+1}", r_out, r_in, t, z, P["mat_rings"]))
    return rings

def make_tanks(P, body_obj):
    tanks = []
    z_center = P["tank_z_center_offset"]
    r = P["tank_diam"]/2.0
    h = P["tank_height"]
    clearance = P["tank_clearance"]
    for angle_deg in P["tank_angles_deg"]:
        angle_rad = math.radians(angle_deg)
        x = (body_obj.Shape.BoundBox.XLength/2.0 + r + clearance) * math.cos(angle_rad)
        y = (body_obj.Shape.BoundBox.YLength/2.0 + r + clearance) * math.sin(angle_rad)
        tanks.append(add_cyl(f"Tank_{angle_deg}", r, h, z_center, P["mat_tank"]))
        tanks[-1].Placement.Base = App.Vector(x,y,z_center)
    return tanks

def make_quant_modules(P, body_obj):
    modules = []
    n = P["quant_module_count"]
    r_offset = P["quant_radius_offset"]
    for i in range(n):
        angle = 2*math.pi*i/n
        x = r_offset*math.cos(angle)
        y = r_offset*math.sin(angle)
        z = body_obj.Shape.BoundBox.ZLength/2.0
        modules.append(add_cyl(f"QuantModule_{i+1}", P["quant_module_diam"]/2.0,
                                P["quant_module_height"], z, P["mat_quant"]))
        modules[-1].Placement.Base = App.Vector(x,y,z)
    return modules

# -----------------------------
# MAIN
# -----------------------------
def main(P):
    doc = get_doc()
    doc.Objects[:] = []
    z0 = 0.0

    # 1. Cuerpo principal
    body, z0 = make_body(P)

    # 2. Chaqueta con canal helicoidal
    jacket = make_jacket(P, z0)
    helix_channel_cut(jacket, r_path=(P["jacket_inner_diam"]/2.0 - P["helix_margin_wall"]),
                      pitch=P["helix_pitch"],
                      turns=P["helix_turns"],
                      channel_r=P["helix_channel_radius"],
                      z0=z0)

    # 3. Boquilla
    nozzle = make_nozzle(P, z0 + P["jacket_length"])

    # 4. Flange y tornillería
    flange, bolts = make_flange(P, z0)

    # 5. Anillos radiativos
    rad_rings = make_rad_rings(P, z0)

    # 6. Tanques laterales
    tanks = make_tanks(P, body)

    # 7. Módulos cuánticos
    quant_modules = make_quant_modules(P, body)

    doc.recompute()
    App.Console.PrintMessage("HybridPlasmaPropulsion: Generado correctamente.\n")
    return body, jacket, nozzle, flange, bolts, rad_rings, tanks, quant_modules

# Ejecutar
if __name__ == "__main__":
    main(P)
