import FreeCAD as App
import Part
import math

DOC_NAME = "ParkerLikeCraft"

# ============================================================
# Parámetros globales (mm)
# Eje +Z es longitudinal. Cara solar del TPS hacia -Z (plano z=0).
# ============================================================

# TPS (escudo térmico) - escalado 3x
TPS_D = 5400.0      # más ancho para aspecto Parker
TPS_T_TOTAL = 342.0
TPS_COAT_AL2O3 = 0.60
TPS_COAT_W     = 0.15
TPS_CC_FACE    = 15.0
TPS_FOAM       = TPS_T_TOTAL - (TPS_COAT_AL2O3 + TPS_COAT_W + 2*TPS_CC_FACE)

# Apertura frontal (tubo detrás del TPS) - escalado 3x
APERT_D_OUT = 1800.0
APERT_WALL  = 15.0
APERT_D_IN  = APERT_D_OUT - 2*APERT_WALL
APERT_L     = 900.0

# Bus/cuerpo central (más chato y ancho) - escalado 3x
BODY_H        = 4800.0
BODY_OCIRC_D  = 3600.0  # diámetro circunscrito del hexágono

# Fuselaje y cola - escalado 3x
FUSE_D = 3000.0
FUSE_L = 1800.0
CONE_L = 3600.0
CONE_D_BASE = 3000.0

# Tobera - escalado 3x
NOZZLE_L = 1200.0
NOZZLE_D_IN  = 1200.0
NOZZLE_D_OUT = 600.0

# Aletas - escalado 3x, grosor aumentado para impresión 3D
FIN_CHORD = 2100.0
FIN_SPAN  = 1200.0
FIN_THK   = 60.0
FIN_COUNT = 4

# Paneles solares - escalado 3x, grosor aumentado
PAN_L  = 4500.0
PAN_W  = 1800.0
PAN_T  = 90.0
PAN_COUNT = 4  # más paneles

# Booms (FIELDS, 4 antenas) - escalado 3x
BOOM_COUNT = 4
BOOM_L = 5400.0
BOOM_D = 60.0

# Instrumentos - escalado 3x
SPC_D = 270.0
SPC_L = 660.0
WISPR_BOX = (1350.0, 750.0, 600.0)
SWEAP_BOX = (900.0, 600.0, 450.0)
ISOIS_BOX = (960.0, 660.0, 540.0)
MAG_D = 210.0
MAG_L = 600.0
MAG_COUNT = 3

# Blindaje de radiación solar
RAD_SHIELD_D_OUT = BODY_OCIRC_D + 300.0  # alrededor del bus
RAD_SHIELD_D_IN = BODY_OCIRC_D + 30.0
RAD_SHIELD_L = BODY_H + 600.0
RAD_SHIELD_THK = 75.0  # grosor de plomo

# Propulsión iónica adicional
ION_THRUSTER_COUNT = 6  # más thrusters
ION_THRUSTER_D = 300.0
ION_THRUSTER_L = 450.0

# Protección contra meteoritos
METEOR_SHIELD_COUNT = 8
METEOR_SHIELD_D = 500.0
METEOR_SHIELD_T = 100.0

# Antenas de comunicación adicionales
COMM_ANTENNA_COUNT = 4
COMM_ANTENNA_D = 100.0
COMM_ANTENNA_L = 800.0

# Offsets
GAP_TPS_TO_APERT  = 0.0
GAP_APERT_TO_BODY = 0.0
GAP_BODY_TO_FUSE  = 0.0
GAP_FUSE_TO_CONE  = 0.0
GAP_CONE_TO_NOZZLE = 0.0

# ============================================================
# Materiales: ortótropos e isótropos (en PropertyMap "Material")
# ============================================================

def ortho_dict(name, rho, ex, ey, ez, nuxy, nuyz, nuzx, gxy, gyz, gzx,
               kx=None, ky=None, kz=None, cp=None,
               ax=(1,0,0), ay=(0,1,0), az=(0,0,1)):
    d = {
        "Name": name,
        "Type": "Orthotropic",
        "Density": f"{rho} kg/m^3",
        "Ex": f"{ex} Pa",
        "Ey": f"{ey} Pa",
        "Ez": f"{ez} Pa",
        "NuXY": f"{nuxy}",
        "NuYZ": f"{nuyz}",
        "NuZX": f"{nuzx}",
        "GXY": f"{gxy} Pa",
        "GYZ": f"{gyz} Pa",
        "GZX": f"{gzx} Pa",
        "AxisX": f"{ax}",
        "AxisY": f"{ay}",
        "AxisZ": f"{az}",
    }
    if kx is not None: d["kX"] = f"{kx} W/m/K"
    if ky is not None: d["kY"] = f"{ky} W/m/K"
    if kz is not None: d["kZ"] = f"{kz} W/m/K"
    if cp is not None: d["Cp"] = f"{cp} J/kg/K"
    return d

