
# -*- coding: utf-8 -*-
# Unified Macro: Parametric Satellite Assembly with DFD XL Ship
# Combines the parametric satellite and the DFD XL spaceship into a coherent assembly.
# The satellite is built in meters, the ship is scaled from mm to meters and attached to the satellite's Orion module.
# Result: A hybrid spacecraft-satellite for extreme missions.

import FreeCAD as App
import Part
import MeshPart
import math
from FreeCAD import Vector

DOC_NAME = "Unified_Satellite_Ship"

def new_doc(name):
    doc = App.newDocument(name) if App.ActiveDocument is None else App.ActiveDocument
    if doc.Name != name:
        doc = App.newDocument(name)
    return doc

doc = new_doc(DOC_NAME)

# -----------------------
# Helpers: properties (from satellite macro)
# -----------------------

def tag_material(obj, material="Al6061", density=2700.0, alpha=0.2, epsilon=0.8, t_nom=0.002):
    if not hasattr(obj, "Material"):
        obj.addProperty("App::PropertyString", "Material", "FEM", "Material tag")
    if not hasattr(obj, "Density"):
        obj.addProperty("App::PropertyFloat", "Density", "FEM", "Density kg/m^3")
    if not hasattr(obj, "Alpha"):
        obj.addProperty("App::PropertyFloat", "Alpha", "Thermal", "Solar absorptivity")
    if not hasattr(obj, "Epsilon"):
        obj.addProperty("App::PropertyFloat", "Epsilon", "Thermal", "Emissivity")
    if not hasattr(obj, "t_nom"):
        obj.addProperty("App::PropertyFloat", "t_nom", "FEM", "Nominal shell thickness")
    obj.Material = material
    obj.Density = density
    obj.Alpha = alpha
    obj.Epsilon = epsilon
    obj.t_nom = t_nom

def color(obj, rgb=(0.8,0.8,0.8)):
    try:
        obj.ViewObject.ShapeColor = rgb
    except Exception:
        pass

# -----------------------
# Helpers: primitives (from satellite macro)
# -----------------------

def make_cylinder(name, R, L, base=Vector(0,0,0), axis=Vector(1,0,0)):
    shape = Part.makeCylinder(R, L, Vector(0,0,0), Vector(1,0,0))
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    obj.Placement.Base = base
    return obj

def make_cone_truncated(name, R1, R2, L, base=Vector(0,0,0), axis=Vector(1,0,0)):
    shape = Part.makeCone(R1, R2, L, Vector(0,0,0), Vector(1,0,0))
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    obj.Placement.Base = base
    return obj

def make_box(name, X, Y, Z, base=Vector(0,0,0)):
    shape = Part.makeBox(X, Y, Z, Vector(0,0,0))
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    obj.Placement.Base = base
    return obj

def make_sphere(name, R, center=Vector(0,0,0)):
    shape = Part.makeSphere(R, center)
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    return obj

def make_annular_flange(name, R_inner, R_outer, t, base=Vector(0,0,0)):
    c_out = Part.makeCylinder(R_outer, t, Vector(0,0,0), Vector(1,0,0))
    c_in  = Part.makeCylinder(R_inner, t+1e-6, Vector(0,0,0), Vector(1,0,0))
    ring = c_out.cut(c_in)
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = ring
    obj.Placement.Base = base
    return obj

def polar_bolt_circle(name_prefix, N, R_pcd, L, d, base=Vector(0,0,0)):
    bolts = []
    for i in range(N):
        theta = 2*math.pi*i/float(N)
        y = R_pcd*math.cos(theta)
        z = R_pcd*math.sin(theta)
        bolt = Part.makeCylinder(d/2.0, L, Vector(0,0,0), Vector(1,0,0))
        bolt_obj = doc.addObject("Part::Feature", f"{name_prefix}_{i+1:02d}")
        bolt_obj.Shape = bolt
        bolt_obj.Placement.Base = base.add(Vector(0, y, z))
        bolts.append(bolt_obj)
    return bolts

def make_tube(name, R_outer, t, L, base=Vector(0,0,0)):
    c_out = Part.makeCylinder(R_outer, L, Vector(0,0,0), Vector(1,0,0))
    c_in  = Part.makeCylinder(max(R_outer - t, 0.0), L+1e-6, Vector(0,0,0), Vector(1,0,0))
    tube = c_out.cut(c_in)
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = tube
    obj.Placement.Base = base
    return obj

def make_paraboloid_dish(name, D, p, t=0.003, base=Vector(0,0,0)):
    R = D/2.0
    f = (D*D)/(16.0*p)
    pts = []
    N = 40
    for i in range(N+1):
        r = R * i/float(N)
        z = (r*r)/(4.0*f)
        pts.append(Vector(0, r, z))
    spline = Part.BSplineCurve()
    spline.interpolate(pts)
    edge = spline.toShape()
    axis = Vector(1,0,0)
    face_outer = Part.Wire([edge]).revolve(Vector(0,0,0), axis, 360)
    solid_outer = face_outer
    pts_in = []
    for i in range(N+1):
        r = R * i/float(N)
        z = (r*r)/(4.0*f) - t
        pts_in.append(Vector(0, r, max(z, 0.0)))
    spline_in = Part.BSplineCurve()
    spline_in.interpolate(pts_in)
    edge_in = spline_in.toShape()
    face_inner = Part.Wire([edge_in]).revolve(Vector(0,0,0), axis, 360)
    dish = solid_outer.cut(face_inner)
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = dish
    obj.Placement.Base = base
    return obj

