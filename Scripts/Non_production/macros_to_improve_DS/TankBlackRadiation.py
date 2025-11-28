# -*- coding: utf-8 -*-
"""
Macro FreeCAD: Nave Espacial con Volumen Interno, Protección Extrema de Radiación y Optimizada para Impresión 3D
Basado en TankBlackRadiation, expandido a nave completa con múltiples subsistemas.

Autor: AI Assistant Mejorado
Unidades: mm, eje longitudinal = X (de nariz a cola)
Versión: 2.0 - Corregida, mejorada y expandida

Descripción:
Esta macro genera un modelo 3D paramétrico de una nave espacial avanzada con:
- Casco hueco con volumen interno accesible
- Blindaje multi-capa contra radiación extrema
- Subsistemas internos: cockpit, reactor, tanques, cuartos de tripulación, soporte vital
- Sistemas de propulsión: motor principal y thrusters de actitud
- Características externas: alas, paneles solares, antenas, tren de aterrizaje
- Sistemas de energía: baterías y generadores solares
- Sensores y comunicaciones
- Optimización para impresión 3D con soportes internos
"""

import FreeCAD as App, FreeCADGui as Gui, Part, math

DOC_NAME = "TankBlackRadiation_Spaceship"
if App.ActiveDocument is None or App.ActiveDocument.Label != DOC_NAME:
    App.newDocument(DOC_NAME)
doc = App.ActiveDocument

def validate_parameters():
    """Validar que los parámetros sean consistentes y positivos"""
    required_positive = [
        "total_length", "hull_outer_d", "hull_inner_d", "hull_wall_t",
        "nose_len", "mid_len", "rear_len", "tail_len",
        "rad_shield_layers", "rad_layer_t",
        "cockpit_len", "cockpit_w", "cockpit_h",
        "reactor_len", "reactor_d",
        "tank_len", "tank_d", "tank_n",
        "main_engine_d", "main_engine_l",
        "attitude_thruster_d", "attitude_thruster_l", "attitude_n",
        "wing_span", "wing_chord", "wing_t",
        "solar_panel_l", "solar_panel_w", "solar_panel_t", "solar_n",
        "antenna_h", "antenna_d",
        "landing_gear_l", "landing_gear_d", "landing_n",
        "min_wall_t", "support_spacing", "fillet_r"
    ]
    for param in required_positive:
        if P.get(param, 0) <= 0:
            raise ValueError(f"Parámetro {param} debe ser positivo")

    if P["hull_inner_d"] >= P["hull_outer_d"]:
        raise ValueError("Diámetro interno del casco debe ser menor que el externo")

    if P["nose_len"] + P["mid_len"] + P["rear_len"] + P["tail_len"] != P["total_length"]:
        print("Advertencia: La suma de longitudes de secciones no coincide con total_length")

# Validar parámetros al inicio
validate_parameters()

# ========================
# Parámetros Completos de la Nave Espacial
# ========================
P = {
    # Dimensiones generales
    "total_length": 15000.0,  # Longitud total de la nave
    "hull_outer_d": 4000.0,   # Diámetro exterior del casco
    "hull_inner_d": 3800.0,   # Diámetro interior (volumen interno)
    "hull_wall_t": 100.0,     # Grosor de pared del casco (imprimible 3D)

    # Secciones longitudinales
    "nose_len": 3000.0,       # Longitud de la nariz
    "mid_len": 6000.0,        # Longitud de la sección media
    "rear_len": 4000.0,       # Longitud de la sección trasera
    "tail_len": 2000.0,       # Longitud de la cola

    # Protección de radiación (multi-capa extrema)
    "rad_shield_layers": 5,   # Número de capas de blindaje
    "rad_layer_t": 50.0,      # Grosor por capa
    "rad_materials": ["LEAD", "TUNGSTEN", "BORON", "WATER", "CARBON"],  # Materiales por capa

    # Compartimentos internos
    "cockpit_len": 2000.0, "cockpit_w": 1500.0, "cockpit_h": 1200.0,
    "reactor_len": 2500.0, "reactor_d": 2000.0,
    "tank_len": 3000.0, "tank_d": 1800.0, "tank_n": 4,  # Tanques de combustible/radiación
    "crew_quarters_len": 1500.0, "crew_quarters_w": 1200.0, "crew_quarters_h": 1000.0, "crew_n": 2,
    "life_support_len": 1000.0, "life_support_d": 800.0,
    "control_room_len": 800.0, "control_room_w": 1000.0, "control_room_h": 800.0,
    "battery_len": 500.0, "battery_d": 600.0, "battery_n": 6,
    "generator_len": 1200.0, "generator_d": 1000.0,

    # Sistemas de propulsión
    "main_engine_d": 1500.0, "main_engine_l": 2000.0,
    "attitude_thruster_d": 200.0, "attitude_thruster_l": 500.0, "attitude_n": 12,

    # Características externas
    "wing_span": 8000.0, "wing_chord": 2000.0, "wing_t": 100.0,
    "solar_panel_l": 5000.0, "solar_panel_w": 2000.0, "solar_panel_t": 20.0, "solar_n": 4,
    "antenna_h": 1500.0, "antenna_d": 800.0,
    "landing_gear_l": 1000.0, "landing_gear_d": 150.0, "landing_n": 6,

    # Sistemas de energía
    "battery_len": 500.0, "battery_d": 600.0, "battery_n": 6,
    "generator_len": 1200.0, "generator_d": 1000.0,

    # Detalles para impresión 3D
    "min_wall_t": 2.0,        # Grosor mínimo de pared
    "support_spacing": 500.0, # Espaciado para soportes internos
    "fillet_r": 50.0,         # Radio de fileteado para suavizado
}

