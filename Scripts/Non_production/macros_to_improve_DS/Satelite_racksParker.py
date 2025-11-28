Satelite_racksParker.py
import FreeCAD as App, FreeCADGui as Gui
import Part, math

doc = App.newDocument("Satellite_Parker_Racks_Cooling")

# -------------------------
# Configuración paramétrica
# -------------------------
cfg = {
    "bus": {"L": 2.6, "W": 1.6, "H": 1.6, "wall": 0.010, "frame_bar": 0.040, "deck_thk": 0.008, "deck_count": 6,
            "panel_cutouts": True, "cut_w": 0.45, "cut_h": 0.25, "cut_gap": 0.08},
    "racks": {"gap": 0.020, "guide_w": 0.012, "guide_t": 0.010, "rows": 2, "slots": 8, "slot_gap": 0.006,
              "backplane_t": 0.012, "conn_r": 0.010, "dowel_r": 0.006},
    "slots_layout": [
        ["PROP","PROP","EPS","OBC","ADCS","RF","PAYLOAD","PAYLOAD"],
        ["PROP","PROP","EPS","OBC","ADCS","RF","PAYLOAD","PAYLOAD"]
    ],
    "eps": {"bat_w": 0.35, "bat_d": 0.18, "bat_h": 0.16, "box_w": 0.42, "box_d": 0.28, "box_h": 0.10},
    "obc": {"pcbs": 6, "pcb_thk": 0.003, "pcb_gap": 0.010, "standoff_r": 0.004},
    "adcs": {"rw_r": 0.08, "rw_h": 0.05, "mag_r": 0.012, "mag_L": 0.50, "sun_sensors": 6},
    "rf": {"patch_w": 0.30, "patch_h": 0.30, "patch_t": 0.008, "trx_w": 0.35, "trx_d": 0.25, "trx_h": 0.10,
           "monopole_r": 0.005, "monopole_L": 1.2, "coax_r": 0.006, "hga_d": 0.9, "hga_depth": 0.20, "gimbal_r": 0.06},
    "prop": {"tanks": 4, "tank_r": 0.11, "tank_L": 0.70, "line_r": 0.010, "manifold_r": 0.040, "manifold_h": 0.12,
             "check_valve_r": 0.016, "thrusters": 12, "thr_r1": 0.028, "thr_r2": 0.010, "thr_h": 0.070,
             "service_panel": True, "qd": 4},
    "payload": {"optic": True, "optic_d": 0.35, "optic_L": 0.30, "bench_w": 0.70, "bench_d": 0.60, "bench_h": 0.06},
    "thermal": {
        "radiators": [
            {"w": 0.9, "h": 1.2, "t": 0.010, "face": "Y+"},
            {"w": 0.9, "h": 1.2, "t": 0.010, "face": "Y-"}
        ],
        "heatpipes": {"r": 0.008, "runs": 6},
        "coldplates": [
            {"w": 0.45, "d": 0.28, "t": 0.012, "slot": ("EPS", 2)},
            {"w": 0.40, "d": 0.25, "t": 0.012, "slot": ("OBC", 3)},
            {"w": 0.50, "d": 0.30, "t": 0.012, "slot": ("RF", 5)}
        ],
        "straps": {"w": 0.020, "t": 0.004, "runs": 4},
        "show_MLI": True
    },
    "arms": {
        "count": 2,
        "bases": [
            {"pos": (0.35, 0.35, 1.45), "yaw": 35, "sh": 12, "el": 28, "wr": -12, "L": (0.8,0.7,0.4), "R": (0.05,0.045,0.035)},
            {"pos": (0.35, 1.25, 1.45), "yaw": 145, "sh": 16, "el": 22, "wr":  10, "L": (0.8,0.7,0.4), "R": (0.05,0.045,0.035)}
        ],
        "gripper": {"jaw_L": 0.18, "jaw_w": 0.06, "jaw_t": 0.02},
        "camera":  {"r": 0.05, "L": 0.10}
    },
    "solar": {"wings": 4, "panel_thk": 0.006, "segment_L": [1.2, 1.0, 0.8], "segment_W": 0.9, "hinge_r": 0.030,
              "sada_r": 0.10, "sada_h": 0.18},
    "parker_shield": {"outer_r": 0.9, "inner_r": 0.25, "thk": 0.05, "cone_h": 0.25, "offset": 0.6,
                      "standoffs": 8, "standoff_L": 0.5, "standoff_r": 0.02, "layers": 3, "layer_gap": 0.012},
    "modularity": {"ring": True, "ring_w": 0.06, "ring_t": 0.02, "lugs": True, "lug_r": 0.028},
    "shielding": {"whipple": True, "patch_t": 0.008, "patch_w": 0.40, "patch_h": 0.55},
    "harness": {"trays": 3, "tray_w": 0.05, "tray_h": 0.03, "bundle_r": 0.015}
}

# -------------------------
# Utilidades
# -------------------------
def add(shape, name, color=(0.8,0.8,0.8), alpha=0.0, parent=None):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    o.ViewObject.ShapeColor = color
    o.ViewObject.Transparency = int(alpha*100)
    if parent: parent.addObject(o)
    return o