# -----------------------
# Truss builder (from satellite macro)
# -----------------------

def make_truss_bus(name, L_tr=2.2, W_tr=1.2, H_tr=1.0, b=0.08, h=0.08, d_cordon=0.06, base=Vector(0,0,0)):
    group = doc.addObject("App::DocumentObjectGroup", name)
    offs = [
        Vector(0, +W_tr/2.0, +H_tr/2.0),
        Vector(0, +W_tr/2.0, -H_tr/2.0),
        Vector(0, -W_tr/2.0, +H_tr/2.0),
        Vector(0, -W_tr/2.0, -H_tr/2.0),
    ]
    for i,o in enumerate(offs):
        tube = make_tube(f"{name}_Chord_{i+1}", d_cordon/2.0, t=d_cordon/10.0, L=L_tr, base=base.add(o))
        color(tube, (0.2,0.2,0.25))
        tag_material(tube, "Al6061", 2700, 0.2, 0.1, 0.003)
        group.addObject(tube)
    nframes = int(L_tr/0.55)+1
    for k in range(nframes):
        xk = base.x + k*(L_tr/(nframes-1 if nframes>1 else 1))
        beam_top = make_box(f"{name}_FrameTop_{k}",  b, W_tr, b, base=Vector(xk, -W_tr/2.0,  H_tr/2.0 - b/2.0))
        beam_bot = make_box(f"{name}_FrameBot_{k}",  b, W_tr, b, base=Vector(xk, -W_tr/2.0, -H_tr/2.0 - b/2.0))
        beam_l   = make_box(f"{name}_FrameLeft_{k}", b, b, H_tr, base=Vector(xk, +W_tr/2.0 - b/2.0, -H_tr/2.0))
        beam_r   = make_box(f"{name}_FrameRight_{k}",b, b, H_tr, base=Vector(xk, -W_tr/2.0 - b/2.0, -H_tr/2.0))
        for be in [beam_top, beam_bot, beam_l, beam_r]:
            color(be, (0.35,0.35,0.4))
            tag_material(be, "CFRP", 1600, 0.2, 0.1, 0.003)
            group.addObject(be)
    bay = 0.55
    ndiag = int(L_tr/bay)
    for j in range(ndiag):
        x0 = base.x + j*bay
        diag1 = Part.makeBox(b, bay, b, Vector(x0, +W_tr/2.0 - b/2.0, -H_tr/2.0 - b/2.0))
        d1_obj = doc.addObject("Part::Feature", f"{name}_Diag_{j}")
        d1_obj.Shape = diag1
        color(d1_obj, (0.4,0.4,0.45))
        tag_material(d1_obj, "CFRP", 1600, 0.2, 0.1, 0.003)
        group.addObject(d1_obj)
    return group

# -----------------------
# Geometry parameters (satellite)
# -----------------------

P_sat = {
    "A_L_tr": 2.2, "A_b": 0.08, "A_h": 0.08, "A_W_tr": 1.2, "A_H_tr": 1.0, "A_cordon": 0.06,
    "A_Box": (1.2, 1.0, 0.8),
    "A_Tank": (0.45, 0.9),
    "A_Bolts": (48, 1.6, 0.014),
    "B_L": 7.0, "B_W": 2.0, "B_t": 0.02, "B_Mast": (0.15, 0.25, 1.2), "B_Hinge": (0.05, 0.12),
    "C_R": 1.60, "C_L": 3.5, "C_t": 0.003, "C_brida_PCD": 3.1, "C_brida_N": 72, "C_brida_t": 0.012,
    "D_R": 1.60, "D_L": 2.2, "D_t": 0.003,
    "E_R": 1.0, "E_L": 1.0, "E_t": 0.002, "E_cone_L": 0.45, "E_R2": 1.60,
    "F_R1": 1.35, "F_R2": 2.10, "F_L": 1.7, "F_Rbase": 1.35, "F_Lbase": 0.6,
    "G_L_ogiva": 1.9, "G_Dmax": 3.1, "G_R_sm": 1.25, "G_L_sm": 1.1, "G_R_adapter1": 1.3, "G_R_adapter2": 1.0, "G_L_adapter": 0.4,
    "H_R": 0.60, "H_L": 1.4, "H_Mast": (0.06, 0.8),
    "I_R": 0.85, "I_Rneck": 0.55, "I_Lneck": 0.5,
    "J_Panel": (1.2, 0.8, 0.02), "J_HGA_D": 0.9, "J_HGA_p": 0.11, "J_Mast": (0.04, 0.6),
    "K_Panel": (1.6, 1.1, 0.015), "K_TubeR": 0.006,
    "L_Trunk": 0.0125, "L_Branch": 0.006,
    "Gap": 0.08
}

# -----------------------
# Build satellite chain along X
# -----------------------

x = 0.0
gap = P_sat["Gap"]

E_R = P_sat["E_R"]; E_L = P_sat["E_L"]; E_cone_L = P_sat["E_cone_L"]; E_R2 = P_sat["E_R2"]
x_E_start = - (E_cone_L + E_L + E_cone_L)/2.0
E_cone_L_obj = make_cone_truncated("E_ConeLeft", E_R2, E_R, E_cone_L, base=Vector(x_E_start,0,0))
E_cyl_obj   = make_cylinder("E_Cyl", E_R, E_L, base=Vector(x_E_start+E_cone_L,0,0))
E_cone_R_obj = make_cone_truncated("E_ConeRight", E_R, E_R2, E_cone_L, base=Vector(x_E_start+E_cone_L+E_L,0,0))
for eo in [E_cone_L_obj, E_cyl_obj, E_cone_R_obj]:
    color(eo, (0.75,0.75,0.78)); tag_material(eo, "Al2219", 2840, 0.15, 0.08, P_sat["E_t"])