# C-C para las caras del TPS (Z atraviesa el espesor)
MAT_CC_ORTHO = ortho_dict(
    "Carbon-Carbon (TPS face)",
    rho=1700, ex=120e9, ey=80e9, ez=30e9,
    nuxy=0.2, nuyz=0.1, nuzx=0.1,
    gxy=25e9, gyz=10e9, gzx=10e9,
    kx=20, ky=20, kz=5, cp=710
)

# CFRP aletas (eje principal a lo largo de cuerda)
MAT_CFRP_FIN = ortho_dict(
    "CFRP Fin (chord-aligned)",
    rho=1600, ex=140e9, ey=10e9, ez=10e9,
    nuxy=0.28, nuyz=0.3, nuzx=0.3,
    gxy=5e9, gyz=4e9, gzx=4e9,
    kx=6, ky=6, kz=2, cp=800
)

# CFRP panel (rigidez principal en plano)
MAT_CFRP_PANEL = ortho_dict(
    "CFRP Panel (in-plane)",
    rho=1600, ex=120e9, ey=12e9, ez=12e9,
    nuxy=0.28, nuyz=0.3, nuzx=0.3,
    gxy=5.5e9, gyz=4.5e9, gzx=4.5e9,
    kx=8, ky=6, kz=2.5, cp=800
)

MAT_FOAM = {"Name": "Carbon foam", "Type": "Isotropic", "Density": "180 kg/m^3", "E":"0.5 GPa","Nu":"0.25","k":"5 W/m/K","Cp":"710 J/kg/K"}
MAT_AL2O3 = {"Name": "Alumina coating", "Type": "Isotropic", "Density": "3900 kg/m^3", "k":"30 W/m/K","Cp":"880 J/kg/K"}
MAT_W = {"Name": "Tungsten", "Type": "Isotropic", "Density": "19300 kg/m^3", "k":"170 W/m/K","Cp":"134 J/kg/K"}
MAT_AL7075 = {"Name": "Al 7075-T6", "Type": "Isotropic", "Density": "2810 kg/m^3", "E":"71 GPa","Nu":"0.33"}
MAT_IN718 = {"Name": "Inconel 718", "Type": "Isotropic", "Density": "8190 kg/m^3", "E":"200 GPa","Nu":"0.29","k":"11.4 W/m/K","Cp":"435 J/kg/K"}
MAT_SI = {"Name": "Silicon (mono)", "Type": "Isotropic", "Density": "2330 kg/m^3", "k":"148 W/m/K","Cp":"700 J/kg/K"}
MAT_BE = {"Name": "Beryllium", "Type": "Isotropic", "Density": "1850 kg/m^3", "E":"287 GPa","Nu":"0.032","k":"200 W/m/K","Cp":"1825 J/kg/K"}
MAT_TZM = {"Name": "TZM (Ti-Zr-Mo)", "Type": "Isotropic", "Density": "10220 kg/m^3", "k":"126 W/m/K","Cp":"300 J/kg/K"}
MAT_LEAD = {"Name": "Lead", "Type": "Isotropic", "Density": "11340 kg/m^3", "k":"35 W/m/K","Cp":"130 J/kg/K"}

# ============================================================
# Utilidades
# ============================================================

def ensure_doc():
    doc = App.ActiveDocument
    if not doc or doc.Name != DOC_NAME:
        if App.ActiveDocument:
            App.closeDocument(App.ActiveDocument.Name)
        doc = App.newDocument(DOC_NAME)
    return doc

def add_map(obj, name, group, desc):
    try:
        obj.addProperty("App::PropertyMap", name, group, desc)
    except Exception:
        pass

def set_material(obj, matdict):
    add_map(obj, "Material", "FEM", "Material properties")
    m = {}
    for k, v in matdict.items():
        m[str(k)] = str(v)
    obj.Material = m

def set_color(obj, rgb):
    try:
        obj.ViewObject.ShapeColor = rgb
    except Exception:
        pass

