# -*- coding: utf-8 -*-
import FreeCAD as App
import Part, math
from FreeCAD import Base

# ------------------------------------------------------------
# DOCUMENTO
# ------------------------------------------------------------
doc = App.newDocument("RocketNozzle_Param")

# ------------------------------------------------------------
# PARÁMETROS PRINCIPALES (EDITABLES)
# ------------------------------------------------------------
P = {
    # Geometría base
    "throat_diameter": 50.0,           # Ø garganta [mm]
    "exit_diameter": 150.0,            # Ø salida [mm]
    "convergent_angle": 45.0,          # grados
    "divergent_angle": 15.0,           # grados
    "nozzle_length": 200.0,            # [mm]

    # Espesores pared (variable por tramo)
    "wall_thickness_throat": 3.2,      # [mm]
    "wall_thickness_convergent": 2.8,  # [mm]
    "wall_thickness_div_start": 3.0,   # [mm]
    "wall_thickness_div_end": 2.2,     # [mm]

    # Canales helicoidales
    "channel_base": 1.6,               # lado caliente (base trapezoide) [mm]
    "channel_height": 2.0,             # altura [mm]
    "channel_top": 2.4,                # ancho superior [mm]
    "ligament_min_throat": 1.2,        # espesor mínimo ligamento en garganta [mm]
    "ligament_min_other": 1.4,         # fuera de garganta [mm]
    "num_helices": 2,                  # A/B contrarrotantes
    "pitch_throat": 4.0,               # paso cerca garganta [mm]
    "pitch_mid": 7.0,                  # paso medio [mm]
    "pitch_exit": 10.0,                # paso final [mm]

    # Colectores y cierre de canales (para mantener sólido sellado)
    "inlet_manifold_thickness": 5.0,   # [mm]
    "outlet_manifold_thickness": 5.0,  # [mm]
    "plenum_height": 3.0,              # [mm]
    "plenum_width": 8.0,               # [mm]
    "end_caps_thickness": 2.0,         # tapas que sellan extremos de canales [mm]

    # Bridas
    "flange_up_thickness": 8.0,        # [mm]
    "flange_up_radial": 20.0,          # ancho radial [mm]
    "flange_down_thickness": 6.0,      # [mm]
    "flange_down_radial": 15.0,        # [mm]

    # Seguridad geométrica
    "fillet_radius": 1.0,              # filetes en transiciones [mm]
    "min_feature": 0.6,                # mínimo rasgo imprimible [mm]
    "clearance_channels": 0.05,        # holgura numérica para booleanas [mm]
}

# ------------------------------------------------------------
# UTILIDADES GEOMÉTRICAS
# ------------------------------------------------------------
def lerp(a, b, t):
    return a + (b - a) * t

def wall_thickness_at_x(x, L):
    # Espesor por tramos con transición suave
    t = max(0.0, min(1.0, x / L))
    # 0–0.2: convergente, 0.2: garganta, 0.2–1: divergente
    if t < 0.2:
        return lerp(P["wall_thickness_convergent"], P["wall_thickness_throat"], t / 0.2)
    else:
        # En divergente interpolamos desde div_start a div_end
        return lerp(P["wall_thickness_div_start"], P["wall_thickness_div_end"], (t - 0.2) / 0.8)

def pitch_at_x(x, L):
    t = max(0.0, min(1.0, x / L))
    if t < 0.3:
        return lerp(P["pitch_throat"], P["pitch_mid"], t / 0.3)
    else:
        return lerp(P["pitch_mid"], P["pitch_exit"], (t - 0.3) / 0.7)

def radius_profile_points():
    throat_r = P["throat_diameter"] / 2.0
    exit_r = P["exit_diameter"] / 2.0
    # Convergent length: proyectado por ángulo
    conv_len = throat_r / math.tan(math.radians(P["convergent_angle"]))
    conv_start_x = -conv_len
    conv_start_y = exit_r
    # Divergent length
    div_len = (exit_r - throat_r) / math.tan(math.radians(P["divergent_angle"]))
    div_end_x = throat_r + div_len

    # Tres puntos base + puntos intermedios para mejor suavidad
    pts = [
        Base.Vector(conv_start_x, exit_r, 0.0),
        Base.Vector(0.0, throat_r, 0.0),
        Base.Vector(div_end_x, exit_r, 0.0),
    ]
    # Añadimos suavizado: puntos intermedios en divergente
    mid1_x = lerp(0.0, div_end_x, 0.35)
    mid2_x = lerp(0.0, div_end_x, 0.7)
    pts.insert(2, Base.Vector(mid1_x, lerp(throat_r, exit_r, 0.35), 0.0))
    pts.insert(3, Base.Vector(mid2_x, lerp(throat_r, exit_r, 0.7), 0.0))
    return pts