C_R = P_sat["C_R"]; C_L = P_sat["C_L"]
x_C = x_E_start - gap - C_L
C_cyl = make_cylinder("C_Hab1", C_R, C_L, base=Vector(x_C,0,0))
color(C_cyl, (0.9,0.9,0.95)); tag_material(C_cyl, "CFRP", 1600, 0.15, 0.05, P_sat["C_t"])
C_brida = make_annular_flange("C_Flange_R", R_inner=E_R*0.98, R_outer=P_sat["C_brida_PCD"]/2.0*0.5+E_R, t=P_sat["C_brida_t"], base=Vector(x_E_start - P_sat["C_brida_t"],0,0))
color(C_brida, (0.8,0.8,0.85)); tag_material(C_brida, "Al6061", 2700, 0.15, 0.08, 0.012)
Cb_N = P_sat["C_brida_N"]; Cb_PCD = P_sat["C_brida_PCD"]/2.0
_ = polar_bolt_circle("C_E_Bolt", N=Cb_N, R_pcd=Cb_PCD, L=0.02, d=0.014, base=Vector(x_E_start - 0.02, 0, 0))

A_L = P_sat["A_L_tr"]
x_A = x_C - gap - A_L
A_truss = make_truss_bus("A_Bus", L_tr=A_L, W_tr=P_sat["A_W_tr"], H_tr=P_sat["A_H_tr"], b=P_sat["A_b"], h=P_sat["A_h"], d_cordon=P_sat["A_cordon"], base=Vector(x_A,0,0))
bx, by, bz = P_sat["A_Box"]
A_box = make_box("A_ElecBox", bx, by, bz, base=Vector(x_A + (A_L-bx)/2.0, -by/2.0, -bz/2.0))
color(A_box, (0.2,0.35,0.6)); tag_material(A_box, "Al6061", 2700, 0.2, 0.8, 0.005)
tR, tL = P_sat["A_Tank"]; A_tank = make_cylinder("A_Tank", tR, tL, base=Vector(x_A + 0.2, 0, -tR))
color(A_tank, (0.85,0.85,0.9)); tag_material(A_tank, "Al2219", 2840, 0.2, 0.1, 0.005)

N_thr = 6; thr_R = 0.06; thr_L = 0.18; PCD_thr = 0.5
for i in range(N_thr):
    th = 2*math.pi*i/N_thr
    y = PCD_thr*math.cos(th)
    z = PCD_thr*math.sin(th)
    thr = make_cylinder(f"A_Thr_{i+1}", thr_R, thr_L, base=Vector(x_A + 0.2 + tL + 0.05, y, z - thr_R))
    color(thr, (0.5,0.5,0.55)); tag_material(thr, "Ti", 4430, 0.2, 0.8, 0.006)

BL, BW, Bt = P_sat["B_L"], P_sat["B_W"], P_sat["B_t"]
B_left = make_box("B_Left", BL, Bt, BW, base=Vector(x_A + 0.3, -Bt/2.0, P_sat["A_H_tr"]/2.0 + 0.05))
color(B_left, (0.1,0.1,0.2)); tag_material(B_left, "Panel_CFRP", 550, 0.2, 0.8, Bt)
B_right = make_box("B_Right", BL, Bt, BW, base=Vector(x_A + 0.3, -Bt/2.0, -P_sat["A_H_tr"]/2.0 - BW - 0.05))
color(B_right, (0.1,0.1,0.2)); tag_material(B_right, "Panel_CFRP", 550, 0.2, 0.8, Bt)

D_R = P_sat["D_R"]; D_L = P_sat["D_L"]
x_D = x_E_start + E_cone_L + E_L + E_cone_L + gap
D_cyl = make_cylinder("D_Hab2", D_R, D_L, base=Vector(x_D,0,0))
color(D_cyl, (0.92,0.92,0.96)); tag_material(D_cyl, "CFRP", 1600, 0.15, 0.05, P_sat["D_t"])
D_brida = make_annular_flange("D_Flange_L", R_inner=E_R*0.98, R_outer=(P_sat["C_brida_PCD"]/2.0)*0.5+E_R, t=P_sat["C_brida_t"], base=Vector(x_E_start + E_cone_L + E_L + E_cone_L,0,0))
color(D_brida, (0.8,0.8,0.85)); tag_material(D_brida, "Al6061", 2700, 0.15, 0.08, 0.012)

G_adapter = make_cone_truncated("G_Adapter", P_sat["G_R_adapter1"], P_sat["G_R_adapter2"], P_sat["G_L_adapter"], base=Vector(x_D + D_L + gap,0,0))
color(G_adapter, (0.75,0.78,0.8)); tag_material(G_adapter, "AlTi", 3000, 0.3, 0.7, 0.006)
G_sm = make_cylinder("G_SM", P_sat["G_R_sm"], P_sat["G_L_sm"], base=Vector(G_adapter.Placement.Base.x + P_sat["G_L_adapter"],0,0))
color(G_sm, (0.7,0.72,0.76)); tag_material(G_sm, "Al2219", 2840, 0.3, 0.6, 0.004)
G_Rmax = P_sat["G_Dmax"]/2.0
G_cone = make_cone_truncated("G_Cone", P_sat["G_R_adapter2"], G_Rmax, P_sat["G_L_ogiva"]*0.7, base=Vector(G_sm.Placement.Base.x + P_sat["G_L_sm"],0,0))
G_cap  = make_cylinder("G_Cap", G_Rmax, P_sat["G_L_ogiva"]*0.3, base=Vector(G_cone.Placement.Base.x + G_cone.Shape.BoundBox.XLength,0,0))
for go in [G_cone, G_cap]:
    color(go, (0.6,0.62,0.66)); tag_material(go, "TPS_Composite", 1800, 0.5, 0.8, 0.01)