def fuse_shapes(shapes):
    res = shapes[0]
    for s in shapes[1:]:
        res = res.fuse(s)
    return res.removeSplitter()

def make_cyl(d, h):
    return Part.makeCylinder(d/2.0, h)

def make_hollow_cyl(d_out, d_in, h):
    return Part.makeCylinder(d_out/2.0, h).cut(Part.makeCylinder(d_in/2.0, h))

def make_cone(d0, d1, h):
    return Part.makeCone(d0/2.0, d1/2.0, h)

def make_hex_prism(ocirc_d, h):
    R = ocirc_d / 2.0
    pts = [App.Vector(R*math.cos(math.radians(60*i)), R*math.sin(math.radians(60*i)), 0) for i in range(6)]
    pts.append(pts[0])
    wire = Part.makePolygon(pts)
    face = Part.Face(wire)
    return face.extrude(App.Vector(0,0,h))

def make_box(lx, ly, lz):
    return Part.makeBox(lx, ly, lz)

def make_tri_fin(chord, span, thk):
    p0 = App.Vector(0, 0, 0)
    p1 = App.Vector(chord, 0, 0)
    p2 = App.Vector(0, 0, span)
    wire = Part.makePolygon([p0, p1, p2, p0])
    face = Part.Face(wire)
    fin = face.extrude(App.Vector(0, thk, 0))
    fin.translate(App.Vector(0, -thk/2.0, 0))
    return fin

# ============================================================
# Construcción
# ============================================================

doc = ensure_doc()
root = doc.addObject("App::Part", "ParkerLikeCraft")

# --- TPS: capas individuales apiladas desde z=0 hacia +Z ---
z = 0.0
layers = []

# Al2O3 (cara solar)
obj_al2o3 = doc.addObject("Part::Feature", "TPS_Al2O3")
obj_al2o3.Shape = make_cyl(TPS_D, TPS_COAT_AL2O3)
obj_al2o3.Placement.Base = App.Vector(0,0,z)
root.addObject(obj_al2o3)
set_material(obj_al2o3, MAT_AL2O3)
set_color(obj_al2o3, (0.95,0.95,1.0))
layers.append(obj_al2o3)
z += TPS_COAT_AL2O3

# Tungsteno
obj_w = doc.addObject("Part::Feature", "TPS_W")
obj_w.Shape = make_cyl(TPS_D, TPS_COAT_W)
obj_w.Placement.Base = App.Vector(0,0,z)
root.addObject(obj_w)
set_material(obj_w, MAT_W)
set_color(obj_w, (0.8,0.8,0.6))
layers.append(obj_w)
z += TPS_COAT_W

# C-C (cara solar)
obj_cc1 = doc.addObject("Part::Feature", "TPS_CC_Solar")
obj_cc1.Shape = make_cyl(TPS_D, TPS_CC_FACE)
obj_cc1.Placement.Base = App.Vector(0,0,z)
root.addObject(obj_cc1)
set_material(obj_cc1, MAT_CC_ORTHO)
set_color(obj_cc1, (0.2,0.2,0.2))
layers.append(obj_cc1)
z += TPS_CC_FACE

# Foam
obj_foam = doc.addObject("Part::Feature", "TPS_Foam")
obj_foam.Shape = make_cyl(TPS_D, TPS_FOAM)
obj_foam.Placement.Base = App.Vector(0,0,z)
root.addObject(obj_foam)
set_material(obj_foam, MAT_FOAM)
set_color(obj_foam, (0.35,0.35,0.35))
layers.append(obj_foam)
z += TPS_FOAM

# C-C (cara sombra)
obj_cc2 = doc.addObject("Part::Feature", "TPS_CC_Shadow")
obj_cc2.Shape = make_cyl(TPS_D, TPS_CC_FACE)
obj_cc2.Placement.Base = App.Vector(0,0,z)
root.addObject(obj_cc2)
set_material(obj_cc2, MAT_CC_ORTHO)
set_color(obj_cc2, (0.22,0.22,0.22))
layers.append(obj_cc2)
z += TPS_CC_FACE

TPS_Z_END = z  # ~114 mm

# --- TPS unificado para mallado como sólido único ---
tps_shapes = [o.Shape.copy().translate(o.Placement.Base) for o in layers]
sh_tps_fused = fuse_shapes(tps_shapes)
obj_tps = doc.addObject("Part::Feature", "TPS_Fused")
obj_tps.Shape = sh_tps_fused
root.addObject(obj_tps)
set_material(obj_tps, {"Name":"TPS_FusedSolid","Note":"Use capas TPS_* para materiales por capa"})
set_color(obj_tps, (0.85,0.9,0.95))