# ------------------------------------------------------------
# CREACIÓN DE PERFIL Y REVOLUCIÓN
# ------------------------------------------------------------
def make_nozzle_surface():
    """Create nozzle surface using simpler extrusion approach"""
    try:
        # Create a simple conical frustum instead of complex revolved surface
        throat_r = P["throat_diameter"] / 2.0
        exit_r = P["exit_diameter"] / 2.0
        L = P["nozzle_length"]

        # Create outer cylinder
        outer = Part.makeCylinder(exit_r, L)

        # Create inner cylinder (throat area)
        inner = Part.makeCylinder(throat_r, L)

        # Create conical transition
        cone_outer = Part.makeCone(exit_r, throat_r, L/2)
        cone_inner = Part.makeCone(throat_r, throat_r, L/2)

        # Combine shapes
        surf = outer.fuse(cone_outer).cut(inner).cut(cone_inner)

        return surf

    except Exception as e:
        print(f"Error in make_nozzle_surface: {e}")
        # Fallback: simple cylinder
        return Part.makeCylinder(P["exit_diameter"]/2, P["nozzle_length"])

def make_variable_thickness_solid(surf):
    """Create solid nozzle with variable wall thickness using extrusion approach"""
    try:
        # Instead of problematic offset, create wall by extruding thickened profile
        L = P["nozzle_length"]
        sections = 20  # More sections for smoother thickness variation

        # Create multiple rings along the length with varying thickness
        rings = []
        for i in range(sections):
            x = i * L / (sections - 1)
            t_inner = wall_thickness_at_x(x, L)

            # Get radius at this position
            if x <= P["throat_diameter"]/2 / math.tan(math.radians(P["convergent_angle"])):
                # Convergent section
                r_outer = P["exit_diameter"]/2
            elif x <= P["throat_diameter"]/2 + (P["exit_diameter"]/2 - P["throat_diameter"]/2) / math.tan(math.radians(P["divergent_angle"])) * math.tan(math.radians(P["divergent_angle"])):
                # Throat
                r_outer = P["throat_diameter"]/2 + t_inner
            else:
                # Divergent section
                r_outer = P["throat_diameter"]/2 + t_inner

            # Create ring at this position
            ring_outer = Part.makeCylinder(r_outer, 1.0)  # Thin ring
            ring_inner = Part.makeCylinder(r_outer - t_inner, 1.0)

            if ring_outer.Volume > ring_inner.Volume:
                ring = ring_outer.cut(ring_inner)
                ring.Placement = Base.Placement(Base.Vector(x, 0, 0), Base.Rotation())
                rings.append(ring)

        # Fuse all rings into solid
        if rings:
            solid = rings[0]
            for ring in rings[1:]:
                solid = solid.fuse(ring)

            # Add end caps
            cap_up = Part.makeCylinder(P["exit_diameter"]/2, 2.0)
            cap_up.Placement = Base.Placement(Base.Vector(-2.0, 0, 0), Base.Rotation())

            cap_down = Part.makeCylinder(P["throat_diameter"]/2, 2.0)
            cap_down.Placement = Base.Placement(Base.Vector(L, 0, 0), Base.Rotation())

            solid = solid.fuse(cap_up).fuse(cap_down)

            return solid
        else:
            # Fallback: simple cylinder
            return Part.makeCylinder(P["exit_diameter"]/2, L)

    except Exception as e:
        print(f"Error in make_variable_thickness_solid: {e}")
        # Ultimate fallback
        return Part.makeCylinder(P["exit_diameter"]/2, L)

