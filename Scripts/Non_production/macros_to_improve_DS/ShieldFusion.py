# -*- coding: utf-8 -*-
"""
Advanced Spacecraft Design System with Radiation Shielding
FreeCAD 0.19-0.21+ compatible
Units: mm (densities in kg/m³)
"""
import FreeCAD as App
import FreeCADGui as Gui
import Part, math

DOC_NAME = "AdvancedSpacecraft_Shield"

# ============================================================================
# ADVANCED PARAMETERS
# ============================================================================
PARAMS = {
    # Main spacecraft body
    "body_sections": [
        (600.0, 1400.0),  # Base section
        (550.0, 1300.0),
        (500.0, 1150.0),
        (600.0, 1200.0),
        (700.0, 1350.0),
    ],
    "body_wall_thickness": 8.0,
    "body_edge_fillet": 4.0,
    
    # Radiation shielding layers
    "shield_layers": [
        {"material": "Polyethylene", "thickness": 50.0, "density": 950.0, "color": (0.9, 0.9, 0.95)},
        {"material": "Aluminum", "thickness": 15.0, "density": 2700.0, "color": (0.75, 0.75, 0.8)},
        {"material": "Lead", "thickness": 5.0, "density": 11340.0, "color": (0.4, 0.4, 0.45)},
        {"material": "Water", "thickness": 100.0, "density": 1000.0, "color": (0.3, 0.5, 0.8)},
    ],
    
    # Thermal Protection System (TPS)
    "tps_enabled": True,
    "tps_material": "Carbon-Carbon",
    "tps_thickness": 25.0,
    "tps_density": 1800.0,
    "tps_color": (0.1, 0.1, 0.12),
    
    # Advanced propulsion
    "propulsion_type": "fusion",  # fusion, ion, plasma
    "reactor_diameter": 800.0,
    "reactor_length": 1200.0,
    "reactor_shield_thickness": 150.0,
    
    # Magnetic field coils
    "mag_coil_count": 8,
    "mag_coil_radius": 700.0,
    "mag_coil_thickness": 40.0,
    "mag_coil_spacing": 200.0,
    
    # Heat radiators
    "radiator_count": 6,
    "radiator_length": 2000.0,
    "radiator_width": 300.0,
    "radiator_thickness": 8.0,
    "radiator_angle_offset": 60.0,
    
    # Fuel tanks (cryogenic)
    "fuel_tank_diameter": 600.0,
    "fuel_tank_length": 1800.0,
    "fuel_tank_count": 4,
    "fuel_tank_insulation": 80.0,
    
    # Whipple shield (micrometeorite protection)
    "whipple_layers": 3,
    "whipple_spacing": 150.0,
    "whipple_thickness": 2.0,
    "whipple_outer_diameter": 1600.0,
    
    # Habitat module
    "habitat_diameter": 1200.0,
    "habitat_length": 800.0,
    "habitat_wall_thickness": 12.0,
    
    # Solar panels
    "solar_panel_count": 4,
    "solar_panel_length": 3000.0,
    "solar_panel_width": 800.0,
    "solar_panel_thickness": 5.0,
    
    # Communication dish
    "comm_dish_diameter": 400.0,
    "comm_dish_depth": 80.0,
    
    # Materials database
    "materials": {
        "Al6061-T6": {"density": 2700.0, "color": (0.70, 0.75, 0.80)},
        "Ti6Al4V": {"density": 4420.0, "color": (0.55, 0.55, 0.65)},
        "Inconel625": {"density": 8440.0, "color": (0.45, 0.50, 0.55)},
        "CFRP": {"density": 1600.0, "color": (0.15, 0.15, 0.18)},
        "Polyethylene": {"density": 950.0, "color": (0.9, 0.9, 0.95)},
        "Lead": {"density": 11340.0, "color": (0.4, 0.4, 0.45)},
        "Water": {"density": 1000.0, "color": (0.3, 0.5, 0.8, 0.6)},
        "CarbonCarbon": {"density": 1800.0, "color": (0.1, 0.1, 0.12)},
        "Tungsten": {"density": 19250.0, "color": (0.3, 0.3, 0.35)},
        "Boron": {"density": 2340.0, "color": (0.5, 0.4, 0.3)},
    },
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
def get_or_create_doc():
    """Get or create FreeCAD document"""
    d = App.ActiveDocument
    if d is None or d.Name != DOC_NAME:
        d = App.newDocument(DOC_NAME)
    return d

def set_material(obj, mat_name, density, color):
    """Set material properties to object"""
    if "Density" not in obj.PropertiesList:
        obj.addProperty("App::PropertyFloat", "Density", "Material", "kg/m³")
    if "MaterialName" not in obj.PropertiesList:
        obj.addProperty("App::PropertyString", "MaterialName", "Material")
    obj.Density = float(density)
    obj.MaterialName = mat_name
    if len(color) == 3:
        obj.ViewObject.ShapeColor = color
    else:
        obj.ViewObject.ShapeColor = color[:3]
        obj.ViewObject.Transparency = int((1.0 - color[3]) * 100)

def calculate_mass(obj):
    """Calculate mass in kg from volume and density"""
    vol_m3 = obj.Shape.Volume * 1e-9
    dens = obj.Density if "Density" in obj.PropertiesList else 0.0
    return dens * vol_m3

def refine(shape):
    """Remove splitters from shape"""
    try:
        return shape.removeSplitter()
    except:
        return shape

def create_cylinder(name, radius, height, z_pos, mat_name, density, color, doc):
    """Create cylinder with material properties"""
    shape = Part.makeCylinder(radius, height, App.Vector(0, 0, z_pos))
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    set_material(obj, mat_name, density, color)
    return obj

def create_hollow_cylinder(name, r_outer, r_inner, height, z_pos, mat_name, density, color, doc):
    """Create hollow cylinder"""
    outer = Part.makeCylinder(r_outer, height, App.Vector(0, 0, z_pos))
    inner = Part.makeCylinder(r_inner, height, App.Vector(0, 0, z_pos))
    shape = refine(outer.cut(inner))
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    set_material(obj, mat_name, density, color)
    return obj

def create_sphere(name, radius, center, mat_name, density, color, doc):
    """Create sphere with material properties"""
    shape = Part.makeSphere(radius, center)
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    set_material(obj, mat_name, density, color)
    return obj

def create_torus(name, r_major, r_minor, center, mat_name, density, color, doc):
    """Create torus (for magnetic coils)"""
    shape = Part.makeTorus(r_major, r_minor, center)
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    set_material(obj, mat_name, density, color)
    return obj

def create_box(name, length, width, height, center, mat_name, density, color, doc):
    """Create box centered at position"""
    shape = Part.makeBox(length, width, height)
    shape.translate(center.sub(App.Vector(length/2, width/2, height/2)))
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    set_material(obj, mat_name, density, color)
    return obj

def apply_fillet(obj, radius, edge_filter=None):
    """Apply fillet to edges"""
    if radius <= 0:
        return
    try:
        edges = obj.Shape.Edges if edge_filter is None else edge_filter(obj.Shape)
        if edges:
            obj.Shape = obj.Shape.makeFillet(radius, edges)
    except Exception as e:
        App.Console.PrintWarning(f"Fillet failed: {e}\n")

# ============================================================================
# RADIATION SHIELDING FUNCTIONS
# ============================================================================

def create_multilayer_shield(name, base_radius, base_height, z_pos, layers, doc):
    """
    Create multi-layer radiation shield
    layers: list of dicts with 'material', 'thickness', 'density', 'color'
    """
    shields = []
    current_radius = base_radius
    
    for i, layer in enumerate(layers):
        r_inner = current_radius
        r_outer = current_radius + layer["thickness"]
        
        shield = create_hollow_cylinder(
            f"{name}_Layer{i+1}_{layer['material']}",
            r_outer, r_inner, base_height, z_pos,
            layer["material"], layer["density"], layer["color"], doc
        )
        shields.append(shield)
        current_radius = r_outer
    
    return shields, current_radius

def create_whipple_shield(name, base_radius, height, z_pos, layer_count, spacing, thickness, doc):
    """
    Create Whipple shield for micrometeorite protection
    Multiple thin layers with spacing
    """
    shields = []
    mat = PARAMS["materials"]["Al6061-T6"]
    
    for i in range(layer_count):
        r = base_radius + i * spacing
        shield = create_hollow_cylinder(
            f"{name}_Whipple{i+1}",
            r + thickness, r, height, z_pos,
            "Al6061-T6", mat["density"], mat["color"], doc
        )
        shields.append(shield)
    
    return shields

def create_magnetic_shield_coils(name, base_radius, coil_count, coil_thickness, spacing, z_start, doc):
    """
    Create magnetic field coils for radiation deflection
    """
    coils = []
    mat = PARAMS["materials"]["CFRP"]
    
    for i in range(coil_count):
        z_pos = z_start + i * spacing
        coil = create_torus(
            f"{name}_MagCoil{i+1}",
            base_radius, coil_thickness,
            App.Vector(0, 0, z_pos),
            "CFRP", mat["density"], mat["color"], doc
        )
        coils.append(coil)
    
    return coils

def create_water_shield(name, r_outer, r_inner, height, z_pos, doc):
    """
    Create water shield layer (excellent for neutron absorption)
    """
    mat = PARAMS["materials"]["Water"]
    return create_hollow_cylinder(
        name, r_outer, r_inner, height, z_pos,
        "Water", mat["density"], mat["color"], doc
    )

def create_borated_polyethylene_shield(name, radius, height, z_pos, thickness, doc):
    """
    Create borated polyethylene shield (hydrogen-rich, good for neutrons)
    """
    mat = PARAMS["materials"]["Polyethylene"]
    return create_hollow_cylinder(
        f"{name}_BoratedPoly",
        radius + thickness, radius, height, z_pos,
        "Polyethylene", mat["density"], mat["color"], doc
    )

# ============================================================================
# THERMAL PROTECTION SYSTEM
# ============================================================================
def create_tps_layer(name, base_shape, thickness, doc):
    """
    Create Thermal Protection System layer
    Uses carbon-carbon composite
    """
    mat = PARAMS["materials"]["CarbonCarbon"]
    
    # Offset the base shape outward
    try:
        tps_shape = base_shape.makeOffsetShape(thickness, 0.01)
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = tps_shape
        set_material(obj, "CarbonCarbon", mat["density"], mat["color"])
        return obj
    except Exception as e:
        App.Console.PrintError(f"TPS creation failed: {e}\n")
        return None

def create_ablative_shield(name, radius, height, z_pos, thickness, doc):
    """
    Create ablative heat shield (for atmospheric entry)
    """
    # Cone shape for aerodynamic heating
    r_base = radius
    r_tip = radius * 0.3
    
    cone = Part.makeCone(r_base, r_tip, height, App.Vector(0, 0, z_pos))
    shell = Part.makeCone(r_base - thickness, r_tip - thickness, height, App.Vector(0, 0, z_pos))
    shape = refine(cone.cut(shell))
    
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    mat = PARAMS["materials"]["CarbonCarbon"]
    set_material(obj, "CarbonCarbon", mat["density"], mat["color"])
    return obj

# ============================================================================
# PROPULSION SYSTEMS
# ============================================================================
def create_fusion_reactor(name, diameter, length, z_pos, shield_thickness, doc):
    """
    Create fusion reactor with radiation shielding
    """
    r_core = diameter / 2.0
    r_shield = r_core + shield_thickness
    
    # Reactor core
    mat_tungsten = PARAMS["materials"]["Tungsten"]
    core = create_cylinder(
        f"{name}_Core", r_core, length, z_pos,
        "Tungsten", mat_tungsten["density"], mat_tungsten["color"], doc
    )
    
    # Radiation shield around reactor
    mat_lead = PARAMS["materials"]["Lead"]
    shield = create_hollow_cylinder(
        f"{name}_Shield", r_shield, r_core, length, z_pos,
        "Lead", mat_lead["density"], mat_lead["color"], doc
    )
    
    # Magnetic confinement coils
    coils = create_magnetic_shield_coils(
        f"{name}_Confinement", r_shield + 50, 6, 30, length/6, z_pos, doc
    )
    
    return core, shield, coils

def create_ion_thruster(name, diameter, length, z_pos, doc):
    """
    Create ion thruster assembly
    """
    r = diameter / 2.0
    
    # Thruster body
    mat_ti = PARAMS["materials"]["Ti6Al4V"]
    body = create_cylinder(
        f"{name}_Body", r, length * 0.6, z_pos,
        "Ti6Al4V", mat_ti["density"], mat_ti["color"], doc
    )
    
    # Acceleration grids
    grids = []
    for i in range(3):
        z = z_pos + length * 0.6 + i * 20
        grid = create_hollow_cylinder(
            f"{name}_Grid{i+1}", r, r - 5, 2, z,
            "Ti6Al4V", mat_ti["density"], mat_ti["color"], doc
        )
        grids.append(grid)
    
    # Nozzle
    nozzle_shape = Part.makeCone(r, r * 1.5, length * 0.4, App.Vector(0, 0, z_pos + length * 0.6))
    nozzle = doc.addObject("Part::Feature", f"{name}_Nozzle")
    nozzle.Shape = nozzle_shape
    set_material(nozzle, "Ti6Al4V", mat_ti["density"], mat_ti["color"])
    
    return body, grids, nozzle

def create_plasma_thruster(name, diameter, length, z_pos, doc):
    """
    Create VASIMR-style plasma thruster
    """
    r = diameter / 2.0
    
    # Main chamber
    mat_inconel = PARAMS["materials"]["Inconel625"]
    chamber = create_cylinder(
        f"{name}_Chamber", r, length, z_pos,
        "Inconel625", mat_inconel["density"], mat_inconel["color"], doc
    )
    
    # RF heating coils
    coils = []
    for i in range(4):
        z = z_pos + length * 0.2 + i * (length * 0.6 / 4)
        coil = create_torus(
            f"{name}_RFCoil{i+1}", r + 20, 15,
            App.Vector(0, 0, z),
            "CFRP", PARAMS["materials"]["CFRP"]["density"],
            PARAMS["materials"]["CFRP"]["color"], doc
        )
        coils.append(coil)
    
    # Magnetic nozzle
    mag_nozzle = Part.makeCone(r, r * 2, length * 0.5, App.Vector(0, 0, z_pos + length))
    nozzle = doc.addObject("Part::Feature", f"{name}_MagNozzle")
    nozzle.Shape = mag_nozzle
    set_material(nozzle, "Ti6Al4V", PARAMS["materials"]["Ti6Al4V"]["density"],
                 PARAMS["materials"]["Ti6Al4V"]["color"])
    
    return chamber, coils, nozzle

# ============================================================================
# SPACECRAFT COMPONENTS
# ============================================================================

def create_habitat_module(name, diameter, length, z_pos, wall_thickness, doc):
    """
    Create pressurized habitat module with radiation shielding
    """
    r_outer = diameter / 2.0
    r_inner = r_outer - wall_thickness
    
    # Main pressure vessel
    mat_al = PARAMS["materials"]["Al6061-T6"]
    hull = create_hollow_cylinder(
        f"{name}_Hull", r_outer, r_inner, length, z_pos,
        "Al6061-T6", mat_al["density"], mat_al["color"], doc
    )
    
    # End caps (spherical)
    cap1 = Part.makeSphere(r_outer, App.Vector(0, 0, z_pos))
    cap1_inner = Part.makeSphere(r_inner, App.Vector(0, 0, z_pos))
    cap1_shape = refine(cap1.cut(cap1_inner))
    
    cap2 = Part.makeSphere(r_outer, App.Vector(0, 0, z_pos + length))
    cap2_inner = Part.makeSphere(r_inner, App.Vector(0, 0, z_pos + length))
    cap2_shape = refine(cap2.cut(cap2_inner))
    
    cap1_obj = doc.addObject("Part::Feature", f"{name}_Cap1")
    cap1_obj.Shape = cap1_shape
    set_material(cap1_obj, "Al6061-T6", mat_al["density"], mat_al["color"])
    
    cap2_obj = doc.addObject("Part::Feature", f"{name}_Cap2")
    cap2_obj.Shape = cap2_shape
    set_material(cap2_obj, "Al6061-T6", mat_al["density"], mat_al["color"])
    
    # Water shield layer
    water_shield = create_water_shield(
        f"{name}_WaterShield", r_outer + 100, r_outer, length, z_pos, doc
    )
    
    return hull, cap1_obj, cap2_obj, water_shield

def create_fuel_tanks(name, diameter, length, count, spacing, z_start, doc):
    """
    Create cryogenic fuel tanks with insulation
    """
    tanks = []
    r = diameter / 2.0
    mat_inconel = PARAMS["materials"]["Inconel625"]
    
    for i in range(count):
        angle = (2 * math.pi * i) / count
        x = spacing * math.cos(angle)
        y = spacing * math.sin(angle)
        
        # Inner tank
        tank = create_cylinder(
            f"{name}_Tank{i+1}", r, length, z_start,
            "Inconel625", mat_inconel["density"], mat_inconel["color"], doc
        )
        tank.Placement.Base = App.Vector(x, y, z_start)
        
        # Insulation layer
        insul = create_hollow_cylinder(
            f"{name}_Insulation{i+1}", r + 80, r, length, z_start,
            "Polyethylene", PARAMS["materials"]["Polyethylene"]["density"],
            PARAMS["materials"]["Polyethylene"]["color"], doc
        )
        insul.Placement.Base = App.Vector(x, y, z_start)
        
        tanks.append((tank, insul))
    
    return tanks

def create_heat_radiators(name, count, length, width, thickness, base_radius, z_pos, doc):
    """
    Create deployable heat radiator panels
    """
    radiators = []
    mat_cfrp = PARAMS["materials"]["CFRP"]
    
    for i in range(count):
        angle = (2 * math.pi * i) / count
        x = base_radius * math.cos(angle)
        y = base_radius * math.sin(angle)
        
        # Radiator panel
        panel = create_box(
            f"{name}_Radiator{i+1}", length, width, thickness,
            App.Vector(x, y, z_pos),
            "CFRP", mat_cfrp["density"], mat_cfrp["color"], doc
        )
        
        # Rotate to face outward
        panel.Placement.Rotation = App.Rotation(App.Vector(0, 0, 1), math.degrees(angle))
        
        radiators.append(panel)
    
    return radiators

def create_solar_panels(name, count, length, width, thickness, base_radius, z_pos, doc):
    """
    Create deployable solar panel arrays
    """
    panels = []
    mat_cfrp = PARAMS["materials"]["CFRP"]
    
    for i in range(count):
        angle = (2 * math.pi * i) / count
        x = base_radius * math.cos(angle)
        y = base_radius * math.sin(angle)
        
        panel = create_box(
            f"{name}_SolarPanel{i+1}", length, width, thickness,
            App.Vector(x, y, z_pos),
            "CFRP", mat_cfrp["density"], (0.1, 0.1, 0.3), doc
        )
        
        panel.Placement.Rotation = App.Rotation(App.Vector(0, 0, 1), math.degrees(angle))
        panels.append(panel)
    
    return panels

def create_communication_dish(name, diameter, depth, z_pos, doc):
    """
    Create parabolic communication dish
    """
    # Simplified as a cone section
    r = diameter / 2.0
    
    # Dish surface
    dish_shape = Part.makeCone(r, r * 0.1, depth, App.Vector(0, 0, z_pos))
    dish = doc.addObject("Part::Feature", f"{name}_Dish")
    dish.Shape = dish_shape
    mat_al = PARAMS["materials"]["Al6061-T6"]
    set_material(dish, "Al6061-T6", mat_al["density"], mat_al["color"])
    
    # Support structure
    support = create_cylinder(
        f"{name}_Support", 20, depth * 2, z_pos - depth,
        "Ti6Al4V", PARAMS["materials"]["Ti6Al4V"]["density"],
        PARAMS["materials"]["Ti6Al4V"]["color"], doc
    )
    
    return dish, support

def create_docking_port(name, diameter, length, z_pos, doc):
    """
    Create docking port mechanism
    """
    r = diameter / 2.0
    mat_ti = PARAMS["materials"]["Ti6Al4V"]
    
    # Main ring
    ring = create_hollow_cylinder(
        f"{name}_Ring", r, r - 30, length, z_pos,
        "Ti6Al4V", mat_ti["density"], mat_ti["color"], doc
    )
    
    # Capture mechanism (simplified)
    capture = create_torus(
        f"{name}_Capture", r - 15, 10,
        App.Vector(0, 0, z_pos + length/2),
        "Ti6Al4V", mat_ti["density"], mat_ti["color"], doc
    )
    
    return ring, capture

# ============================================================================
# MAIN ASSEMBLY FUNCTION
# ============================================================================
def build_advanced_spacecraft(params):
    """
    Main function to build complete spacecraft with all systems
    """
    doc = get_or_create_doc()
    doc.Objects[:] = []  # Clear existing objects
    
    App.Console.PrintMessage("="*60 + "\n")
    App.Console.PrintMessage("Building Advanced Spacecraft with Radiation Shielding\n")
    App.Console.PrintMessage("="*60 + "\n")
    
    components = {}
    z_current = 0.0
    
    # 1. Main spacecraft body with multi-layer shielding
    App.Console.PrintMessage("Creating main body structure...\n")
    body_sections = params["body_sections"]
    body_parts = []
    
    for i, (length, diameter) in enumerate(body_sections):
        r = diameter / 2.0
        wall = params["body_wall_thickness"]
        
        section = create_hollow_cylinder(
            f"Body_Section{i+1}", r, r - wall, length, z_current,
            "Al6061-T6", params["materials"]["Al6061-T6"]["density"],
            params["materials"]["Al6061-T6"]["color"], doc
        )
        body_parts.append(section)
        z_current += length
    
    components["body"] = body_parts
    body_length = z_current
    
    # 2. Radiation shielding layers
    App.Console.PrintMessage("Creating radiation shielding layers...\n")
    shield_layers, final_radius = create_multilayer_shield(
        "RadShield", 
        max([d/2 for _, d in body_sections]) + 50,
        body_length, 0.0,
        params["shield_layers"], doc
    )
    components["radiation_shields"] = shield_layers
    
    # 3. Whipple shield for micrometeorite protection
    App.Console.PrintMessage("Creating Whipple shield...\n")
    whipple = create_whipple_shield(
        "Whipple", final_radius + 100, body_length, 0.0,
        params["whipple_layers"], params["whipple_spacing"],
        params["whipple_thickness"], doc
    )
    components["whipple_shield"] = whipple
    
    # 4. Magnetic field coils
    App.Console.PrintMessage("Creating magnetic deflection coils...\n")
    mag_coils = create_magnetic_shield_coils(
        "MagneticShield", final_radius + 400,
        params["mag_coil_count"], params["mag_coil_thickness"],
        params["mag_coil_spacing"], 0.0, doc
    )
    components["magnetic_coils"] = mag_coils
    
    # 5. Propulsion system
    App.Console.PrintMessage(f"Creating {params['propulsion_type']} propulsion system...\n")
    if params["propulsion_type"] == "fusion":
        reactor_z = body_length + 200
        reactor_parts = create_fusion_reactor(
            "FusionReactor", params["reactor_diameter"],
            params["reactor_length"], reactor_z,
            params["reactor_shield_thickness"], doc
        )
        components["propulsion"] = reactor_parts
    elif params["propulsion_type"] == "ion":
        thruster_z = body_length + 200
        thruster_parts = create_ion_thruster(
            "IonThruster", 600, 1000, thruster_z, doc
        )
        components["propulsion"] = thruster_parts
    else:  # plasma
        plasma_z = body_length + 200
        plasma_parts = create_plasma_thruster(
            "PlasmaThruster", 700, 1200, plasma_z, doc
        )
        components["propulsion"] = plasma_parts
    
    # 6. Habitat module
    App.Console.PrintMessage("Creating habitat module...\n")
    habitat_z = body_length * 0.3
    habitat_parts = create_habitat_module(
        "Habitat", params["habitat_diameter"],
        params["habitat_length"], habitat_z,
        params["habitat_wall_thickness"], doc
    )
    components["habitat"] = habitat_parts
    
    # 7. Fuel tanks
    App.Console.PrintMessage("Creating cryogenic fuel tanks...\n")
    fuel_tanks = create_fuel_tanks(
        "FuelTank", params["fuel_tank_diameter"],
        params["fuel_tank_length"], params["fuel_tank_count"],
        max([d/2 for _, d in body_sections]) + 800,
        body_length * 0.5, doc
    )
    components["fuel_tanks"] = fuel_tanks
    
    # 8. Heat radiators
    App.Console.PrintMessage("Creating heat radiators...\n")
    radiators = create_heat_radiators(
        "HeatRadiator", params["radiator_count"],
        params["radiator_length"], params["radiator_width"],
        params["radiator_thickness"],
        max([d/2 for _, d in body_sections]) + 1200,
        body_length * 0.4, doc
    )
    components["radiators"] = radiators
    
    # 9. Solar panels
    App.Console.PrintMessage("Creating solar panel arrays...\n")
    solar_panels = create_solar_panels(
        "SolarArray", params["solar_panel_count"],
        params["solar_panel_length"], params["solar_panel_width"],
        params["solar_panel_thickness"],
        max([d/2 for _, d in body_sections]) + 1500,
        body_length * 0.6, doc
    )
    components["solar_panels"] = solar_panels
    
    # 10. Communication dish
    App.Console.PrintMessage("Creating communication system...\n")
    comm_dish = create_communication_dish(
        "CommDish", params["comm_dish_diameter"],
        params["comm_dish_depth"], body_length + 100, doc
    )
    components["communication"] = comm_dish
    
    # 11. Docking port
    App.Console.PrintMessage("Creating docking port...\n")
    docking = create_docking_port(
        "DockingPort", 400, 200, -200, doc
    )
    components["docking"] = docking
    
    # 12. Thermal Protection System (if enabled)
    if params["tps_enabled"]:
        App.Console.PrintMessage("Creating Thermal Protection System...\n")
        # TPS on forward section
        tps_shield = create_ablative_shield(
            "TPS_Forward", max([d/2 for _, d in body_sections]) + 200,
            300, -300, params["tps_thickness"], doc
        )
        components["tps"] = tps_shield
    
    # Calculate total mass
    App.Console.PrintMessage("\n" + "="*60 + "\n")
    App.Console.PrintMessage("Calculating spacecraft mass...\n")
    total_mass = 0.0
    
    for category, items in components.items():
        category_mass = 0.0
        if isinstance(items, (list, tuple)):
            for item in items:
                if isinstance(item, (list, tuple)):
                    for subitem in item:
                        if hasattr(subitem, 'Shape'):
                            category_mass += calculate_mass(subitem)
                elif hasattr(item, 'Shape'):
                    category_mass += calculate_mass(item)
        elif hasattr(items, 'Shape'):
            category_mass += calculate_mass(items)
        
        total_mass += category_mass
        App.Console.PrintMessage(f"  {category}: {category_mass:.2f} kg\n")
    
    App.Console.PrintMessage(f"\nTOTAL SPACECRAFT MASS: {total_mass:.2f} kg ({total_mass/1000:.2f} tonnes)\n")
    App.Console.PrintMessage("="*60 + "\n")
    
    doc.recompute()
    Gui.SendMsgToActiveView("ViewFit")
    
    return components, total_mass

# ============================================================================
# ANALYSIS FUNCTIONS
# ============================================================================
def calculate_radiation_dose(shield_layers, radiation_type="GCR"):
    """
    Estimate radiation dose reduction through shield layers
    Simplified model - for detailed analysis use MCNP or similar
    """
    App.Console.PrintMessage("\nRadiation Shielding Analysis:\n")
    App.Console.PrintMessage("-" * 40 + "\n")
    
    # Simplified attenuation coefficients (1/cm)
    attenuation = {
        "Polyethylene": {"GCR": 0.15, "SPE": 0.20, "neutron": 0.25},
        "Aluminum": {"GCR": 0.08, "SPE": 0.12, "neutron": 0.05},
        "Lead": {"GCR": 0.05, "SPE": 0.08, "neutron": 0.03},
        "Water": {"GCR": 0.18, "SPE": 0.22, "neutron": 0.30},
    }
    
    initial_dose = 100.0  # Arbitrary units
    current_dose = initial_dose
    
    for layer in shield_layers:
        material = layer["material"]
        thickness_cm = layer["thickness"] / 10.0
        
        if material in attenuation:
            mu = attenuation[material].get(radiation_type, 0.1)
            reduction = math.exp(-mu * thickness_cm)
            current_dose *= reduction
            
            App.Console.PrintMessage(
                f"  {material} ({thickness_cm:.1f} cm): "
                f"{(1-reduction)*100:.1f}% reduction\n"
            )
    
    total_reduction = (1 - current_dose/initial_dose) * 100
    App.Console.PrintMessage(f"\nTotal dose reduction: {total_reduction:.1f}%\n")
    App.Console.PrintMessage(f"Remaining dose: {current_dose:.2f}% of initial\n")
    
    return current_dose, total_reduction

def estimate_delta_v(dry_mass, fuel_mass, isp):
    """
    Calculate delta-v using Tsiolkovsky rocket equation
    """
    if fuel_mass <= 0:
        return 0.0
    
    mass_ratio = (dry_mass + fuel_mass) / dry_mass
    g0 = 9.81  # m/s²
    delta_v = isp * g0 * math.log(mass_ratio)
    
    return delta_v

def thermal_analysis_summary(radiator_area, power_dissipation, temp_hot, temp_cold):
    """
    Simplified thermal analysis using Stefan-Boltzmann
    """
    sigma = 5.67e-8  # Stefan-Boltzmann constant W/(m²·K⁴)
    emissivity = 0.85  # Typical for spacecraft radiators
    
    # Convert temperatures to Kelvin
    T_hot = temp_hot + 273.15
    T_cold = temp_cold + 273.15
    
    # Radiative heat transfer
    q_rad = emissivity * sigma * radiator_area * (T_hot**4 - T_cold**4)
    
    App.Console.PrintMessage("\nThermal Analysis:\n")
    App.Console.PrintMessage("-" * 40 + "\n")
    App.Console.PrintMessage(f"Radiator area: {radiator_area:.2f} m²\n")
    App.Console.PrintMessage(f"Power dissipation: {power_dissipation/1000:.2f} kW\n")
    App.Console.PrintMessage(f"Radiative cooling: {q_rad/1000:.2f} kW\n")
    
    if q_rad >= power_dissipation:
        App.Console.PrintMessage("✓ Thermal system adequate\n")
    else:
        deficit = (power_dissipation - q_rad) / 1000
        App.Console.PrintMessage(f"✗ Additional cooling needed: {deficit:.2f} kW\n")
    
    return q_rad

# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================
def export_to_step(filename="AdvancedSpacecraft.step"):
    """Export all visible objects to STEP file"""
    doc = App.ActiveDocument
    if doc is None:
        App.Console.PrintError("No active document\n")
        return
    
    objs = [obj for obj in doc.Objects if hasattr(obj, 'Shape') and obj.ViewObject.Visibility]
    
    if not objs:
        App.Console.PrintError("No objects to export\n")
        return
    
    try:
        import ImportGui
        ImportGui.export(objs, filename)
        App.Console.PrintMessage(f"Exported to {filename}\n")
    except Exception as e:
        App.Console.PrintError(f"Export failed: {e}\n")

def generate_mass_report(components):
    """Generate detailed mass breakdown report"""
    report = []
    report.append("\n" + "="*60)
    report.append("SPACECRAFT MASS BREAKDOWN REPORT")
    report.append("="*60 + "\n")
    
    total = 0.0
    for category, items in components.items():
        cat_mass = 0.0
        report.append(f"\n{category.upper().replace('_', ' ')}:")
        report.append("-" * 40)
        
        if isinstance(items, (list, tuple)):
            for i, item in enumerate(items):
                if isinstance(item, (list, tuple)):
                    for j, subitem in enumerate(item):
                        if hasattr(subitem, 'Shape'):
                            m = calculate_mass(subitem)
                            cat_mass += m
                            report.append(f"  {subitem.Label}: {m:.2f} kg")
                elif hasattr(item, 'Shape'):
                    m = calculate_mass(item)
                    cat_mass += m
                    report.append(f"  {item.Label}: {m:.2f} kg")
        elif hasattr(items, 'Shape'):
            m = calculate_mass(items)
            cat_mass += m
            report.append(f"  {items.Label}: {m:.2f} kg")
        
        report.append(f"Subtotal: {cat_mass:.2f} kg")
        total += cat_mass
    
    report.append("\n" + "="*60)
    report.append(f"TOTAL MASS: {total:.2f} kg ({total/1000:.2f} tonnes)")
    report.append("="*60 + "\n")
    
    report_text = "\n".join(report)
    App.Console.PrintMessage(report_text)
    
    return report_text

# ============================================================================
# MAIN EXECUTION
# ============================================================================
if __name__ == "__main__":
    # Build the spacecraft
    components, total_mass = build_advanced_spacecraft(PARAMS)
    
    # Perform analyses
    calculate_radiation_dose(PARAMS["shield_layers"], "GCR")
    
    # Thermal analysis (example values)
    radiator_area = PARAMS["radiator_count"] * PARAMS["radiator_length"] * PARAMS["radiator_width"] * 1e-6
    thermal_analysis_summary(radiator_area, 500000, 400, -270)  # 500 kW, 400°C hot, -270°C cold
    
    # Delta-v estimate (example)
    fuel_mass = 10000  # kg
    isp = 3000  # seconds (fusion drive)
    dv = estimate_delta_v(total_mass, fuel_mass, isp)
    App.Console.PrintMessage(f"\nEstimated Delta-V: {dv/1000:.2f} km/s\n")
    
    # Generate mass report
    generate_mass_report(components)
    
    App.Console.PrintMessage("\n✓ Spacecraft construction complete!\n")
    App.Console.PrintMessage("Use export_to_step() to save the design\n\n")