# --- Apertura frontal (tubo) detrás del TPS ---
apert_z0 = TPS_Z_END + GAP_TPS_TO_APERT
obj_apert = doc.addObject("Part::Feature", "ApertureTube")
obj_apert.Shape = make_hollow_cyl(APERT_D_OUT, APERT_D_IN, APERT_L)
obj_apert.Placement.Base = App.Vector(0,0,apert_z0)
root.addObject(obj_apert)
set_material(obj_apert, MAT_AL7075)
set_color(obj_apert, (0.75,0.78,0.82))

# --- Bus hexagonal (más chato y ancho) ---
body_z0 = apert_z0 + APERT_L + GAP_APERT_TO_BODY
obj_bus = doc.addObject("Part::Feature", "BusHex")
obj_bus.Shape = make_hex_prism(BODY_OCIRC_D, BODY_H)
obj_bus.Placement.Base = App.Vector(0,0,body_z0)
root.addObject(obj_bus)
set_material(obj_bus, MAT_AL7075)
set_color(obj_bus, (0.6,0.7,0.9))

# --- Blindaje de radiación solar alrededor del bus ---
rad_shield_z0 = body_z0 - 200.0  # un poco antes y después
obj_rad_shield = doc.addObject("Part::Feature", "RadiationShield")
obj_rad_shield.Shape = make_hollow_cyl(RAD_SHIELD_D_OUT, RAD_SHIELD_D_IN, RAD_SHIELD_L)
obj_rad_shield.Placement.Base = App.Vector(0,0,rad_shield_z0)
root.addObject(obj_rad_shield)
set_material(obj_rad_shield, MAT_LEAD)
set_color(obj_rad_shield, (0.4,0.4,0.4))

# --- Fuselaje cilíndrico ---
fuse_z0 = body_z0 + BODY_H + GAP_BODY_TO_FUSE
obj_fuse = doc.addObject("Part::Feature", "Fuselage")
obj_fuse.Shape = make_cyl(FUSE_D, FUSE_L)
obj_fuse.Placement.Base = App.Vector(0,0,fuse_z0)
root.addObject(obj_fuse)
set_material(obj_fuse, MAT_AL7075)
set_color(obj_fuse, (0.55,0.65,0.85))

# --- Cola cónica ---
cone_z0 = fuse_z0 + FUSE_L + GAP_FUSE_TO_CONE
obj_cone = doc.addObject("Part::Feature", "TailCone")
obj_cone.Shape = make_cone(CONE_D_BASE, 0.0, CONE_L)
obj_cone.Placement.Base = App.Vector(0,0,cone_z0)
root.addObject(obj_cone)
set_material(obj_cone, MAT_IN718)
set_color(obj_cone, (0.5,0.55,0.6))

# --- Tobera ---
noz_z0 = cone_z0 + CONE_L + GAP_CONE_TO_NOZZLE
obj_noz = doc.addObject("Part::Feature", "Nozzle")
obj_noz.Shape = make_cone(NOZZLE_D_IN, NOZZLE_D_OUT, NOZZLE_L)
obj_noz.Placement.Base = App.Vector(0,0,noz_z0)
root.addObject(obj_noz)
set_material(obj_noz, MAT_IN718)
set_color(obj_noz, (0.45,0.5,0.55))

# --- Aletas (CFRP ortótropo, eje principal ~ cuerda) ---
fin_base = make_tri_fin(FIN_CHORD, FIN_SPAN, FIN_THK)
fin_r = FUSE_D/2.0
fin_z_attach = fuse_z0 + FUSE_L*0.5 - FIN_SPAN*0.2
for i in range(FIN_COUNT):
    angle = i*(360.0/FIN_COUNT)
    shape = fin_base.copy()
    shape.translate(App.Vector(0,0,fin_z_attach))
    shape.translate(App.Vector(fin_r - 1.0, 0, 0))   # 1 mm de empotramiento
    shape.rotate(App.Vector(0,0,0), App.Vector(0,0,1), angle)
    obj_fin = doc.addObject("Part::Feature", f"Fin_{i+1}")
    obj_fin.Shape = shape
    root.addObject(obj_fin)
    set_material(obj_fin, MAT_CFRP_FIN)
    set_color(obj_fin, (0.1,0.12,0.16))