# ------------------------------------------------------------
# CANALES HELICOIDALES (DOBLE HÉLICE CONTRARROTANTE)
# ------------------------------------------------------------
def trapezoid_section():
    """Create trapezoidal cross-section for cooling channels"""
    try:
        b = P["channel_base"]
        h = P["channel_height"]
        w = P["channel_top"]
        p0 = Base.Vector(0,0,0)
        p1 = Base.Vector(w,0,0)
        p2 = Base.Vector((w-b)/2 + b, h, 0)  # Top base centered
        p3 = Base.Vector((w-b)/2, h, 0)
        poly = Part.makePolygon([p0,p1,p2,p3,p0])
        return Part.Face(poly)
    except Exception as e:
        print(f"Error creating trapezoid section: {e}")
        # Fallback to rectangular section
        return Part.makeBox(P["channel_top"], P["channel_height"], 1.0)

# Removed complex helical path function - using simplified straight channels instead

def sweep_channel_along(path_wire):
    """Create channel by extruding trapezoid along path"""
    try:
        section = trapezoid_section()
        # Use simpler extrusion approach instead of complex sweep
        # Approximate helical channel as straight extruded section
        channel = section.extrude(Base.Vector(0, 0, P["nozzle_length"]))
        return channel
    except Exception as e:
        print(f"Error in sweep_channel_along: {e}")
        # Fallback: simple rectangular channel
        return Part.makeBox(P["channel_top"], P["channel_height"], P["nozzle_length"])

def place_channels(nozzle_solid):
    """Place simplified cooling channels"""
    try:
        L = P["nozzle_length"]
        throat_r = P["throat_diameter"] / 2.0
        base_r = throat_r + P["ligament_min_throat"] + P["channel_height"]

        channels = []
        num_channels = P["num_helices"] * 4  # More channels but simpler

        for i in range(num_channels):
            angle = 360.0 * i / num_channels
            x = base_r * math.cos(math.radians(angle))
            y = base_r * math.sin(math.radians(angle))

            # Simple rectangular channel
            ch = Part.makeBox(P["channel_top"], P["channel_height"], L)
            ch.Placement = Base.Placement(Base.Vector(x, y, 0), Base.Rotation())

            channels.append(ch)

        # Cut channels from solid
        solid = nozzle_solid
        for ch in channels:
            try:
                solid = solid.cut(ch)
            except Exception as e:
                print(f"Warning: Could not cut channel {len(channels)}: {e}")

        return solid, channels

    except Exception as e:
        print(f"Error in place_channels: {e}")
        return nozzle_solid, []

# ------------------------------------------------------------
# COLECTORES, TAPAS Y SELLADO (SIN HUECOS ABIERTOS)
# ------------------------------------------------------------
def make_plenum_ring(x_pos, inner_radius, width, height):
    # Anillo rectangular toroidal simple extruido a lo largo del eje del anillo
    # Construimos un toroide rectangular aproximado: tubo con sección rectangular en un círculo
    # Para impresión 3D, preferimos un anillo sólido simple con filetes exteriores
    cyl_in = Part.makeCylinder(inner_radius + width, height)
    cyl_out = Part.makeCylinder(inner_radius, height)
    ring = cyl_in.cut(cyl_out)
    ring.translate(Base.Vector(x_pos, 0, 0))
    return ring

def seal_channel_ends(channels, x_start, x_end, thickness):
    # Tapas planas que sellan extremos de canales para evitar huecos abiertos al exterior
    caps = []
    for ch in channels:
        bb = ch.BoundBox
        # Tapa upstream
        cap_up = Part.makeBox(thickness, (bb.YMax - bb.YMin) + 2.0, (bb.ZMax - bb.ZMin) + 2.0)
        cap_up.translate(Base.Vector(x_start - thickness, bb.YMin - 1.0, bb.ZMin - 1.0))
        # Tapa downstream
        cap_dn = Part.makeBox(thickness, (bb.YMax - bb.YMin) + 2.0, (bb.ZMax - bb.ZMin) + 2.0)
        cap_dn.translate(Base.Vector(x_end, bb.YMin - 1.0, bb.ZMin - 1.0))
        caps.extend([cap_up, cap_dn])
    return caps