# Materiales con propiedades físicas (densidad en kg/m³, colores RGB)
MATERIALS = {
    'TITANIUM': {'name': 'Ti-6Al-4V', 'rho': 4430.0, 'color': (0.7, 0.7, 0.8)},
    'CARBON_FIBER': {'name': 'Carbon Fiber Composite', 'rho': 1600.0, 'color': (0.2, 0.2, 0.2)},
    'LEAD': {'name': 'Lead Shield', 'rho': 11340.0, 'color': (0.3, 0.3, 0.3)},
    'TUNGSTEN': {'name': 'Tungsten Alloy', 'rho': 19300.0, 'color': (0.4, 0.4, 0.4)},
    'BORON': {'name': 'Boron Carbide', 'rho': 2500.0, 'color': (0.1, 0.1, 0.1)},
    'WATER': {'name': 'Water/Anti-Radiation Tank', 'rho': 1000.0, 'color': (0.0, 0.5, 1.0)},
    'STEEL': {'name': 'Stainless Steel 316L', 'rho': 8000.0, 'color': (0.6, 0.6, 0.6)},
    'ABLATIVE': {'name': 'Ablative TPS', 'rho': 1200.0, 'color': (0.8, 0.4, 0.0)},
    'ALUMINUM': {'name': 'Aluminum 6061', 'rho': 2700.0, 'color': (0.9, 0.9, 0.9)},
    'COPPER': {'name': 'Copper for Heat Sinks', 'rho': 8960.0, 'color': (0.8, 0.5, 0.2)},
    'SILICON': {'name': 'Silicon Solar Cells', 'rho': 2330.0, 'color': (0.6, 0.6, 0.7)},
    'INSULATION': {'name': 'Thermal Insulation Foam', 'rho': 50.0, 'color': (0.8, 0.8, 0.8)},
    'BATTERY': {'name': 'Lithium-Ion Battery', 'rho': 2500.0, 'color': (0.1, 0.1, 0.5)},
    'SUPERCONDUCTOR': {'name': 'Superconducting Wire', 'rho': 8000.0, 'color': (0.0, 0.8, 0.8)},
}

# ========================
# Funciones Utilitarias
# ========================
def rot_to_x():
    return App.Rotation(App.Vector(0,1,0), 90)

def add_obj(shape, label, material=None):
    obj = doc.addObject("Part::Feature", label)
    obj.Shape = shape
    if material and material in MATERIALS:
        obj.ViewObject.ShapeColor = MATERIALS[material]['color']
    return obj

def make_cylinder(d, l, cx=0, cy=0, cz=0, axis='x'):
    r = d / 2.0
    cyl = Part.makeCylinder(r, l)
    if axis == 'x':
        cyl.Placement = App.Placement(App.Vector(cx - l/2.0, cy, cz), rot_to_x())
    elif axis == 'y':
        cyl.Placement = App.Placement(App.Vector(cx, cy - l/2.0, cz), App.Rotation(App.Vector(1,0,0), 90))
    elif axis == 'z':
        cyl.Placement = App.Placement(App.Vector(cx, cy, cz - l/2.0), App.Rotation())
    return cyl

