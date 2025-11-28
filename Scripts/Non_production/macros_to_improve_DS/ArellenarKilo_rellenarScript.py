ArellenarKilo_rellenarScript.py
# -*- coding:utf-8 -*-
import FreeCAD as App, FreeCADGui as Gui, Part, math

doc_name="CassiniUltra_HeavySatellite_RadiationShield_MULTILAYER"
doc=App.ActiveDocument if App.ActiveDocument and App.ActiveDocument.Label==doc_name else App.newDocument(doc_name)
doc=App.ActiveDocument

# === Parámetros ===
P={
 "shield_shape":"cyl",
 "tank_len":11000.0,"tank_d":6000.0,"hull_t":85.0,"hull_outer_d":7000.0,"liner_t":36.0,
 "tps_front_R":4200.0,"tps_front_t":220.0,"tps_offset":780.0,"shoulder_len":1600.0,
 "bus_len":5200.0,"bus_outer_d":6800.0,"bus_inner_d":5600.0,
 "hga_R":2800.0,"hga_t":32.0,"hga_offset":880.0,"hga_mast_len":2000.0,"hga_mast_d":320.0,
 "rtg_box_l":1600.0,"rtg_box_w":920.0,"rtg_box_t":420.0,"rtg_arm_len":1650.0,"rtg_arm_d":320.0,"rtg_arm_offset_z":1400.0,
 "throat_d":900.0,"exit_d":5600.0,"nozzle_len":4600.0,"gimbal_ring_ro":2800.0,"gimbal_ring_t":160.0,
 "bulkhead_t":90.0,"frame_ring_d":4600.0,"frame_ring_t":140.0,"frame_step":800.0,
 "rcs_thr_d":520.0,"rcs_thr_len":900.0,"rcs_ring_R":4200.0,"rcs_count":12,
 "aux_thr_d":1200.0,"aux_thr_len":1800.0,"aux_thr_ring_R":4800.0,"aux_thr_count":12,
 "rad_shield_inner_d":7600.0,"rad_shield_gap":120.0,"rad_shield_len":7600.0,
 "whipple_t":80.0,"whipple_gap":300.0,
 "shield_box_L":7600.0,"shield_box_W":7600.0,"shield_box_H":7600.0,
 "inst_bay_len":2400.0,"inst_bay_d":4800.0,
 "mag_boom_len":5200.0,"mag_boom_d":220.0,
 "star_boom_len":3800.0,"star_boom_d":180.0,
 "fin_len":1600.0,"fin_w":940.0,"fin_t":180.0,
 "ion_thr_d":380.0,"ion_thr_len":1100.0,"ion_ring_R":3600.0,"ion_count":16,
 "hall_thr_d":720.0,"hall_thr_len":1400.0,"hall_arm_len":1800.0,
 "rad_len":3200.0,"rad_w":1400.0,"rad_t":90.0,"rad_z":1800.0,
 "parker_shield_R":3200.0,"engine_bay_len":2800.0
}

# === Materiales ===
MATS={
 "Hull":{"name":"Ti-6Al-4V","rho":4430,"E":114e9,"nu":0.34},
 "Tank":{"name":"Al-Li 2195","rho":2700,"E":73e9,"nu":0.33},
 "Shield":{"name":"CFRP+PE+W","rho":1900,"E":60e9,"nu":0.28},
 "Whipple":{"name":"Al 6061-T6","rho":2700,"E":69e9,"nu":0.33},
 "Nozzle":{"name":"C/SiC","rho":2600,"E":300e9,"nu":0.15},
 "RTG":{"name":"Inconel+Graphite","rho":8200,"E":200e9,"nu":0.29},
 "Booms":{"name":"Al 7075-T6","rho":2810,"E":72e9,"nu":0.33},
 "Radiator":{"name":"Al+Ammonia plate","rho":1500,"E":40e9,"nu":0.29},
 "HGA":{"name":"CFRP Honeycomb","rho":1400,"E":70e9,"nu":0.30},
 "Avionics":{"name":"Al Frame + PCB","rho":2200,"E":50e9,"nu":0.30},
 "PE_Shield":{"name":"HDPE","rho":950,"E":1.1e9,"nu":0.42},
 "TrayCube":{"name":"Al 7075 + CFRP","rho":1750,"E":60e9,"nu":0.30},
 "TrayCirc":{"name":"Al 6061 + CFRP","rho":1800,"E":58e9,"nu":0.30},
 "Rail":{"name":"Ti-6Al-4V","rho":4430,"E":114e9,"nu":0.34}
}

# === Utilidades ===
X_AXIS=App.Vector(1,0,0);Y_AXIS=App.Vector(0,1,0);Z_AXIS=App.Vector(0,0,1)
rot_to_x=lambda:App.Rotation(Y_AXIS,90)
def add_obj(s,n): o=doc.addObject("Part::Feature",n); o.Shape=s; return o
def color(o,rgb): 
    if hasattr(o,"ViewObject"): o.ViewObject.ShapeColor=rgb
    return o
def cyl_x(d,L,cx=0,cy=0,cz=0): s=Part.makeCylinder(d/2.0,L); s.Placement=App.Placement(App.Vector(cx-L/2.0,cy,cz),rot_to_x()); return s
def cone_x(d1,d2,L,cx=0,cy=0,cz=0): s=Part.makeCone(max(d1/2.0,1.0),max(d2/2.0,1.0),L); s.Placement=App.Placement(App.Vector(cx-L/2.0,cy,cz),rot_to_x()); return s
def box_x(l,w,h,cx=0,cy=0,cz=0): b=Part.makeBox(l,w,h); b.Placement=App.Placement(App.Vector(cx-l/2.0,cy-w/2.0,cz-h/2.0),App.Rotation()); return b

# === Escudo Parker multilayer ===
def parker_shield_cyl(cx, diam, face_th=10.0, foam_th=120.0, coat_th=2.0, uhtc_t=10.0,
                      sup_L=280.0, sup_d1=900.0, sup_d2=600.0):
    R=diam/2.0
    cx0=cx+sup_L+(face_th*2+foam_th+coat_th)/2.0
    back_cc=cyl_x(diam,face_th,cx=cx0-(foam_th/2+face_th/2+coat_th/2))
    core=cyl_x(diam-10.0,foam_th,cx=cx0)
    front_cc=cyl_x(diam,face_th,cx=cx0+(foam_th/2+face_th/2))
    coat=cyl_x(diam,coat_th,cx=cx0+(foam_th/2+face_th+coat_th/2))
    torus=Part.makeTorus(R-6.0,uhtc_t); torus.Placement=App.Placement(App.Vector(cx0,0,0),App.Rotation(Y_AXIS,90))
    sup=cone_x(sup_d1,sup_d2,sup_L,cx=cx+sup_L/2.0)
    fused=back_cc.fuse(core).fuse(front_cc).fuse(coat).fuse(torus).fuse(sup).removeSplitter()
    return add_obj(fused,"Parker_Shield")

# === Construcción principal ===
tank_cx=0.0
tank=cyl_x(P["tank_d"],P["tank_len"],cx=tank_cx); color(add_obj(tank,"Tank"),(0.75,0.75,0.8))

# Escudo Parker
cap_center_x=tank_cx+P["tank_len"]/2.0+P["tps_offset"]
shield_obj=parker_shield_cyl(cap_center_x,P["parker_shield_R"]*2.0)

# Whipple externo
wh_outer=cyl_x(P["parker_shield_R"]*2.0