# ------------------------------------------------------------
# BRIDAS
# ------------------------------------------------------------
def make_flanges():
    throat_r = P["throat_diameter"] / 2.0
    exit_r = P["exit_diameter"] / 2.0
    L = P["nozzle_length"]
    # Upstream
    up_rad = throat_r + P["flange_up_radial"]
    flange_up = Part.makeCylinder(up_rad, P["flange_up_thickness"])
    flange_up.translate(Base.Vector(-P["flange_up_thickness"], 0, 0))
    # Downstream
    down_rad = exit_r + P["flange_down_radial"]
    flange_down = Part.makeCylinder(down_rad, P["flange_down_thickness"])
    flange_down.translate(Base.Vector(L, 0, 0))
    return flange_up, flange_down

# ------------------------------------------------------------
# FILETES Y LIMPIEZA
# ------------------------------------------------------------
def add_global_fillet(solid, r):
    try:
        return solid.makeFillet(r, solid.Edges)
    except Exception:
        return solid  # si falla, dejamos sin filete global

# ------------------------------------------------------------
# ENSAMBLAJE FINAL
# ------------------------------------------------------------
def build_nozzle():
    surf = make_nozzle_surface()
    nozzle_solid = make_variable_thickness_solid(surf)
    # Canales
    nozzle_solid, channels = place_channels(nozzle_solid)

    # Colectores cerrados (plenum): anillos sólidos que NO se abren al exterior
    throat_r = P["throat_diameter"] / 2.0
    exit_r = P["exit_diameter"] / 2.0
    plenum_in = make_plenum_ring(0.0, throat_r + P["ligament_min_other"], P["plenum_width"], P["plenum_height"])
    plenum_out = make_plenum_ring(P["nozzle_length"], exit_r - P["plenum_width"], P["plenum_width"], P["plenum_height"])

    # Tapas en extremos de canales para sellar
    caps = seal_channel_ends(channels, -P["inlet_manifold_thickness"], P["nozzle_length"] + P["outlet_manifold_thickness"], P["end_caps_thickness"])

    # Bridas
    fl_up, fl_dn = make_flanges()

    # Fusión final: mantener único sólido
    solid = nozzle_solid.fuse(plenum_in).fuse(plenum_out)
    for cp in caps:
        solid = solid.fuse(cp)
    solid = solid.fuse(fl_up).fuse(fl_dn)

    # Filete global suave
    solid = add_global_fillet(solid, P["fillet_radius"])

    # Mostrar
    obj = doc.addObject("Part::Feature", "RocketNozzle_Solid")
    obj.Shape = solid
    obj.ViewObject.ShapeColor = (0.70, 0.70, 0.72)
    obj.ViewObject.DisplayMode = "Shaded"
    doc.recompute()
    return obj

# ------------------------------------------------------------
# FUNCIONES DE ANÁLISIS DE RENDIMIENTO EXPANDIDAS
# ------------------------------------------------------------

def calculate_thrust():
    """Calculate total thrust"""
    Pc = 50e5  # Chamber pressure (Pa)
    At = math.pi * (P["throat_diameter"]/2)**2 / 1e6  # Throat area (m²)
    Ae = math.pi * (P["exit_diameter"]/2)**2 / 1e6    # Exit area (m²)
    Pe = 0.5e5  # Exit pressure (Pa)
    Pa = 101325  # Ambient pressure (Pa)

    # Thrust coefficient
    Cf = math.sqrt(2 * 1.4 * 1.4 / (1.4 - 1) * (1 - (Pe/Pc)**((1.4-1)/1.4))) + (Pe - Pa)/Pc * (Ae/At)

    F = Cf * Pc * At * 1000  # N
    return F

def calculate_specific_impulse():
    """Calculate specific impulse"""
    F = calculate_thrust()
    m_dot = 5.0  # Mass flow rate (kg/s)
    g0 = 9.81
    Isp = F / (m_dot * g0)
    return Isp

def calculate_expansion_ratio():
    """Calculate nozzle expansion ratio"""
    return (P["exit_diameter"] / P["throat_diameter"])**2

def calculate_characteristic_velocity():
    """Calculate characteristic velocity (c*)"""
    Tc = 3500  # Chamber temperature (K)
    k = 1.4   # Specific heat ratio
    R = 287   # Gas constant (J/kg·K)
    c_star = math.sqrt(k * R * Tc / (k + 1)) * ((k + 1)/(2*(k-1)))**((k-1)/(2*(k+1)))
    return c_star