def make_cone(d1, d2, l, cx=0, cy=0, cz=0, axis='x'):
    r1, r2 = d1/2.0, d2/2.0
    cone = Part.makeCone(r1, r2, l)
    if axis == 'x':
        cone.Placement = App.Placement(App.Vector(cx - l/2.0, cy, cz), rot_to_x())
    return cone

def make_box(w, h, d, cx=0, cy=0, cz=0):
    box = Part.makeBox(w, h, d)
    box.Placement = App.Placement(App.Vector(cx - w/2.0, cy - h/2.0, cz - d/2.0), App.Rotation())
    return box

def fillet_shape(shape, r):
    try:
        edges = [e for e in shape.Edges if 100 < e.Length < 10000]
        return shape.makeFillet(r, edges)
    except:
        return shape

# ========================
# Componentes de la Nave
# ========================

def make_hull():
    """Crear el casco principal con volumen interno hueco"""
    # Nariz cónica hueca
    outer_nose = Part.makeCone(P["hull_outer_d"]/2.0, P["hull_inner_d"]/2.0, P["nose_len"])
    inner_nose = Part.makeCone(P["hull_inner_d"]/2.0, P["hull_inner_d"]/2.0, P["nose_len"] + 100)
    nose = outer_nose.cut(inner_nose)
    nose.Placement = App.Placement(App.Vector(P["nose_len"]/2.0, 0, 0), rot_to_x())

    # Sección media cilíndrica hueca
    mid_outer = make_cylinder(P["hull_outer_d"], P["mid_len"], cx=P["nose_len"] + P["mid_len"]/2.0)
    mid_inner = make_cylinder(P["hull_inner_d"], P["mid_len"] + 100, cx=P["nose_len"] + P["mid_len"]/2.0)
    mid = mid_outer.cut(mid_inner)

    # Sección trasera hueca
    rear_outer = make_cylinder(P["hull_outer_d"], P["rear_len"], cx=P["nose_len"] + P["mid_len"] + P["rear_len"]/2.0)
    rear_inner = make_cylinder(P["hull_inner_d"], P["rear_len"] + 100, cx=P["nose_len"] + P["mid_len"] + P["rear_len"]/2.0)
    rear = rear_outer.cut(rear_inner)

    # Cola convergente hueca
    outer_tail = Part.makeCone(P["hull_outer_d"]/2.0, P["hull_outer_d"]*0.5/2.0, P["tail_len"])
    inner_tail = Part.makeCone(P["hull_inner_d"]/2.0, P["hull_inner_d"]*0.5/2.0, P["tail_len"] + 100)
    tail = outer_tail.cut(inner_tail)
    tail.Placement = App.Placement(App.Vector(P["total_length"] - P["tail_len"]/2.0, 0, 0), rot_to_x())

    # Fusionar y filetear
    hull = nose.fuse(mid).fuse(rear).fuse(tail)
    hull = fillet_shape(hull, P["fillet_r"])
    return add_obj(hull, "Hull", "TITANIUM")

def make_radiation_shields():
    """Sistema de blindaje multi-capa para radiación extrema"""
    shields = []
    for i in range(P["rad_shield_layers"]):
        layer_d = P["hull_outer_d"] + (i+1) * P["rad_layer_t"] * 2
        layer = make_cylinder(layer_d, P["total_length"], cx=P["total_length"]/2.0)
        inner_cut = make_cylinder(layer_d - P["rad_layer_t"]*2, P["total_length"] + 100, cx=P["total_length"]/2.0)
        layer = layer.cut(inner_cut)
        mat = P["rad_materials"][i] if i < len(P["rad_materials"]) else "LEAD"
        shields.append(add_obj(layer, f"Rad_Shield_Layer_{i+1}", mat))
    return shields