F_neck_R = 1.05; F_neck_L = 0.35
x_F = x_C + C_L*0.6
F_neck = make_cylinder("F_Neck", F_neck_R, F_neck_L, base=Vector(x_F, C_R + F_neck_R*0.1, 0))
F_cone = make_cone_truncated("F_Cone", P_sat["F_R1"], P_sat["F_R2"], P_sat["F_L"], base=Vector(x_F + F_neck_L, C_R + F_neck_R*0.1, 0))
F_base = make_cylinder("F_Base", P_sat["F_Rbase"], P_sat["F_Lbase"], base=Vector(F_cone.Placement.Base.x + P_sat["F_L"], C_R + F_neck_R*0.1, 0))
for fo in [F_neck, F_cone, F_base]:
    color(fo, (0.55,0.57,0.6)); tag_material(fo, "Ti_Al_Ablative", 2000, 0.4, 0.8, 0.01)

H_R = P_sat["H_R"]; H_L = P_sat["H_L"]
H_cyl = make_cylinder("H_Log", H_R, H_L, base=Vector(x_E_start + E_cone_L + E_L/2.0 - H_L/2.0, 0, -E_R - H_R - 0.2))
color(H_cyl, (0.75,0.77,0.8)); tag_material(H_cyl, "Al6061", 2700, 0.25, 0.7, 0.004)
H_mast = make_cylinder("H_AntennaMast", P_sat["H_Mast"][0]/2.0, P_sat["H_Mast"][1], base=Vector(H_cyl.Placement.Base.x + H_L + 0.05, 0, H_cyl.Placement.Base.z - P_sat["H_Mast"][0]/2.0))
color(H_mast, (0.2,0.2,0.25)); tag_material(H_mast, "CFRP", 1600, 0.2, 0.9, 0.003)

I_sph = make_sphere("I_Sphere", P_sat["I_R"], center=Vector(x_E_start + E_cone_L + E_L*0.2, E_R + P_sat["I_R"] + 0.15, 0))
color(I_sph, (0.88,0.9,0.95)); tag_material(I_sph, "Ti_Al", 3000, 0.25, 0.7, 0.003)
I_neck = make_cylinder("I_Neck", P_sat["I_Rneck"], P_sat["I_Lneck"], base=Vector(x_E_start + E_cone_L + E_L*0.2 - P_sat["I_Lneck"], E_R + 0.15, 0))
color(I_neck, (0.85,0.87,0.92)); tag_material(I_neck, "Al2219", 2840, 0.25, 0.7, 0.003)
for i in range(4):
    dz = (-0.3 + 0.2*i)
    bracket = make_box(f"I_Bracket_{i+1}", 0.25, 0.05, 0.12, base=Vector(I_neck.Placement.Base.x + 0.02, E_R + 0.12, dz))
    color(bracket, (0.7,0.7,0.75)); tag_material(bracket, "Al6061", 2700, 0.2, 0.8, 0.006)

for side, sgn in [("J_Panel_L", +1), ("J_Panel_R", -1)]:
    px, py, pz = P_sat["J_Panel"]
    pan = make_box(side, px, py, pz, base=Vector(x_C + C_L*0.4, sgn*(C_R + 0.2), -pz/2.0))
    color(pan, (0.95,0.85,0.2)); tag_material(pan, "Panel_Antenna", 900, 0.6, 0.8, py)
    mast = make_cylinder(f"{side}_Mast", P_sat["J_Mast"][0]/2.0, P_sat["J_Mast"][1], base=Vector(x_C + C_L*0.4 - 0.1, sgn*(C_R + 0.2), -P_sat["J_Mast"][0]/2.0))
    color(mast, (0.25,0.25,0.3)); tag_material(mast, "CFRP", 1600, 0.2, 0.9, 0.003)

J_dish = make_paraboloid_dish("J_HGA_Dish", P_sat["J_HGA_D"], P_sat["J_HGA_p"], t=0.003, base=Vector(x_E_start + E_cone_L + E_L*0.6, -(E_R + 0.6), 0))
color(J_dish, (0.95,0.95,0.95)); tag_material(J_dish, "Al_Coated", 2700, 0.3, 0.85, 0.003)
J_mast = make_cylinder("J_HGA_Mast", P_sat["J_Mast"][0]/2.0, P_sat["J_Mast"][1], base=Vector(J_dish.Placement.Base.x - 0.1, -(E_R + 0.6), -P_sat["J_Mast"][0]/2.0))
color(J_mast, (0.25,0.25,0.3)); tag_material(J_mast, "CFRP", 1600, 0.2, 0.9, 0.003)

kx, ky, kz = P_sat["K_Panel"]
K1 = make_box("K_Rad_C", kx, ky, kz, base=Vector(x_C + 0.6, C_R + 0.05, -kz/2.0))
K2 = make_box("K_Rad_D", kx, ky, kz, base=Vector(x_D + 0.4, -(D_R + 0.05) - ky, -kz/2.0))
for k in [K1, K2]:
    color(k, (0.9,0.9,0.95)); tag_material(k, "Radiator", 120, 0.15, 0.85, kz)