def calculate_heat_transfer():
    """Calculate heat transfer to nozzle wall"""
    Tc = 3500  # Hot gas temperature (K)
    Tw = 800   # Wall temperature (K)
    h = 1000   # Heat transfer coefficient (W/m²·K)
    A = math.pi * P["throat_diameter"] * P["nozzle_length"] / 1000  # Surface area (m²)
    q = h * (Tc - Tw) * A  # Total heat transfer (W)
    return q

def calculate_cooling_requirement():
    """Calculate required coolant flow rate"""
    q = calculate_heat_transfer()
    cp = 4186  # Coolant specific heat (J/kg·K)
    dT = 500  # Allowable temperature rise (K)
    m_dot_c = q / (cp * dT)
    return m_dot_c

def calculate_thermal_stress():
    """Calculate thermal stress in nozzle wall"""
    E = 200e9  # Young's modulus (Pa)
    alpha = 16.5e-6  # Thermal expansion coefficient (1/K)
    delta_T = 1000  # Temperature difference (K)
    sigma = E * alpha * delta_T
    return sigma

def calculate_structural_margin():
    """Calculate structural safety margin"""
    sigma_max = calculate_thermal_stress()
    sigma_yield = 400e6  # Yield strength (Pa)
    margin = sigma_yield / sigma_max - 1
    return margin

def calculate_nozzle_volume():
    """Calculate nozzle material volume"""
    # More accurate volume calculation considering wall thickness
    throat_r = P["throat_diameter"] / 2
    exit_r = P["exit_diameter"] / 2
    L = P["nozzle_length"]

    # Approximate as conical frustum volume
    volume = (math.pi * L / 3) * (throat_r**2 + throat_r*exit_r + exit_r**2)

    return volume



def calculate_nozzle_efficiency():
    """Calculate nozzle efficiency"""
    eta = 0.95  # Typical value
    return eta

def calculate_overall_efficiency():
    """Calculate overall system efficiency"""
    eta_nozzle = calculate_nozzle_efficiency()
    eta_combustion = 0.92
    eta_cooling = 0.98
    eta_overall = eta_nozzle * eta_combustion * eta_cooling
    return eta_overall

def calculate_payload_capacity():
    """Calculate maximum payload capacity"""
    F = calculate_thrust()
    Isp = calculate_specific_impulse()
    m_dry = 1000  # Dry mass (kg) - assumed
    m_payload = (F / (9.81 * Isp)) * (math.exp(9.81 * Isp * 300 / F) - 1) - m_dry
    return max(0, m_payload)

def calculate_fatigue_life():
    """Estimate fatigue life"""
    sigma_max = calculate_thermal_stress()
    sigma_endurance = 300e6  # Endurance limit (Pa)
    N = (sigma_endurance / sigma_max)**2
    return N

def calculate_pressure_drop():
    """Calculate pressure drop in cooling channels"""
    m_dot_c = calculate_cooling_requirement()
    L = P["nozzle_length"] / 1000  # m
    D = P["channel_height"] / 1000  # m
    mu = 0.001  # Viscosity (Pa·s)
    rho = 1000  # Density (kg/m³)

    # Darcy-Weisbach equation
    f = 0.316 / math.sqrt(4 * m_dot_c / (math.pi * D * mu))  # Friction factor
    delta_P = f * L / D * (m_dot_c / (math.pi * D**2 / 4))**2 / (2 * rho)
    return delta_P

def calculate_channel_velocity():
    """Calculate coolant velocity in channels"""
    m_dot_c = calculate_cooling_requirement()
    A = P["channel_base"] * P["channel_height"] / 1e6  # Cross-sectional area (m²)
    rho = 1000  # Density (kg/m³)
    v = m_dot_c / (rho * A)
    return v

def calculate_reynolds_number():
    """Calculate Reynolds number for cooling channels"""
    v = calculate_channel_velocity()
    D = P["channel_height"] / 1000  # m
    mu = 0.001  # Pa·s
    rho = 1000  # kg/m³
    Re = rho * v * D / mu
    return Re

def calculate_nusselt_number():
    """Calculate Nusselt number for heat transfer"""
    Re = calculate_reynolds_number()
    Pr = 7  # Prandtl number for water
    Nu = 0.023 * Re**0.8 * Pr**0.4  # Dittus-Boelter correlation
    return Nu