def make_internal_compartments():
    """Crear compartimentos internos: cockpit, reactor, tanques, cuartos de tripulación, soporte vital, sala de control"""
    compartments = []

    # Cockpit (cabina de mando)
    cockpit = make_box(P["cockpit_len"], P["cockpit_w"], P["cockpit_h"],
                      cx=P["nose_len"] - P["cockpit_len"]/2.0, cy=0, cz=0)
    compartments.append(add_obj(cockpit, "Cockpit", "TITANIUM"))

    # Reactor nuclear/iónico
    reactor = make_cylinder(P["reactor_d"], P["reactor_len"],
                           cx=P["nose_len"] + P["mid_len"]/2.0, cy=0, cz=0)
    compartments.append(add_obj(reactor, "Reactor", "STEEL"))

    # Tanques de combustible/radiación/agua
    for i in range(P["tank_n"]):
        angle = i * (360.0 / P["tank_n"])
        x = P["nose_len"] + P["mid_len"] + P["rear_len"]/2.0
        y = (P["hull_inner_d"]/2.0 - P["tank_d"]/2.0 - 200) * math.cos(math.radians(angle))
        z = (P["hull_inner_d"]/2.0 - P["tank_d"]/2.0 - 200) * math.sin(math.radians(angle))
        tank = make_cylinder(P["tank_d"], P["tank_len"], cx=x, cy=y, cz=z)
        compartments.append(add_obj(tank, f"Tank_{i+1}", "WATER"))

    # Cuartos de tripulación
    for i in range(P["crew_n"]):
        quarters = make_box(P["crew_quarters_len"], P["crew_quarters_w"], P["crew_quarters_h"],
                           cx=P["nose_len"] + P["mid_len"]*0.3 + i*P["crew_quarters_len"], cy=0, cz=P["hull_inner_d"]/4.0)
        compartments.append(add_obj(quarters, f"Crew_Quarters_{i+1}", "ALUMINUM"))

    # Sistema de soporte vital (filtrado de aire, reciclaje)
    life_support = make_cylinder(P["life_support_d"], P["life_support_len"],
                                cx=P["nose_len"] + P["mid_len"]*0.7, cy=0, cz=-P["hull_inner_d"]/4.0)
    compartments.append(add_obj(life_support, "Life_Support", "STEEL"))

    # Sala de control (computadoras, navegación)
    control_room = make_box(P["control_room_len"], P["control_room_w"], P["control_room_h"],
                           cx=P["nose_len"] + P["mid_len"]*0.5, cy=0, cz=P["hull_inner_d"]/3.0)
    compartments.append(add_obj(control_room, "Control_Room", "ALUMINUM"))

    return compartments

def make_propulsion_systems():
    """Sistemas de propulsión: motor principal y thrusters de actitud"""
    propulsion = []

    # Motor principal
    main_engine = make_cone(P["main_engine_d"], P["main_engine_d"]*0.5, P["main_engine_l"],
                           cx=P["total_length"] - P["main_engine_l"]/2.0)
    propulsion.append(add_obj(main_engine, "Main_Engine", "STEEL"))

    # Thrusters de actitud
    for i in range(P["attitude_n"]):
        angle = i * (360.0 / P["attitude_n"])
        x = P["nose_len"] + P["mid_len"] + P["rear_len"]*0.7
        y = P["hull_outer_d"]/2.0 * math.cos(math.radians(angle))
        z = P["hull_outer_d"]/2.0 * math.sin(math.radians(angle))
        thruster = make_cylinder(P["attitude_thruster_d"], P["attitude_thruster_l"],
                                cx=x, cy=y, cz=z, axis='x')
        propulsion.append(add_obj(thruster, f"Attitude_Thruster_{i+1}", "TITANIUM"))

    return propulsion

def make_power_systems():
    """Sistemas de energía: baterías y generadores solares"""
    power = []

    # Baterías de litio-ion
    for i in range(P["battery_n"]):
        angle = i * (360.0 / P["battery_n"])
        x = P["nose_len"] + P["mid_len"]*0.8
        y = (P["hull_inner_d"]/2.0 - P["battery_d"]/2.0 - 100) * math.cos(math.radians(angle))
        z = (P["hull_inner_d"]/2.0 - P["battery_d"]/2.0 - 100) * math.sin(math.radians(angle))
        battery = make_cylinder(P["battery_d"], P["battery_len"], cx=x, cy=y, cz=z)
        power.append(add_obj(battery, f"Battery_{i+1}", "BATTERY"))

    # Generador termoeléctrico (RTG - Radioisotope Thermoelectric Generator)
    generator = make_cylinder(P["generator_d"], P["generator_len"],
                             cx=P["nose_len"] + P["mid_len"]*0.6, cy=0, cz=-P["hull_inner_d"]/3.0)
    power.append(add_obj(generator, "RTG_Generator", "SUPERCONDUCTOR"))

    return power