for baseX in [K1.Placement.Base.x + kx/2.0, K2.Placement.Base.x + kx/2.0]:
    tube = make_cylinder("K_Loop", P_sat["K_TubeR"], 1.2, base=Vector(baseX, 0.0, -P_sat["K_TubeR"]))
    color(tube, (0.8,0.8,0.85)); tag_material(tube, "CoolantTube", 2700, 0.3, 0.8, 0.002)

L_len = (x_D + D_L + P_sat["G_L_ogiva"] + 2.0) - (x_A - 0.5)
wire = make_cylinder(f"L_Trunk_1", P_sat["L_Trunk"], L_len, base=Vector(x_A - 0.5, +C_R + 0.3, +(C_R + 0.3)))
color(wire, (0.2,0.2,0.2)); tag_material(wire, "Harness", 3500, 0.3, 0.8, 0.01)
wire2 = make_cylinder(f"L_Trunk_2", P_sat["L_Trunk"], L_len, base=Vector(x_A - 0.5, +C_R + 0.3, -(C_R + 0.3)))
color(wire2, (0.2,0.2,0.2)); tag_material(wire2, "Harness", 3500, 0.3, 0.8, 0.01)

# Bolts and flanges for satellite
EC_N = P_sat["C_brida_N"]
EC_PCD = P_sat["C_brida_PCD"] / 2.0
EC_x = x_E_start
EC_bolts = polar_bolt_circle("Bolt_EC", N=EC_N, R_pcd=EC_PCD, L=0.02, d=0.014, base=Vector(EC_x - 0.01, 0, 0))
for b in EC_bolts:
    color(b, (0.35, 0.35, 0.35)); tag_material(b, "Bolt_Steel", 7850, 0.2, 0.7, 0.014)
try:
    fused = EC_bolts[0].Shape
    for bb in EC_bolts[1:]:
        fused = fused.fuse(bb.Shape)
    C_brida.Shape = C_brida.Shape.cut(fused)
except Exception:
    pass

ED_N = P_sat["C_brida_N"]
ED_PCD = P_sat["C_brida_PCD"] / 2.0
ED_x = x_E_start + E_cone_L + E_L + E_cone_L
ED_bolts = polar_bolt_circle("Bolt_ED", N=ED_N, R_pcd=ED_PCD, L=0.02, d=0.014, base=Vector(ED_x + 0.01, 0, 0))
for b in ED_bolts:
    color(b, (0.35, 0.35, 0.35)); tag_material(b, "Bolt_Steel", 7850, 0.2, 0.7, 0.014)
try:
    fused = ED_bolts[0].Shape
    for bb in ED_bolts[1:]:
        fused = fused.fuse(bb.Shape)
    D_brida.Shape = D_brida.Shape.cut(fused)
except Exception:
    pass

A_N, A_PCD_diam, A_bolt_d = P_sat["A_Bolts"]
A_PCD = A_PCD_diam / 2.0
AC_x = x_C - P_sat["C_brida_t"] - 0.02
A_flange = make_annular_flange("A_Flange_C", R_inner=A_PCD - 0.06, R_outer=A_PCD + 0.06, t=P_sat["C_brida_t"], base=Vector(AC_x, 0, 0))
color(A_flange, (0.8, 0.8, 0.85)); tag_material(A_flange, "Al6061", 2700, 0.15, 0.08, 0.012)
AC_bolts = polar_bolt_circle("Bolt_AC", N=A_N, R_pcd=A_PCD, L=0.02, d=A_bolt_d, base=Vector(AC_x - 0.005, 0, 0))
for b in AC_bolts:
    color(b, (0.35, 0.35, 0.35)); tag_material(b, "Bolt_Steel", 7850, 0.2, 0.7, A_bolt_d)

F_ring_R = 2.1 / 2.0
F_ring_x = F_base.Placement.Base.x + 0.02
F_ring = make_annular_flange("F_Dock_Ring", R_inner=F_ring_R - 0.06, R_outer=F_ring_R + 0.06, t=0.012, base=Vector(F_ring_x, F_base.Placement.Base.y, F_base.Placement.Base.z))
color(F_ring, (0.78, 0.78, 0.82)); tag_material(F_ring, "Ti_Al", 3000, 0.3, 0.7, 0.012)
F_bolts = polar_bolt_circle("Bolt_F_Dock", N=60, R_pcd=F_ring_R, L=0.02, d=0.014, base=Vector(F_ring_x, F_base.Placement.Base.y, F_base.Placement.Base.z))
for b in F_bolts:
    color(b, (0.35, 0.35, 0.35)); tag_material(b, "Bolt_Steel", 7850, 0.2, 0.7, 0.014)

G_ring_R = 2.6 / 2.0
G_ring_x = G_adapter.Placement.Base.x - 0.01
G_ring = make_annular_flange("G_Adapter_Ring", R_inner=G_ring_R - 0.07, R_outer=G_ring_R + 0.07, t=0.012, base=Vector(G_ring_x, 0, 0))
color(G_ring, (0.78, 0.8, 0.82)); tag_material(G_ring, "AlTi", 3000, 0.3, 0.7, 0.012)
G_bolts = polar_bolt_circle("Bolt_G_Adapt", N=80, R_pcd=G_ring_R, L=0.02, d=0.014, base=Vector(G_ring_x - 0.005, 0, 0))
for b in G_bolts:
    color(b, (0.35, 0.35, 0.35)); tag_material(b, "Bolt_Steel", 7850, 0.2, 0.7, 0.014)