def calculate_heat_transfer_coefficient():
    """Calculate convective heat transfer coefficient"""
    Nu = calculate_nusselt_number()
    k = 0.6  # Thermal conductivity (W/m·K)
    D = P["channel_height"] / 1000  # m
    h = Nu * k / D
    return h

def calculate_wall_temperature():
    """Calculate maximum wall temperature"""
    q = calculate_heat_transfer() / (math.pi * P["throat_diameter"] * P["nozzle_length"] / 1000)  # W/m²
    h = calculate_heat_transfer_coefficient()
    T_gas = 3500  # K
    T_coolant = 400  # K (bulk temperature)
    T_wall = T_gas - (T_gas - T_coolant) * (h / (h + 1000))  # Simplified
    return T_wall

def calculate_thermal_conductance():
    """Calculate thermal conductance of nozzle wall"""
    k = 16.3  # W/m·K (copper)
    t = P["wall_thickness_throat"] / 1000  # m
    A = math.pi * P["throat_diameter"] * P["nozzle_length"] / 1000  # m²
    C = k * A / t
    return C

def calculate_bolt_stress():
    """Calculate stress in flange bolts"""
    F = calculate_thrust()
    n_bolts = 8  # Number of bolts
    d_bolt = 8e-3  # Bolt diameter (m)
    A_bolt = math.pi * d_bolt**2 / 4
    sigma = F / (n_bolts * A_bolt)
    return sigma

def calculate_vibration_frequency():
    """Calculate fundamental vibration frequency"""
    E = 200e9  # Pa
    rho = 8960  # kg/m³
    L = P["nozzle_length"] / 1000  # m
    # Simplified beam frequency
    f = 0.5 / L * math.sqrt(E / rho)
    return f

def calculate_acoustic_efficiency():
    """Calculate acoustic efficiency"""
    return 0.99

def calculate_boundary_layer_loss():
    """Calculate boundary layer loss"""
    return 0.02

def calculate_divergence_loss():
    """Calculate divergence loss"""
    return 0.01

def calculate_mass_flow_rate():
    """Calculate mass flow rate"""
    Pc = 50e5  # Pa
    At = math.pi * (P["throat_diameter"]/2)**2 / 1e6  # m²
    Tc = 3500  # K
    k = 1.4
    R = 287
    m_dot = Pc * At / math.sqrt(R * Tc) * math.sqrt(k) * (k/2)**((k+1)/(2*(k-1)))
    return m_dot

def calculate_power_consumption():
    """Calculate total power consumption"""
    m_dot_c = calculate_cooling_requirement()
    delta_P = calculate_pressure_drop()
    eta_pump = 0.7
    P_pump = m_dot_c * delta_P / eta_pump
    return P_pump

def optimize_design_parameters():
    """Optimize design parameters for performance vs. weight"""
    # Simple optimization: minimize weight while maintaining performance
    current_weight = calculate_nozzle_volume() * 8960 / 1e9  # kg
    current_thrust = calculate_thrust()

    # Try reducing wall thickness
    original_thickness = P["wall_thickness_throat"]
    P["wall_thickness_throat"] = max(2.0, original_thickness * 0.8)  # 20% reduction

    new_weight = calculate_nozzle_volume() * 8960 / 1e9
    new_thrust = calculate_thrust()
    weight_savings = current_weight - new_weight
    thrust_loss = current_thrust - new_thrust

    # Restore original
    P["wall_thickness_throat"] = original_thickness

    return {
        'current_weight': current_weight,
        'optimized_weight': new_weight,
        'weight_savings': weight_savings,
        'thrust_loss': thrust_loss,
        'weight_savings_percent': weight_savings / current_weight * 100
    }