def grp(name): return doc.addObject("App::Part", name)
def box(w,d,h, p=(0,0,0)): return Part.makeBox(w,d,h, App.Vector(*p))
def cyl(r,h, p=(0,0,0), d=(0,0,1)): return Part.makeCylinder(r,h, App.Vector(*p), App.Vector(*d))
def cone(r1,r2,h, p=(0,0,0), d=(0,0,1)): return Part.makeCone(r1,r2,h, App.Vector(*p), App.Vector(*d))
def sph(r, c=(0,0,0)): return Part.makeSphere(r, App.Vector(*c))
def tube_between(p1, p2, r):
    v = App.Vector(*p2) - App.Vector(*p1)
    h = v.Length
    if h < 1e-6: return None
    return cyl(r, h, p1, (v.x, v.y, v.z))
def dir_from_angles(yaw_deg, pitch_deg):
    y = math.radians(yaw_deg); p = math.radians(pitch_deg)
    return (math.cos(p)*math.cos(y), math.cos(p)*math.sin(y), math.sin(p))

# -------------------------
# Grupos
# -------------------------
g_bus=grp("Bus"); g_racks=grp("Racks"); g_mods=grp("Modulos")
g_eps=grp("EPS"); g_obc=grp("OBC"); g_adcs=grp("ADCS"); g_rf=grp("RF"); g_prop=grp("Propulsion")
g_pl=grp("Payload"); g_therm=grp("Termico"); g_arms=grp("Brazos"); g_solar=grp("Solares")
g_shield=grp("ParkerShield"); g_mod=grp("Modularidad"); g_shld=grp("Blindaje"); g_harn=grp("Arnes"); g_ext=grp("Exterior")

# -------------------------
# 1) Bus estructural
# -------------------------
B = cfg["bus"]; L,W,H,t = B["L"],B["W"],B["H"],B["wall"]
outer = box(L,W,H,(0,0,0)); inner = box(L-2*t,W-2*t,H-2*t,(t,t,t)); shell = outer.cut(inner)
if B["panel_cutouts"]:
    cw,ch,cg = B["cut_w"],B["cut_h"],B["cut_gap"]
    for side in [0,1]:
        y0 = -0.0002 if side==0 else W - t + 0.0002
        for k in range(3):
            z0 = t + cg + k*(ch+cg)
            shell = shell.cut(box(cw, t+0.0004, ch, (L/2 - cw/2, y0, z0)))
add(shell, "Carcasa", (0.75,0.75,0.78), 0.0, g_bus)

fb = B["frame_bar"]
for (x,y) in [(t,t),(L-t-fb,t),(t,W-t-fb),(L-t-fb,W-t-fb),(L/2-fb/2,t),(L/2-fb/2,W-t-fb)]:
    add(box(fb,fb,H-2*t,(x,y,t)), f"Frame_{x:.2f}_{y:.2f}", (0.50,0.50,0.55), 0.0, g_bus)

for k in range(B["deck_count"]):
    z = t + (H-2*t - B["deck_thk"]) * (k+1)/(B["deck_count"]+1)
    add(box(L-2*t, W-2*t, B["deck_thk"], (t,t,z)), f"Deck_{k+1}", (0.70,0.70,0.75), 0.0, g_bus)

# -------------------------
# 2) Racks y backplanes
# -------------------------
R = cfg["racks"]
rack_w = (L - 2*t)
rack_d = (W - 3*R["gap"])/2
rack_h = (H - 2*t)
def rack_bbox(r_index):
    y0 = t + R["gap"] + r_index*(rack_d + R["gap"])
    return (t, y0, t), (rack_w, rack_d, rack_h)

for r_i in range(R["rows"]):
    (rx,ry,rz),(rw,rd,rh) = rack_bbox(r_i)
    add(box(rw, rd, rh, (rx,ry,rz)), f"Rack_{r_i+1}", (0.60,0.60,0.65), 0.0, g_racks)
    gw,gt = R["guide_w"], R["guide_t"]
    for (x,y) in [(rx,ry),(rx+rw-gw,ry),(rx,ry+rd-gw),(rx+rw-gw,ry+rd-gw)]:
        add(box(gw,gt,rh,(x,y,rz)), f"GuideA_R{r_i+1}_{x:.2f}", (0.55,0.55,0.58), 0.0, g_racks)
        add(box(gt,gw,rh,(x,y,rz)), f"GuideB_R{r_i+1}_{y:.2f}", (0.55,0.55,0.58), 0.0, g_racks)
    back = box(rw, R["backplane_t"], rh, (rx, ry + rd - R["backplane_t"], rz))
    add(back, f"Backplane_R{r_i+1}", (0.45,0.50,0.55), 0.0, g_racks)
    slot_h = (rh - (R["slots"]+1)*R["slot_gap"]) / R["slots"]
    for s in range(R["slots"]):
        zc = rz + R["slot_gap"]*(s+1) + slot_h*s + slot_h/2
        add(cyl(R["conn_r"], 0.030, (L/2, ry + rd, zc), (0,-1,0)), f"BP_Conn_R{r_i+1}_S{s+1}", (0.9,0.9,0.9), 0.0, g_racks)
        add(cyl(R["dowel_r"], 0.020, (L/2 - 0.12, ry + rd, zc), (0,-1,0)), f"BP_Dowel_R{r_i+1}_S{s+1}", (0.8,0.8,0.8), 0.0, g_racks)
        add(box(rw, rd, 0.006, (rx, ry, rz + R["slot_gap"]*(s+1) + slot_h*s)), f"SlotTray_R{r_i+1}_S{s+1}", (0.62,0.62,0.65), 0.0, g_racks)