# --- Paneles solares (CFRP in-plane) - 4 paneles ---
for i in range(PAN_COUNT):
    pan = make_box(PAN_L, PAN_T, PAN_W)
    obj_pan = doc.addObject("Part::Feature", f"Panel_{i+1}")
    obj_pan.Shape = pan
    root.addObject(obj_pan)
    set_material(obj_pan, MAT_CFRP_PANEL)
    set_color(obj_pan, (0.2,0.25,0.3))
    pan_z = body_z0 + BODY_H*0.5 - PAN_W*0.5
    side_offset = (BODY_OCIRC_D/2.0) + 30.0
    if i < 2:
        y = side_offset
        x_offset = -PAN_L*0.5 if i == 0 else PAN_L*0.5
    else:
        y = -side_offset
        x_offset = -PAN_L*0.5 if i == 2 else PAN_L*0.5
    obj_pan.Placement.Rotation = App.Rotation(App.Vector(1,0,0), 90)
    obj_pan.Placement.Base = App.Vector(x_offset, y - PAN_T*0.5, pan_z)

# --- FIELDS Antennas (4), sobresaliendo hacia -Z alrededor del borde TPS ---
fields_radius = (TPS_D/2.0) - 80.0
for i in range(BOOM_COUNT):
    theta = i*(360.0/BOOM_COUNT)
    x = fields_radius*math.cos(math.radians(theta))
    y = fields_radius*math.sin(math.radians(theta))
    obj_boom = doc.addObject("Part::Feature", f"FIELDS_Antenna_{i+1}")
    obj_boom.Shape = Part.makeCylinder(BOOM_D/2.0, BOOM_L)
    obj_boom.Placement.Rotation = App.Rotation(App.Vector(1,0,0), 180)  # apunta a -Z
    obj_boom.Placement.Base = App.Vector(x, y, 0.0)
    root.addObject(obj_boom)
    set_material(obj_boom, {"Name":"FIELDS_Antenna","Material":"Be or Ti-6Al-4V"})
    set_color(obj_boom, (0.8,0.85,0.9))

# --- SPC (Solar Probe Cup) delante del TPS en -Z ---
obj_spc = doc.addObject("Part::Feature", "SWEAP_SPC")
obj_spc.Shape = Part.makeCylinder(SPC_D/2.0, SPC_L)
obj_spc.Placement.Rotation = App.Rotation(App.Vector(1,0,0), 180)
obj_spc.Placement.Base = App.Vector(TPS_D*0.15, 0, -SPC_L)
root.addObject(obj_spc)
set_material(obj_spc, MAT_TZM)
set_color(obj_spc, (0.7,0.7,0.75))

# --- WISPR (cámara) en costado del bus, mirando -Z ---
obj_wispr = doc.addObject("Part::Feature", "WISPR_Imager")
obj_wispr.Shape = make_box(*WISPR_BOX)
root.addObject(obj_wispr)
set_material(obj_wispr, MAT_AL7075)
set_color(obj_wispr, (0.45,0.5,0.55))
wispr_x = -WISPR_BOX[0]/2.0
wispr_y = (BODY_OCIRC_D/2.0) + 60.0
wispr_z = body_z0 + BODY_H*0.4
obj_wispr.Placement.Base = App.Vector(wispr_x, wispr_y, wispr_z)

# --- SWEAP SPAN A+ detrás del borde del TPS ---
obj_sweap = doc.addObject("Part::Feature", "SWEAP_SPAN_Aplus")
obj_sweap.Shape = make_box(*SWEAP_BOX)
root.addObject(obj_sweap)
set_material(obj_sweap, MAT_AL7075)
set_color(obj_sweap, (0.5,0.55,0.6))
sweap_x = -SWEAP_BOX[0]/2.0
sweap_y = -(BODY_OCIRC_D/2.0) - 40.0
sweap_z = body_z0 + TPS_T_TOTAL*0.5
obj_sweap.Placement.Base = App.Vector(sweap_x, sweap_y, sweap_z)

# --- ISOIS Suite (EPI-Lo/Hi) en el bus ---
obj_isois = doc.addObject("Part::Feature", "ISOIS_Suite")
obj_isois.Shape = make_box(*ISOIS_BOX)
root.addObject(obj_isois)
set_material(obj_isois, MAT_AL7075)
set_color(obj_isois, (0.52,0.56,0.6))
isois_x = -ISOIS_BOX[0]/2.0
isois_y = 0.0
isois_z = body_z0 + BODY_H*0.65
obj_isois.Placement.Base = App.Vector(isois_x, isois_y, isois_z)