def make_external_features():
    """Características externas: alas, paneles solares, antena, tren de aterrizaje"""
    features = []

    # Alas
    wing_left = make_box(P["wing_chord"], P["wing_span"]/2.0, P["wing_t"],
                        cx=P["nose_len"] + P["mid_len"]/2.0, cy=P["wing_span"]/4.0, cz=0)
    wing_right = make_box(P["wing_chord"], P["wing_span"]/2.0, P["wing_t"],
                         cx=P["nose_len"] + P["mid_len"]/2.0, cy=-P["wing_span"]/4.0, cz=0)
    features.append(add_obj(wing_left, "Wing_Left", "CARBON_FIBER"))
    features.append(add_obj(wing_right, "Wing_Right", "CARBON_FIBER"))

    # Paneles solares
    for i in range(P["solar_n"]):
        side = 1 if i % 2 == 0 else -1
        panel = make_box(P["solar_panel_l"], P["solar_panel_w"], P["solar_panel_t"],
                        cx=P["nose_len"] + P["mid_len"]*0.8 + i*500, cy=side*(P["hull_outer_d"]/2.0 + P["solar_panel_w"]/2.0), cz=0)
        features.append(add_obj(panel, f"Solar_Panel_{i+1}", "CARBON_FIBER"))

    # Antena
    antenna = make_cylinder(P["antenna_d"], P["antenna_h"],
                           cx=P["nose_len"] + P["mid_len"] + P["antenna_h"]/2.0, cy=0, cz=P["hull_outer_d"]/2.0 + 200)
    features.append(add_obj(antenna, "Antenna", "STEEL"))

    # Tren de aterrizaje
    for i in range(P["landing_n"]):
        angle = i * (360.0 / P["landing_n"])
        x = P["nose_len"] + P["mid_len"]*0.3
        y = P["hull_outer_d"]/2.0 * math.cos(math.radians(angle))
        z = P["hull_outer_d"]/2.0 * math.sin(math.radians(angle))
        leg = make_cylinder(P["landing_gear_d"], P["landing_gear_l"], cx=x, cy=y, cz=z, axis='x')
        features.append(add_obj(leg, f"Landing_Gear_{i+1}", "TITANIUM"))

    return features

def make_support_structures():
    """Estructuras de soporte interno para impresión 3D"""
    supports = []
    spacing = P["support_spacing"]
    for x in range(int(P["nose_len"]), int(P["total_length"] - P["tail_len"]), int(spacing)):
        for angle in range(0, 360, 45):
            y = (P["hull_inner_d"]/2.0 - 300) * math.cos(math.radians(angle))
            z = (P["hull_inner_d"]/2.0 - 300) * math.sin(math.radians(angle))
            support = make_cylinder(50, P["hull_inner_d"] - 600, cx=x, cy=y, cz=z, axis='y')
            supports.append(add_obj(support, f"Support_{x}_{angle}", "CARBON_FIBER"))
    return supports

# ========================
# Ensamblaje Final
# ========================
hull = make_hull()
rad_shields = make_radiation_shields()
internal_comps = make_internal_compartments()
propulsion = make_propulsion_systems()
external_features = make_external_features()
supports = make_support_structures()

# Fusionar componentes principales
main_body = hull.Shape
for comp in internal_comps + propulsion + external_features:
    main_body = main_body.fuse(comp.Shape)

# Añadir blindaje de radiación como capas separadas
for shield in rad_shields:
    main_body = main_body.fuse(shield.Shape)

# Objeto final
spaceship_obj = add_obj(main_body, "TankBlackRadiation_Spaceship", "TITANIUM")
spaceship_obj.ViewObject.DisplayMode = "Shaded"

# Recomputar documento
doc.recompute()

try:
    Gui.ActiveDocument.ActiveView.viewAxonometric()
    Gui.SendMsgToActiveView("ViewFit")
except:
    pass

print("Nave espacial TankBlackRadiation completada: volumen interno, blindaje extremo de radiación multi-capa, optimizada para impresión 3D con soportes internos.")