H_coll_R = 1.2 / 2.0
H_ring = make_annular_flange("H_Collar", R_inner=H_coll_R - 0.05, R_outer=H_coll_R + 0.05, t=0.010,
                             base=Vector(H_cyl.Placement.Base.x + H_L*0.5, 0, H_cyl.Placement.Base.z + H_R + 0.02))
color(H_ring, (0.8, 0.8, 0.85)); tag_material(H_ring, "Al6061", 2700, 0.2, 0.7, 0.010)
H_bolts = polar_bolt_circle("Bolt_H_Collar", N=36, R_pcd=H_coll_R, L=0.02, d=0.012,
                            base=Vector(H_ring.Placement.Base.x, H_ring.Placement.Base.y, H_ring.Placement.Base.z))
for b in H_bolts:
    color(b, (0.35, 0.35, 0.35)); tag_material(b, "Bolt_Steel", 7850, 0.2, 0.7, 0.012)

I_PCD_R = 1.1 / 2.0
I_ring = make_annular_flange("I_Collar", R_inner=I_PCD_R - 0.05, R_outer=I_PCD_R + 0.05, t=0.010,
                             base=Vector(I_neck.Placement.Base.x + P_sat["I_Lneck"] - 0.005, I_neck.Placement.Base.y, I_neck.Placement.Base.z))
color(I_ring, (0.82, 0.84, 0.88)); tag_material(I_ring, "Al2219", 2840, 0.25, 0.7, 0.010)
I_bolts = polar_bolt_circle("Bolt_I_Collar", N=32, R_pcd=I_PCD_R, L=0.02, d=0.012,
                            base=Vector(I_ring.Placement.Base.x, I_ring.Placement.Base.y, I_ring.Placement.Base.z))
for b in I_bolts:
    color(b, (0.35, 0.35, 0.35)); tag_material(b, "Bolt_Steel", 7850, 0.2, 0.7, 0.012)

# Mesh hints for satellite
def set_mesh_hint(obj, h):
    if not hasattr(obj, "MeshSizeHint"):
        obj.addProperty("App::PropertyFloat", "MeshSizeHint", "Mesh", "Target mesh edge length")
    obj.MeshSizeHint = float(h)

for o in [C_cyl, D_cyl, E_cyl_obj, E_cone_L_obj, E_cone_R_obj, G_cone, G_cap, F_cone, F_base, F_neck, I_sph, I_neck]:
    set_mesh_hint(o, 0.15)
for o in [C_brida, D_brida, A_flange, F_ring, G_ring, H_ring, I_ring]:
    set_mesh_hint(o, 0.05)
for o in [B_left, B_right, K1, K2]:
    set_mesh_hint(o, 0.20)
for o in A_truss.Group:
    set_mesh_hint(o, 0.12)
for o in [J_dish, J_mast, H_mast]:
    set_mesh_hint(o, 0.12)

# Now, build the DFD XL ship, scaled to meters and attached to the satellite's end
# Parameters scaled from mm to m
P_ship = {
    'scale': 2.0,
    'nose_len': 1.5, 'nose_base_d': 1.1,
    'mid_len': 3.0, 'mid_d': 1.8,
    'rear_len': 1.5, 'rear_d': 2.2,
    'hull_t': 0.03,
    'shield_d': 2.6, 'shield_flecha': 0.08, 't_ceramic': 0.004, 't_foam': 0.12, 't_cc': 0.012, 'rim_w': 0.06, 'rim_h': 0.08,
    'hull_shield_t': 0.08, 'hull_shield_l': 2.8,
    'reactor_shield_t': 0.12, 'reactor_shield_l': 2.2,
    'reactor_d': 1.5, 'reactor_l': 1.8,
    'hab_d': 1.4, 'hab_l': 2.5,
    'cockpit_d': 0.9, 'cockpit_l': 0.8, 'window_r': 0.15,
    'tank_r': 0.4, 'tank_l': 2.0, 'tank_off': 1.2,
    'sphere_r': 0.45, 'sphere_off': 1.6,
    'wing_span': 2.5, 'wing_th': 0.06, 'wing_l': 2.2, 'wing_back_offset': 1.2,
    'collar_d_delta': 0.3, 'collar_h': 0.12, 'collar_t': 0.04,
    'def_count': 8, 'def_l': 0.8, 'def_w': 0.16, 'def_t': 0.03,
    'mast_l': 1.0, 'mast_r': 0.04, 'dish_r': 0.4,
    'leg_r': 0.1, 'leg_l': 0.8, 'foot_r': 0.25, 'foot_t': 0.05,
    'dock_r': 0.4, 'dock_l': 0.3, 'dock_off': 0.8,
    'sensor_r': 0.05, 'sensor_l': 0.2,
    'beam_r': 0.05, 'beam_l': 3.0,
    'overlap': 0.002
}

# Position the ship attached to the satellite's Orion (G_cap end)
ship_base_x = G_cap.Placement.Base.x + G_cap.Shape.BoundBox.XLength + gap

# Build ship parts with base offset
nose = Part.makeCone(0, P_ship['nose_base_d']/2, P_ship['nose_len'])
nose.translate(App.Vector(ship_base_x, 0, 0))
mid = Part.makeCylinder(P_ship['mid_d']/2, P_ship['mid_len'])
mid.translate(App.Vector(ship_base_x, 0, P_ship['nose_len']))
rear = Part.makeCone(P_ship['rear_d']/2, P_ship['mid_d']/2, P_ship['rear_len'])
rear.translate(App.Vector(ship_base_x, 0, P_ship['nose_len'] + P_ship['mid_len']))
hull = nose.fuse(mid).fuse(rear)