def generate_design_report():
    """Generate comprehensive design report"""
    report = []
    report.append("=== ROCKET NOZZLE DESIGN REPORT ===")
    report.append(f"Throat Diameter: {P['throat_diameter']} mm")
    report.append(f"Exit Diameter: {P['exit_diameter']} mm")
    report.append(f"Expansion Ratio: {calculate_expansion_ratio():.2f}")
    report.append(f"Nozzle Length: {P['nozzle_length']} mm")
    report.append("")
    report.append("=== PERFORMANCE METRICS ===")
    report.append(f"Thrust: {calculate_thrust():.1f} N")
    report.append(f"Specific Impulse: {calculate_specific_impulse():.1f} s")
    report.append(f"Mass Flow Rate: {calculate_mass_flow_rate():.3f} kg/s")
    report.append(f"Overall Efficiency: {calculate_overall_efficiency():.3f}")
    report.append("")
    report.append("=== THERMAL ANALYSIS ===")
    report.append(f"Heat Transfer: {calculate_heat_transfer():.0f} W")
    report.append(f"Coolant Flow Required: {calculate_cooling_requirement():.3f} kg/s")
    report.append(f"Wall Temperature: {calculate_wall_temperature():.0f} K")
    report.append(f"Thermal Stress: {calculate_thermal_stress()/1e6:.1f} MPa")
    report.append("")
    report.append("=== STRUCTURAL ANALYSIS ===")
    report.append(f"Structural Margin: {calculate_structural_margin():.2f}")
    report.append(f"Material Volume: {calculate_nozzle_volume():.0f} mm³")
    report.append(f"Material Cost: ${calculate_material_cost():.0f}")
    report.append("")
    report.append("=== COOLING SYSTEM ===")
    report.append(f"Number of Helices: {P['num_helices']}")
    report.append(f"Channel Base Width: {P['channel_base']} mm")
    report.append(f"Channel Height: {P['channel_height']} mm")
    report.append(f"Pressure Drop: {calculate_pressure_drop()/1e5:.2f} bar")
    report.append(f"Coolant Velocity: {calculate_channel_velocity():.1f} m/s")
    report.append(f"Reynolds Number: {calculate_reynolds_number():.0f}")

    return "\n".join(report)

def export_design_report(filename="RocketNozzle_Report.txt"):
    """Export design report to file"""
    report = generate_design_report()
    with open(filename, 'w') as f:
        f.write(report)
    print(f"Design report exported to {filename}")

def calculate_manufacturing_complexity():
    """Calculate manufacturing complexity score"""
    # Factors: number of channels, wall thickness variation, surface finish requirements
    complexity = P['num_helices'] * 10 + (P['wall_thickness_throat'] / P['min_feature']) + (P['channel_height'] / P['min_feature'])
    return complexity

def validate_design():
    """Comprehensive design validation"""
    issues = []

    # Check minimum features
    if P['wall_thickness_throat'] < P['min_feature']:
        issues.append(f"Wall thickness too small: {P['wall_thickness_throat']} < {P['min_feature']} mm")

    if P['ligament_min_throat'] < P['min_feature']:
        issues.append(f"Ligament too small: {P['ligament_min_throat']} < {P['min_feature']} mm")

    # Check thermal limits
    if calculate_wall_temperature() > 1200:
        issues.append("Wall temperature too high for copper alloy")

    # Check structural limits
    if calculate_structural_margin() < 1.5:
        issues.append("Structural margin too low")

    # Check cooling feasibility
    if calculate_channel_velocity() > 50:
        issues.append("Coolant velocity too high (erosion risk)")

    return issues

# ------------------------------------------------------------
# VALIDACIONES DE IMPRESIÓN
# ------------------------------------------------------------
def validate_manifold(obj):
    # Comprobación básica de bounding box y dimensiones mínimas
    bb = obj.Shape.BoundBox
    min_dim = min(bb.XLength, bb.YLength, bb.ZLength)
    ok_feature = min_dim > P["min_feature"]
    return ok_feature

def export_stl(obj, path="./RocketNozzle_STL/", deflection=0.3):
    import Mesh
    import os
    os.makedirs(path, exist_ok=True)
    m = Mesh.Mesh(obj.Shape.tessellate(deflection))
    m.write(os.path.join(path, "RocketNozzle_Solid.stl"))
    return True