def get_slot_bbox(r_index, s_index):
    (rx,ry,rz),(rw,rd,rh) = rack_bbox(r_index)
    slot_h = (rh - (R["slots"]+1)*R["slot_gap"]) / R["slots"]
    z = rz + R["slot_gap"]*(s_index+1) + slot_h*s_index
    return (rx, ry, z), (rw, rd, slot_h)

# -------------------------
# 3) Módulos de subsistemas
# -------------------------
def build_EPS(r_i, s_i):
    (x0,y0,z0),(w,d,h) = get_slot_bbox(r_i, s_i)
    e = cfg["eps"]
    eps = box(e["box_w"], e["box_d"], e["box_h"], (x0 + (w-e["box_w"])/2, y0 + (d-e["box_d"])/2, z0 + 0.010))
    add(eps, f"EPS_Box_R{r_i+1}_S{s_i+1}", (0.25,0.30,0.35), 0.0, g_eps)
    bat = box(e["bat_w"], e["bat_d"], e["bat_h"], (x0 + (w-e["bat_w"])/2, y0 + (d-e["bat_d"])/2, z0 + 0.010 + e["box_h"] + 0.010))
    add(bat, f"EPS_Bat_R{r_i+1}_S{s_i+1}", (0.20,0.20,0.20), 0.0, g_eps)
    add(cyl(0.010, 0.035, (L/2, y0 + d, z0 + h/2), (0,-1,0)), f"EPS_BPConn_R{r_i+1}_S{s_i+1}", (0.9,0.9,0.9), 0.0, g_eps)

def build_OBC(r_i, s_i):
    (x0,y0,z0),(w,d,h) = get_slot_bbox(r_i, s_i)
    o = cfg["obc"]; pcb_w=w-0.06; pcb_d=d-0.06; z=z0+0.012
    for k in range(o["pcbs"]):
        add(box(pcb_w, pcb_d, o["pcb_thk"], (x0+(w-pcb_w)/2, y0+(d-pcb_d)/2, z)), f"OBC_PCB_R{r_i+1}_S{s_i+1}_{k+1}", (0.05,0.45,0.25), 0.0, g_obc)
        z += o["pcb_thk"] + o["pcb_gap"]
    st_h = o["pcbs"]*(o["pcb_thk"]+o["pcb_gap"])
    for (dx,dy) in [(x0+0.02,y0+0.02),(x0+w-0.02,y0+0.02),(x0+0.02,y0+d-0.02),(x0+w-0.02,y0+d-0.02)]:
        add(cyl(o["standoff_r"], st_h, (dx, dy, z0+0.012), (0,0,1)), f"OBC_Standoff_R{r_i+1}_S{s_i+1}_{dx:.2f}", (0.7,0.7,0.7), 0.0, g_obc)

def build_ADCS(r_i, s_i):
    (x0,y0,z0),(w,d,h) = get_slot_bbox(r_i, s_i)
    a = cfg["adcs"]
    add(cyl(a["rw_r"], a["rw_h"], (x0+w/2 - a["rw_r"], y0+d/2, z0+0.020), (1,0,0)), f"ADCS_RW_X_R{r_i+1}_S{s_i+1}", (0.3,0.3,0.35), 0.0, g_adcs)
    add(cyl(a["rw_r"], a["rw_h"], (x0+w/2, y0+d/2 - a["rw_r"], z0+0.020), (0,1,0)), f"ADCS_RW_Y_R{r_i+1}_S{s_i+1}", (0.3,0.3,0.35), 0.0, g_adcs)
    add(cyl(a["rw_r"], a["rw_h"], (x0+w/2, y0+d/2, z0+0.020), (0,0,1)), f"ADCS_RW_Z_R{r_i+1}_S{s_i+1}", (0.3,0.3,0.35), 0.0, g_adcs)
    add(cyl(a["mag_r"], a["mag_L"], (x0+w/2, y0+0.02, z0+0.015), (0,0,1)), f"ADCS_MTQ_R{r_i+1}_S{s_i+1}", (0.1,0.4,0.6), 0.0, g_adcs)