shield_R = P_ship['shield_d']/2.0
cer = Part.makeCylinder(shield_R, P_ship['t_ceramic'])
cone = Part.makeCone(shield_R, shield_R - 0.04, P_ship['shield_flecha'])
cone.translate(App.Vector(0, 0, -P_ship['shield_flecha']))
cer = cer.fuse(cone)
foam = Part.makeCylinder(shield_R - P_ship['overlap'], P_ship['t_foam'])
foam.translate(App.Vector(0, 0, P_ship['t_ceramic'] - P_ship['overlap']))
back = Part.makeCylinder(shield_R - 2*P_ship['overlap'], P_ship['t_cc'])
back.translate(App.Vector(0, 0, P_ship['t_ceramic'] + P_ship['t_foam'] - 2*P_ship['overlap']))
rimOD = shield_R; rimID = shield_R - P_ship['rim_w']
rim = Part.makeCylinder(rimOD, P_ship['rim_h']).cut(Part.makeCylinder(rimID, P_ship['rim_h']))
rim.translate(App.Vector(0, 0, P_ship['t_ceramic'] + P_ship['t_foam'] + P_ship['t_cc'] - P_ship['rim_h']))
shield = cer.fuse(foam).fuse(back).fuse(rim)
shield.translate(App.Vector(ship_base_x, 0, - (P_ship['t_ceramic'] + P_ship['t_foam'] + P_ship['t_cc'])))

hull_shield = Part.makeCylinder(P_ship['mid_d']/2 + P_ship['hull_shield_t'], P_ship['hull_shield_l'])
hull_shield.translate(App.Vector(ship_base_x, 0, P_ship['nose_len'] + (P_ship['mid_len'] - P_ship['hull_shield_l'])/2.0))

reactor_shield = Part.makeCylinder(P_ship['reactor_d']/2 + P_ship['reactor_shield_t'], P_ship['reactor_shield_l'])
reactor_shield.translate(App.Vector(ship_base_x, 0, P_ship['nose_len'] + P_ship['mid_len'] - 0.2))

reactor = Part.makeCylinder(P_ship['reactor_d']/2, P_ship['reactor_l'])
reactor.translate(App.Vector(ship_base_x, 0, P_ship['nose_len'] + 1.2))
nozzle = Part.makeCone(P_ship['rear_d']/2, P_ship['rear_d'], 1.0)
nozzle.translate(App.Vector(ship_base_x, 0, P_ship['nose_len'] + P_ship['mid_len'] + P_ship['rear_len']))
reactor_full = reactor.fuse(nozzle)

hab = Part.makeCylinder(P_ship['hab_d']/2, P_ship['hab_l'])
hab.translate(App.Vector(ship_base_x, 0, P_ship['nose_len'] + P_ship['mid_len'] + 0.5))

cockpit = Part.makeCylinder(P_ship['cockpit_d']/2, P_ship['cockpit_l'])
cockpit.translate(App.Vector(ship_base_x, 0, 0.05))
window = Part.makeSphere(P_ship['window_r'])
window.translate(App.Vector(ship_base_x + P_ship['cockpit_d']/3, 0, P_ship['cockpit_l']/2))
cockpit_cut = cockpit.cut(window)

tankL = Part.makeCylinder(P_ship['tank_r'], P_ship['tank_l'])
tankL.translate(App.Vector(ship_base_x + P_ship['tank_off'], 0, P_ship['nose_len'] + 1.0))
tankR = Part.makeCylinder(P_ship['tank_r'], P_ship['tank_l'])
tankR.translate(App.Vector(ship_base_x - P_ship['tank_off'], 0, P_ship['nose_len'] + 1.0))
sphereL = Part.makeSphere(P_ship['sphere_r'])
sphereL.translate(App.Vector(ship_base_x + P_ship['sphere_off'], 0, P_ship['nose_len'] + 2.5))
sphereR = Part.makeSphere(P_ship['sphere_r'])
sphereR.translate(App.Vector(ship_base_x - P_ship['sphere_off'], 0, P_ship['nose_len'] + 2.5))
tanks = tankL.fuse(tankR).fuse(sphereL).fuse(sphereR)

wingL = Part.makeBox(P_ship['wing_span'], P_ship['wing_th'], P_ship['wing_l'])
wingL.translate(App.Vector(ship_base_x - P_ship['wing_span']/2, -P_ship['mid_d']/2 - 0.15, P_ship['nose_len'] + P_ship['mid_len'] + P_ship['wing_back_offset']))
wingR = Part.makeBox(P_ship['wing_span'], P_ship['wing_th'], P_ship['wing_l'])
wingR.translate(App.Vector(ship_base_x - P_ship['wing_span']/2, P_ship['mid_d']/2 + 0.15, P_ship['nose_len'] + P_ship['mid_len'] + P_ship['wing_back_offset']))
wings = wingL.fuse(wingR)

collarOD = P_ship['mid_d'] + P_ship['collar_d_delta']
collar = Part.makeCylinder(collarOD/2.0, P_ship['collar_h']).cut(Part.makeCylinder((collarOD/2.0 - P_ship['collar_t']), P_ship['collar_h']))
collar.translate(App.Vector(ship_base_x, 0, P_ship['nose_len'] + P_ship['mid_len']/2.0 - P_ship['collar_h']/2.0))