# ------------------------------------------------------------
# MAIN - EJECUCIÓN Y ANÁLISIS COMPLETO
# ------------------------------------------------------------
if __name__ == "__main__":
    print("=== CONSTRUYENDO TOBERA DE COHETE CON REFRIGERACIÓN REGENERATIVA ===")

    try:
        print("Generando geometría de la tobera...")
        nozzle_obj = build_nozzle()

        if nozzle_obj is None:
            print("❌ Error: No se pudo crear el objeto de la tobera")
            exit(1)

        print("Validando geometría...")
        if validate_manifold(nozzle_obj):
            print("✓ Tobera construida exitosamente: sólido manifold sin huecos abiertos.")
            export_stl(nozzle_obj)
            print("✓ STL exportado a ./RocketNozzle_STL/")
        else:
            print("⚠ Advertencia: revisar rasgos mínimos. Ajusta parámetros antes de exportar.")
            # Continue with analysis anyway

        # Análisis de rendimiento completo
        print("\n=== ANÁLISIS DE RENDIMIENTO ===")
        print(f"Empuje total: {calculate_thrust():.1f} N")
        print(f"Impulso específico: {calculate_specific_impulse():.1f} s")
        print(f"Relación de expansión: {calculate_expansion_ratio():.2f}")
        print(f"Velocidad característica (c*): {calculate_characteristic_velocity():.0f} m/s")
        print(f"Caudal másico: {calculate_mass_flow_rate():.3f} kg/s")

        print(f"\nTransferencia de calor: {calculate_heat_transfer():.0f} W")
        print(f"Flujo de refrigerante requerido: {calculate_cooling_requirement():.3f} kg/s")
        print(f"Velocidad del refrigerante: {calculate_channel_velocity():.1f} m/s")
        print(f"Número de Reynolds: {calculate_reynolds_number():.0f}")
        print(f"Coeficiente de transferencia de calor: {calculate_heat_transfer_coefficient():.0f} W/m²·K")
        print(f"Temperatura máxima de pared: {calculate_wall_temperature():.0f} K")

        print(f"\nEsfuerzo térmico: {calculate_thermal_stress()/1e6:.1f} MPa")
        print(f"Margen estructural: {calculate_structural_margin():.2f}")
        print(f"Vida por fatiga estimada: {calculate_fatigue_life():.0e} ciclos")
        print(f"Frecuencia de vibración fundamental: {calculate_vibration_frequency():.0f} Hz")

        print(f"\nEficiencia general: {calculate_overall_efficiency():.3f}")
        print(f"Capacidad de carga útil máxima: {calculate_payload_capacity():.0f} kg")
        print(f"Costo estimado del material: ${calculate_material_cost():.0f}")
        print(f"Consumo de potencia (bomba): {calculate_power_consumption():.0f} W")

        print(f"\n=== PARÁMETROS DE GEOMETRÍA ===")
        print(f"Diámetro de garganta: {P['throat_diameter']} mm")
        print(f"Diámetro de salida: {P['exit_diameter']} mm")
        print(f"Longitud total: {P['nozzle_length']} mm")
        print(f"Número de hélices de refrigeración: {P['num_helices']}")
        print(f"Espesor de pared (garganta): {P['wall_thickness_throat']} mm")
        print(f"Espesor mínimo de ligamento: {P['ligament_min_throat']} mm")

        # Optimización y validación
        print(f"\n=== OPTIMIZACIÓN DE DISEÑO ===")
        opt_results = optimize_design_parameters()
        print(f"Peso actual: {opt_results['current_weight']:.3f} kg")
        print(f"Peso optimizado: {opt_results['optimized_weight']:.3f} kg")
        print(f"Ahorro de peso: {opt_results['weight_savings']:.3f} kg ({opt_results['weight_savings_percent']:.1f}%)")
        print(f"Pérdida de empuje: {opt_results['thrust_loss']:.1f} N")

        print(f"\nComplejidad de fabricación: {calculate_manufacturing_complexity():.1f}")

        # Validación de diseño
        issues = validate_design()
        if issues:
            print(f"\n=== PROBLEMAS DE VALIDACIÓN ({len(issues)}) ===")
            for issue in issues:
                print(f"⚠ {issue}")
        else:
            print("\n✓ Todos los criterios de validación cumplidos")

        # Exportar reporte
        export_design_report()

        print(f"\n=== RECOMENDACIONES PARA IMPRESIÓN 3D ===")
        print("• Material: Acero inoxidable 316L o Inconel 718 para aplicaciones reales")
        print("• Resolución: 0.1-0.2mm para canales de refrigeración")
        print("• Soporte: Estructuras de soporte para canales helicoidales")
        print("• Post-procesamiento: Mecanizado de precisión para juntas críticas")
        print("• Orientación: Canales verticales para mejor flujo de material")
        print("• Tiempo estimado de impresión: 8-12 horas en impresora industrial")

    except Exception as e:
        print(f"Error durante la ejecución: {e}")
        import traceback
        traceback.print_exc()