def build_RF(r_i, s_i):
    (x0,y0,z0),(w,d,h) = get_slot_bbox(r_i, s_i)
    r = cfg["rf"]
    trx = box(r["trx_w"], r["trx_d"], r["trx_h"], (x0+(w-r["trx_w"])/2, y0+(d-r["trx_d"])/2, z0+0.012))
    add(trx, f"RF_TRX_R{r_i+1}_S{s_i+1}", (0.35,0.35,0.40), 0.0, g_rf)
    add(tube_between((x0+w/2, y0, z0+r["trx_h"]+0.04), (L/2, -r["patch_t"], z0 + h/2), r["coax_r"]), f"RF_Coax_R{r_i+1}_S{s_i+1}", (0.2,0.2,0.2), 0.0, g_rf)
    add(box(r["patch_w"], r["patch_t"], r["patch_h"], (L/2 - r["patch_w"]/2, -r["patch_t"], z0 + h/2 - r["patch_h"]/2)), f"RF_Patch_R{r_i+1}_S{s_i+1}", (0.95,0.85,0.25), 0.0, g_rf)

def build_PROP(r_i, s_i):
    (x0,y0,z0),(w,d,h) = get_slot_bbox(r_i, s_i)
    p = cfg["prop"]; offs=0.05; zc = z0 + 0.015
    tpos = [
        (x0+offs+p["tank_r"], y0+offs+p["tank_r"]),
        (x0+w-offs-p["tank_r"], y0+offs+p["tank_r"]),
        (x0+offs+p["tank_r"], y0+d-offs-p["tank_r"]),
        (x0+w-offs-p["tank_r"], y0+d-offs-p["tank_r"])
    ][:p["tanks"]]
    tops=[]
    for n,(tx,ty) in enumerate(tpos):
        add(cyl(p["tank_r"], p["tank_L"], (tx,ty,zc), (0,0,1)), f"PROP_Tank_R{r_i+1}_S{s_i+1}_{n+1}", (0.90,0.90,0.95), 0.0, g_prop)
        add(box(0.018,0.045,0.018,(tx-0.009,ty-0.0225,zc + p["tank_L"]/2 - 0.009)), f"PROP_TankBrkt_R{r_i+1}_S{s_i+1}_{n+1}", (0.6,0.6,0.6), 0.0, g_prop)
        tops.append((tx,ty,zc+p["tank_L"]))
    man = cyl(p["manifold_r"], p["manifold_h"], (x0+w/2, y0+d/2, z0 + h - p["manifold_h"] - 0.02), (0,0,1))
    add(man, f"PROP_Manifold_R{r_i+1}_S{s_i+1}", (0.6,0.6,0.65), 0.0, g_prop)
    for k,tp in enumerate(tops):
        ln = tube_between(tp, (x0+w/2, y0+d/2, z0 + h - 0.02), p["line_r"])
        if ln: add(ln, f"PROP_Line_R{r_i+1}_S{s_i+1}_{k+1}", (0.85,0.75,0.25), 0.0, g_prop)
        add(cyl(p["check_valve_r"], 0.05, ((tp[0]+x0+w/2)/2, (tp[1]+y0+d/2)/2, tp[2]+0.03), (0,0,1)), f"PROP_Check_R{r_i+1}_S{s_i+1}_{k+1}", (0.75,0.75,0.78), 0.0, g_prop)

def build_PAYLOAD(r_i, s_i):
    (x0,y0,z0),(w,d,h) = get_slot_bbox(r_i, s_i)
    P = cfg["payload"]
    bench = box(P["bench_w"], P["bench_d"], P["bench_h"], (x0+(w-P["bench_w"])/2, y0+(d-P["bench_d"])/2, z0+0.012))
    add(bench, f"PL_Bench_R{r_i+1}_S{s_i+1}", (0.6,0.8,0.9), 0.3, g_pl)

builders = {"EPS":build_EPS,"OBC":build_OBC,"ADCS":build_ADCS,"RF":build_RF,"PROP":build_PROP,"PAYLOAD":build_PAYLOAD}
for r_i in range(cfg["racks"]["rows"]):
    for s_i,typ in enumerate(cfg["slots_layout"][r_i]):
        if typ in builders: builders[typ](r_i, s_i)

# Óptica (frontal +X)
if cfg["payload"]["optic"]:
    add(cyl(cfg["payload"]["optic_d"]/2, cfg["payload"]["optic_L"], (L - t - cfg["payload"]["optic_L"], W/2, H/2 - cfg["payload"]["optic_d"]/4), (1,0,0)), "PL_Optic", (0.7,0.8,0.95), 0.0, g_pl)