defs = []
for i in range(P_ship['def_count']):
    ang = i * (360.0 / P_ship['def_count'])
    d = Part.makeBox(P_ship['def_l'], P_ship['def_w'], P_ship['def_t'])
    d.translate(App.Vector(ship_base_x - P_ship['def_l']/2.0, -P_ship['def_w']/2.0, P_ship['nose_len'] + P_ship['mid_len']/2.0 - P_ship['def_t']/2.0))
    baseR = collarOD/2.0 + P_ship['overlap']
    d.Placement = App.Placement(App.Vector(ship_base_x + baseR, 0, P_ship['nose_len'] + P_ship['mid_len']/2.0 - P_ship['def_t']/2.0), App.Rotation(App.Vector(0,0,1), ang))
    defs.append(d)
deflectores = defs[0]
for d in defs[1:]:
    deflectores = deflectores.fuse(d)

dockL = Part.makeCylinder(P_ship['dock_r'], P_ship['dock_l'])
dockL.translate(App.Vector(ship_base_x + P_ship['dock_off'], 0, P_ship['nose_len'] + 1.8))
dockR = Part.makeCylinder(P_ship['dock_r'], P_ship['dock_l'])
dockR.translate(App.Vector(ship_base_x - P_ship['dock_off'], 0, P_ship['nose_len'] + 1.8))
docking = dockL.fuse(dockR)

sensor1 = Part.makeSphere(P_ship['sensor_r'])
sensor1.translate(App.Vector(ship_base_x + P_ship['mid_d']/2 + 0.1, 0, P_ship['nose_len'] + 2.0))
sensor2 = Part.makeSphere(P_ship['sensor_r'])
sensor2.translate(App.Vector(ship_base_x - P_ship['mid_d']/2 - 0.1, 0, P_ship['nose_len'] + 2.0))
sensors = sensor1.fuse(sensor2)

beam1 = Part.makeCylinder(P_ship['beam_r'], P_ship['beam_l'])
beam1.translate(App.Vector(ship_base_x, 0, P_ship['nose_len']))
beam2 = Part.makeCylinder(P_ship['beam_r'], P_ship['beam_l'])
beam2.translate(App.Vector(ship_base_x, 0, P_ship['nose_len'] + P_ship['mid_len']))
beams = beam1.fuse(beam2)

mast = Part.makeCylinder(P_ship['mast_r'], P_ship['mast_l'])
mast.translate(App.Vector(ship_base_x + P_ship['mid_d']/2 + 0.1, 0, P_ship['nose_len'] + P_ship['mid_len']))
dish_flat = Part.makeCone(P_ship['dish_r'], P_ship['dish_r'] - 0.2, 0.18)
dish_flat.translate(App.Vector(ship_base_x + P_ship['mid_d']/2 + 0.1, 0, P_ship['nose_len'] + P_ship['mid_len'] + P_ship['mast_l']))
antenna = mast.fuse(dish_flat)

legs = []
for angle in [0,90,180,270]:
    leg = Part.makeCylinder(P_ship['leg_r'], P_ship['leg_l'])
    leg.translate(App.Vector(ship_base_x + P_ship['mid_d']/2*math.cos(math.radians(angle)),
                             P_ship['mid_d']/2*math.sin(math.radians(angle)), 0))
    foot = Part.makeCylinder(P_ship['foot_r'], P_ship['foot_t'])
    foot.translate(App.Vector(ship_base_x + P_ship['mid_d']/2*math.cos(math.radians(angle)),
                              P_ship['mid_d']/2*math.sin(math.radians(angle)), -P_ship['foot_t']))
    legs.append(leg.fuse(foot))
landing_full = legs[0].fuse(legs[1]).fuse(legs[2]).fuse(legs[3])

# Fuse all ship parts into one object
nave = hull
for part in [shield, hull_shield, reactor_shield, cockpit_cut, reactor_full, hab, tanks,
             wings, collar, deflectores, docking, sensors, beams, antenna, landing_full]:
    try:
        nave = nave.fuse(part)
    except Exception:
        part.translate(App.Vector(0,0,0.002))
        nave = nave.fuse(part)

nave_obj = doc.addObject("Part::Feature", "Ship_DFD_XL")
nave_obj.Shape = nave
doc.recompute()

# Now, compute masses and export

def obj_mass(obj):
    try:
        vol = obj.Shape.Volume
        rho = getattr(obj, "Density", 0.0)
        return vol, vol * rho
    except Exception:
        return 0.0, 0.0

total_vol = 0.0
total_mass = 0.0
for o in doc.Objects:
    if hasattr(o, "Shape") and not o.isDerivedFrom("App::DocumentObjectGroup"):
        v, m = obj_mass(o)
        total_vol += v
        total_mass += m

print("=== Unified Assembly Report ===")
print(f"Total Volume: {total_vol:0.3f} m^3")
print(f"Total Mass: {total_mass:0.1f} kg")

# Export STEP

try:
    import ImportGui as IG
    export_mod = "ImportGui"
except Exception:
    try:
        import Import as IG
        export_mod = "Import"
    except Exception:
        IG = None
        export_mod = None

App.ActiveDocument.recompute()

objs_to_export = [o for o in doc.Objects if hasattr(o, "Shape") and not o.isDerivedFrom("App::DocumentObjectGroup")]

out_dir = App.getUserAppDataDir()
step_path = out_dir + "unified_satellite_ship.step"
if IG:
    IG.export(objs_to_export, step_path)
    print(f"STEP exported: {step_path}")
else:
    print("STEP export not available.")

print("Unified model completed: Satellite with attached DFD XL ship!")