# --- FIELDS Magnetometers (3) como pequeños cilindros en un lateral ---
for i in range(MAG_COUNT):
    obj_mag = doc.addObject("Part::Feature", f"FIELDS_Magnetometer_{i+1}")
    obj_mag.Shape = Part.makeCylinder(MAG_D/2.0, MAG_L)
    root.addObject(obj_mag)
    set_material(obj_mag, MAT_AL7075)
    set_color(obj_mag, (0.6,0.6,0.65))
    mag_y = (BODY_OCIRC_D/2.0) + 40.0
    mag_z = body_z0 + BODY_H*0.2 + i*(BODY_H*0.25)
    obj_mag.Placement.Rotation = App.Rotation(App.Vector(0,1,0), 90)
    obj_mag.Placement.Base = App.Vector(0, mag_y, mag_z)

# --- Propulsores iónicos (6) en los costados del bus ---
ion_r = (RAD_SHIELD_D_OUT / 2.0) + 150.0
ion_z = body_z0 + BODY_H * 0.5
for i in range(ION_THRUSTER_COUNT):
    angle = i * (360.0 / ION_THRUSTER_COUNT)
    x = ion_r * math.cos(math.radians(angle))
    y = ion_r * math.sin(math.radians(angle))
    obj_ion = doc.addObject("Part::Feature", f"IonThruster_{i+1}")
    obj_ion.Shape = Part.makeCylinder(ION_THRUSTER_D/2.0, ION_THRUSTER_L)
    obj_ion.Placement.Rotation = App.Rotation(App.Vector(1,0,0), 90)  # apunta radialmente
    obj_ion.Placement.Base = App.Vector(x, y, ion_z)
    root.addObject(obj_ion)
    set_material(obj_ion, MAT_IN718)
    set_color(obj_ion, (0.8,0.8,0.9))

# --- Escudos contra meteoritos (8) distribuidos ---
meteor_r = (RAD_SHIELD_D_OUT / 2.0) + 200.0
meteor_z = body_z0 + BODY_H * 0.3
for i in range(METEOR_SHIELD_COUNT):
    angle = i * (360.0 / METEOR_SHIELD_COUNT)
    x = meteor_r * math.cos(math.radians(angle))
    y = meteor_r * math.sin(math.radians(angle))
    obj_meteor = doc.addObject("Part::Feature", f"MeteorShield_{i+1}")
    obj_meteor.Shape = make_cyl(METEOR_SHIELD_D, METEOR_SHIELD_T)
    obj_meteor.Placement.Base = App.Vector(x, y, meteor_z)
    root.addObject(obj_meteor)
    set_material(obj_meteor, MAT_W)  # Tungsten for impact resistance
    set_color(obj_meteor, (0.5,0.5,0.5))

# --- Antenas de comunicación (4) ---
comm_r = (TPS_D / 2.0) + 100.0
for i in range(COMM_ANTENNA_COUNT):
    angle = i * (360.0 / COMM_ANTENNA_COUNT) + 45  # offset
    x = comm_r * math.cos(math.radians(angle))
    y = comm_r * math.sin(math.radians(angle))
    obj_comm = doc.addObject("Part::Feature", f"CommAntenna_{i+1}")
    obj_comm.Shape = Part.makeCylinder(COMM_ANTENNA_D/2.0, COMM_ANTENNA_L)
    obj_comm.Placement.Rotation = App.Rotation(App.Vector(1,0,0), 180)  # apunta hacia afuera
    obj_comm.Placement.Base = App.Vector(x, y, TPS_Z_END)
    root.addObject(obj_comm)
    set_material(obj_comm, MAT_AL7075)
    set_color(obj_comm, (0.9,0.9,0.9))

# Recalcular
doc.recompute()

TOTAL_LEN = TPS_T_TOTAL + APERT_L + BODY_H + FUSE_L + CONE_L + NOZZLE_L
print("Longitud total aproximada (mm):", TOTAL_LEN)
print("Documento:", doc.Name)
print("Nota: TPS_Fused es un sólido único para mallado; capas TPS_* conservan materiales por capa.")
print("Mejoras: Escalado 3x, blindaje de radiación añadido, propulsores iónicos (6), escudos contra meteoritos, antenas de comunicación, paneles solares extra, grosor aumentado para impresión 3D, protección contra impactos.")