# -------------------------
# 4) Brazos robóticos (simplificados robustos) puede quitarse
# -------------------------
A = cfg["arms"]
def build_arm(base, name):
    (bx,by,bz) = base["pos"]
    yaw, sh, el, wr = base["yaw"], base["sh"], base["el"], base["wr"]
    L1,L2,L3 = base["L"]; R1,R2,R3 = base["R"]
    ped = cyl(R1*1.2, 0.12, (bx, by, bz-0.12), (0,0,1)); add(ped, f"{name}_Base", (0.55,0.55,0.58), 0.0, g_arms)
    def d(a,b): return dir_from_angles(a,b)
    d1=d(yaw,sh); p1=(bx + d1[0]*L1, by + d1[1]*L1, bz + d1[2]*L1)
    add(cyl(R1, L1, (bx,by,bz), d1), f"{name}_S1", (0.8,0.8,0.85), 0.0, g_arms)
    d2=d(yaw,sh+el); p2=(p1[0]+d2[0]*L2, p1[1]+d2[1]*L2, p1[2]+d2[2]*L2)
    add(cyl(R2, L2, p1, d2), f"{name}_S2", (0.8,0.8,0.85), 0.0, g_arms)
    d3=d(yaw,sh+el+wr); p3=(p2[0]+d3[0]*L3, p2[1]+d3[1]*L3, p2[2]+d3[2]*L3)
    add(cyl(R3, L3, p2, d3), f"{name}_S3", (0.8,0.8,0.85), 0.0, g_arms)
    # Pinza simple
    jaw_L, jaw_w, jaw_t = A["gripper"]["jaw_L"], A["gripper"]["jaw_w"], A["gripper"]["jaw_t"]
    lat = (-d3[1], d3[0], 0.0); n = math.sqrt(lat[0]**2 + lat[1]**2) or 1.0; lat=(lat[0]/n,lat[1]/n,lat[2]/n)
    j1=(p3[0]+lat[0]*jaw_w/2, p3[1]+lat[1]*jaw_w/2, p3[2]); j2=(p3[0]-lat[0]*jaw_w/2, p3[1]-lat[1]*jaw_w/2, p3[2])
    add(box(jaw_t,jaw_w,jaw_L,(j1[0],j1[1]-jaw_w/2,j1[2])), f"{name}_Jaw1", (0.85,0.75,0.55), 0.0, g_arms)
    add(box(jaw_t,jaw_w,jaw_L,(j2[0]-jaw_t,j2[1]-jaw_w/2,j2[2])), f"{name}_Jaw2", (0.85,0.75,0.55), 0.0, g_arms)
for idx, base in enumerate(A["bases"][:A["count"]]): build_arm(base, f"Arm_{idx+1}")

# -------------------------
# 5) Paneles solares articulados (2 lados)
# -------------------------
S = cfg["solar"]
def build_wing(side, idx):
    y = -S["panel_thk"] if side=="Y-" else W
    sada = cyl(S["sada_r"], S["sada_h"], (0, y, H/2 - S["sada_h"]/2), (1,0,0)); add(sada, f"SADA_{side}_{idx}", (0.2,0.2,0.2), 0.0, g_solar)
    x0 = 0.0 if side=="Y-" else L - S["segment_L"][0]; segW = S["segment_W"]; thk = S["panel_thk"]
    seg0 = box(S["segment_L"][0], thk, segW, (x0, y, H/2 - segW/2)); add(seg0, f"Panel_{side}_{idx}_Root", (0.1,0.2,0.8), 0.0, g_solar)
    add(cyl(S["hinge_r"], segW, (x0, y, H/2 - segW/2), (0,1,0)), f"Hinge_{side}_{idx}_0", (0.2,0.2,0.2), 0.0, g_solar)
    x1 = x0 + (S["segment_L"][0] if side=="Y-" else -S["segment_L"][1])
    seg1 = box(S["segment_L"][1], thk, segW, (x1, y, H/2 - segW/2)); add(seg1, f"Panel_{side}_{idx}_Mid", (0.1,0.2,0.8), 0.0, g_solar)
    add(cyl(S["hinge_r"], segW, (x1, y, H/2 - segW/2), (0,1,0)), f"Hinge_{side}_{idx}_1", (0.2,0.2,0.2), 0.0, g_solar)
    x2 = x1 + (S["segment_L"][1] if side=="Y-" else -S["segment_L"][2])
    seg2 = box(S["segment_L"][2], thk, segW, (x2, y, H/2 - segW/2)); add(seg2, f"Panel_{side}_{idx}_Tip", (0.1,0.2,0.8), 0.0, g_solar)
    add(cyl(S["hinge_r"], segW, (x2, y, H/2 - segW/2), (0,1,0)), f"Hinge_{side}_{idx}_2", (0.2,0.2,0.2), 0.0, g_solar)
for i in range(S["wings"]//2): build_wing("Y-", i+1); build_wing("Y+", i+1)

# -------------------------
# 6) Escudo térmico tipo Parker (multicapa) y MLI trasero
# -------------------------
PS = cfg["parker_shield"]; x_face=L
for k in range(PS["layers"]):
    r_out = PS["outer_r"] - k*PS["layer_gap"]; r_in = max(PS["inner_r"] - k*PS["layer_gap"]*0.5, 0.06)
    frustum = cone(r_out, r_in, PS["cone_h"], (x_face + PS["offset"], W/2, H/2), (1,0,0))
    add(frustum, f"TPS_Layer_{k+1}", (0.90,0.90,0.95) if k==0 else (0.85,0.85,0.9), 0.0, g_shield)
for i in range(PS["standoffs"]):
    ang = 2*math.pi*i/PS["standoffs"]
    yb = W/2 + (W/2 - 0.15)*math.cos(ang); zb = H/2 + (H/2 - 0.15)*math.sin(ang)
    base_pt = (x_face, yb, zb); tip_pt  = (x_face + PS["offset"], W/2 + PS["outer_r"]*math.cos(ang), H/2 + PS["outer_r"]*math.sin(ang))
    add(tube_between(base_pt, tip_pt, PS["standoff_r"]), f"TPS_Standoff_{i+1}", (0.6,0.6,0.65), 0.0, g_shield)
if cfg["thermal"]["show_MLI"]:
    mli = box(0.012, 1.05*W, 1.05*H, (x_face + PS["offset"] - 0.012, -0.025, -0.025)); add(mli, "TPS_MLI_Back", (1.0,1.0,0.6), 0.85, g_shield)

# -------------------------
# 7) Propulsión externa: thrusters + panel servicio con sensores
# -------------------------
Pp = cfg["prop"]; base_ring_z = t + 0.10
for i in range(Pp["thrusters"]):
    ang = 2*math.pi*i/Pp["thrusters"]
    x = L*0.20 + (L-0.40)*((i%3)/2.0)
    y = W/2 + (W/2 - 0.10)*math.cos(ang)
    z = base_ring_z + (H*0.05)*math.sin(ang*2)
    dirv = (0.2, (y - W/2)*0.02, -0.6)
    add(cone(Pp["thr_r1"], Pp["thr_r2"], Pp["thr_h"], (x,y,z), dirv), f"Thruster_{i+1}", (0.85,0.85,0.90), 0.0, g_prop)
    ln = tube_between((L/2, W/2, H/2), (x, y, z + Pp["thr_h"]*dirv[2]), Pp["line_r"])
    if ln: add(ln, f"FuelLine_Thr_{i+1}", (0.85,0.75,0.25), 0.0, g_prop)

if Pp["service_panel"]:
    sp_w, sp_h, sp_t = 0.40, 0.60, 0.012
    sp_x, sp_y, sp_z = L - sp_w - t*0.5, W, H/2 - sp_h/2
    service_panel = box(sp_w, sp_t, sp_h, (sp_x, sp_y, sp_z)); add(service_panel, "ServicePanel", (0.55,0.55,0.6), 0.0, g_prop)
    for k in range(Pp["qd"]):
        qd_r, qd_L = 0.012, 0.020
        qd_x, qd_y = sp_x + sp_w/2, sp_y + sp_t
        qd_z = sp_z + (sp_h/(Pp["qd"]+1))*(k+1)
        add(cyl(qd_r, qd_L, (qd_x, qd_y, qd_z), (1,0,0)), f"QD_{k+1}", (0.9,0.9,0.9), 0.0, g_prop)
        add(cyl(0.006, 0.015, (qd_x + 0.025, qd_y, qd_z + 0.005), (1,0,0)), f"PressureSensor_{k+1}", (0.8,0.2,0.2), 0.0, g_prop)
        add(cyl(0.005, 0.015, (qd_x - 0.025, qd_y, qd_z - 0.005), (1,0,0)), f"TempSensor_{k+1}", (0.2,0.2,0.8), 0.0, g_prop)
    add(cone(0.010, 0.002, 0.025, (sp_x + sp_w/2, sp_y + sp_t, sp_z + sp_h - 0.025), (1,0,0)), "ReliefValve", (0.8,0.8,0.85), 0.0, g_prop)

# -------------------------
# 8) Refrigeración funcional: radiadores, heatpipes, cold plates, straps
# -------------------------
TH = cfg["thermal"]
# Radiadores en caras Y±
for rad in TH["radiators"]:
    w,hx,tg,face = rad["w"], rad["h"], rad["t"], rad["face"]
    y = W if face=="Y+" else -tg
    add(box(w, tg, hx, (L/2 - w/2, y, H/2 - hx/2)), f"Radiator_{face}", (0.85,0.85,0.9), 0.0, g_therm)
# Cold plates en módulos
name_to_slot = {}
for r_i in range(cfg["racks"]["rows"]):
    for s_i,typ in enumerate(cfg["slots_layout"][r_i]):
        name_to_slot.setdefault(typ, (r_i, s_i))
for cp in TH["coldplates"]:
    typ, sidx = cp["slot"]
    # busca la primera coincidencia del tipo y aplica offset sidx relativo
    # simple: usa el índice declarado en layout
    for r_i in range(cfg["racks"]["rows"]):
        layout = cfg["slots_layout"][r_i]
        if sidx < len(layout) and layout[sidx] == typ:
            (x0,y0,z0),(w,d,h) = get_slot_bbox(r_i, sidx)
            plate = box(cp["w"], cp["d"], cp["t"], (x0 + (w-cp["w"])/2, y0 + (d-cp["d"])/2, z0 + 0.008))
            add(plate, f"ColdPlate_{typ}_R{r_i+1}_S{sidx+1}", (0.7,0.75,0.8), 0.0, g_therm)
            break
# Heatpipes (verticales hacia radiadores Y+)
hp_r, hp_runs = TH["heatpipes"]["r"], TH["heatpipes"]["runs"]
for i in range(hp_runs):
    x = t + 0.20 + i*((L-0.40)/max(hp_runs-1,1))
    add(cyl(hp_r, H-2*t, (x, W-0.02, t), (0,0,1)), f"HeatPipe_{i+1}", (0.75,0.75,0.80), 0.0, g_therm)
# Thermal straps desde EPS y OBC a radiador Y+
strap_w, strap_t, strap_runs = TH["straps"]["w"], TH["straps"]["t"], TH["straps"]["runs"]
for i in range(strap_runs):
    z = t + 0.20 + i*((H-0.40)/max(strap_runs-1,1))
    add(box(strap_w, strap_t, 0.60, (L - t - strap_w, W - t - strap_t, z - 0.30)), f"Strap_{i+1}", (0.85,0.75,0.55), 0.0, g_therm)

# -------------------------
# 9) Parker shield (multicapa) ya creado y blindajes Whipple adicionales
# -------------------------
SH = cfg["shielding"]
if SH["whipple"]:
    # Parche en cara inferior (impactos orbitales)
    add(box(SH["patch_w"], SH["patch_h"], SH["patch_t"], (L/2 - SH["patch_w"]/2, W/2 - SH["patch_h"]/2, -SH["patch_t"])), "Whipple_Bottom", (0.8,0.8,0.85), 0.0, g_shld)
    # Parches laterales cercanos a panel de servicio
    add(box(SH["patch_w"]*0.7, SH["patch_t"], SH["patch_h"]*0.7, (L/2 - SH["patch_w"]*0.35, W + SH["patch_t"], H/2 - (SH["patch_h"]*0.7)/2)), "Whipple_Service", (0.8,0.8,0.85), 0.0, g_shld)

# -------------------------
# 10) Modularidad (anillo acople + orejetas)
# -------------------------
MD = cfg["modularity"]
if MD["ring"]:
    ringR = min(W,H)/2 - t*2
    ring = cyl(ringR, MD["ring_t"], (L - t - MD["ring_t"], W/2 - ringR, H/2), (0,1,0)).cut(
           cyl(ringR - MD["ring_w"], MD["ring_t"]+0.0001, (L - t - MD["ring_t"], W/2 - (ringR - MD["ring_w"]), H/2), (0,1,0)))
    add(ring, "DockingRing", (0.65,0.65,0.65), 0.0, g_mod)
if MD["lugs"]:
    for (x,y) in [(t*2,t*2),(L-t*2,t*2),(t*2,W-t*2),(L-t*2,W-t*2)]:
        add(cyl(MD["lug_r"], 0.04, (x, y, H - t - 0.04), (0,0,1)), "GrappleLug", (0.6,0.6,0.65), 0.0, g_mod)

# -------------------------
# 11) Arnés principal (bandejas + troncales)
# -------------------------
HA = cfg["harness"]
for i in range(HA["trays"]):
    z = t + (H-2*t) * (i+1)/(HA["trays"]+1)
    add(box(HA["tray_w"], HA["tray_h"], L-2*t, (L - t - HA["tray_w"], t, z - (L-2*t)/2)), f"HarnessTray_{i+1}", (0.6,0.55,0.45), 0.0, g_harn)
# Troncal EPS->OBC->RF
def slot_center(typ):
    for r_i in range(cfg["racks"]["rows"]):
        for s_i,tname in enumerate(cfg["slots_layout"][r_i]):
            if tname==typ:
                (x0,y0,z0),(w,d,h)=get_slot_bbox(r_i,s_i)
                return (x0+w/2, y0+d/2, z0+h/2)
    return (L/2,W/2,H/2)
bund_r = HA["bundle_r"]
p_eps, p_obc, p_rf = slot_center("EPS"), slot_center("OBC"), slot_center("RF")
add(tube_between(p_eps, p_obc, bund_r), "Harness_EPS_OBC", (0.3,0.25,0.2), 0.0, g_harn)
add(tube_between(p_obc, p_rf, bund_r), "Harness_OBC_RF", (0.3,0.25,0.2), 0.0, g_harn)

# ...existing code...
# --- funciones añadidas: capas de blindaje solar/alta temperatura (geométricas y físicas)
def create_sun_shield_layers(origin, radius, stack, gap=0.001, normal=(1,0,0), parent=None):
    """
    Crea una pila de capas protectoras orientadas según `normal`.
    origin: (x,y,z) punto de montaje (cara del bus hacia el sol).
    radius: radio exterior aproximado de las capas.
    stack: lista de dicts con keys: name, th (m), annulus (m, reducción per capa opcional),
           material (string), emissivity (float opc), density (opc), k (opc), color (tuple opc).
    gap: separación entre capas.
    parent: grupo FreeCAD opcional donde añadir objetos.
    """
    ox,oy,oz = origin
    # desplazamiento local a lo largo de normal (simplemente x en nuestro layout)
    offset = 0.0
    for idx, layer in enumerate(stack):
        th = float(layer.get("th", 0.002))
        ann = float(layer.get("annulus", radius*0.05))
        r_out = float(layer.get("r_out", radius - idx * (ann*0.2)))
        r_in = max(0.01, r_out - ann)
        # usar frusta cónica para buen encuadre mecánico; posicionar el cono con su base centrada en origin + offset
        pos = (ox + offset*normal[0], oy + offset*normal[1], oz + offset*normal[2])
        try:
            fr = cone(r_out, r_in, th, pos, normal)
        except Exception:
            # fallback a disco rectangular si cone falla en algún entorno FreeCAD
            fr = box(th if normal[0] else r_out*2, r_out*2, r_out*2, (pos[0], pos[1]-r_out, pos[2]-r_out))
        o = add(fr, layer.get("name", f"SunLayer_{idx+1}"), layer.get("color", (0.9,0.9,0.9)), 0.0, parent if parent else g_shield)
        # etiquetas físicas simples
        tag_material_props(o, layer.get("material", "Unknown"), density=layer.get("density"), emissivity=layer.get("emissivity"), k=layer.get("k"))
        offset += th + gap
    return True

def create_sun_layer_standoffs(face_x, ring_radius, n_standoffs=8, standoff_r=0.015, standoff_len=0.04, parent=None):
    """
    Crea standoffs radiales que sujetan la pila de capas al borde del bus.
    face_x: coordenada X del bus (punto de anclaje).
    ring_radius: radio donde emergerán los standoffs (en torno al centro YZ).
    """
    for i in range(n_standoffs):
        ang = 2.0 * math.pi * i / n_standoffs
        y = W/2.0 + ring_radius * math.cos(ang)
        z = H/2.0 + ring_radius * math.sin(ang)
        base = (face_x, y, z)
        tip = (face_x + 0.02, W/2.0 + (ring_radius + 0.02) * math.cos(ang), H/2.0 + (ring_radius + 0.02) * math.sin(ang))
        st = tube_between(base, tip, standoff_r)
        if st:
            add(st, f"SunStandoff_{i+1}", (0.6,0.6,0.65), 0.0, parent if parent else g_shield)
# ...existing code...
def tag_material_props(obj, name, density=None, emissivity=None, k=None):
    """
    Añade propiedades informativas de material a un objeto FreeCAD de forma segura.
    """
    try:
        if not hasattr(obj, "Material"):
            obj.addProperty("App::PropertyString", "Material", "Meta", "Material")
        obj.Material = str(name)
        if density is not None and not hasattr(obj, "Density"):
            obj.addProperty("App::PropertyFloat", "Density", "Meta", "Density")
            obj.Density = float(density)
        if emissivity is not None and not hasattr(obj, "Emissivity"):
            obj.addProperty("App::PropertyFloat", "Emissivity", "Meta", "Emissivity")
            obj.Emissivity = float(emissivity)
        if k is not None and not hasattr(obj, "ThermalConductivity"):
            obj.addProperty("App::PropertyFloat", "ThermalConductivity", "Meta", "ThermalConductivity")
            obj.ThermalConductivity = float(k)
    except Exception:
        pass
# ...existing code...

def apply_solar_coating_to_radiators(coating_reflectivity=0.92, coating_emissivity=0.05):
    """
    Marca radiadores con propiedades de recubrimiento solar (para uso informativo).
    """
    for o in doc.Objects:
        if o.Name.startswith("Radiator_"):
            try:
                tag_material_props(o, "Radiator_Alloy", emissivity=coating_emissivity, density=2700.0, k=205.0)
                if not hasattr(o, "Coating_Reflectivity"):
                    o.addProperty("App::PropertyFloat","Coating_Reflectivity","Thermal","Coating")
                o.Coating_Reflectivity = float(coating_reflectivity)
            except Exception:
                pass

# --- ejemplo de uso (insertar en el flujo justo después de crear la cara frontal +X del bus / Parker shield)
# origin frontal (un poco desplazado desde la cara X del bus)
_sun_origin = (L + 0.02, W/2.0, H/2.0)
_sun_radius = min(PS["outer_r"], 0.95) if "PS" in globals() else 0.9

_sun_stack = [
    {"name":"Sun_Outer_Reflector","th":0.001,"annulus":0.020,"material":"Aluminum_Reflect","emissivity":0.05,"density":2700.0,"k":205.0,"color":(0.98,0.95,0.80)},
    {"name":"Sun_Refractory_Ceramic","th":0.008,"annulus":0.018,"material":"RefractoryC","emissivity":0.6,"density":7800.0,"k":20.0,"color":(0.82,0.72,0.62)},
    {"name":"Sun_Spreader_Cu","th":0.004,"annulus":0.015,"material":"Copper","emissivity":0.2,"density":8960.0,"k":380.0,"color":(0.85,0.65,0.45)},
    {"name":"Sun_MLI_Layers","th":0.002,"annulus":0.012,"material":"MLI_Composite","emissivity":0.02,"density":1420.0,"k":0.02,"color":(1.0,1.0,0.92)}
]

# crear pila y standoffs (funciones idempotentes simples)
create_sun_shield_layers(_sun_origin, _sun_radius, _sun_stack, gap=0.001, parent=g_shield)
create_sun_layer_standoffs(L, _sun_radius*0.9, n_standoffs=8, standoff_r=0.012, standoff_len=0.04, parent=g_shield)
apply_solar_coating_to_radiators(coating_reflectivity=0.92, coating_emissivity=0.05)
# ...existing code...

# -------------------------
# Vista final
# -------------------------
doc.recompute()
Gui.activeView().viewAxonometric()
Gui.SendMsgToActiveView("ViewFit")

print("Satélite con racks, blindajes Parker y refrigeración generado (v3).")
print(f"Dimensiones exteriores: {L:.2f} x {W:.2f} x {H:.2f} m")
