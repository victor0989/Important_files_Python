import FreeCAD as App
import Part

def safe_fillet(shape, radius):
    """Apply fillet to shape edges safely."""
    try:
        return shape.makeFillet(radius, shape.Edges)
    except:
        return shape

def rot_to_x():
    """Rotation to align along x-axis."""
    return App.Rotation(App.Vector(0, 1, 0), 90)

def make_cone_x(height, r1, r2, cx, cy, cz):
    """Create a cone aligned along x-axis."""
    cone = Part.makeCone(r1, r2, height)
    cone.Placement = App.Placement(App.Vector(cx, cy, cz), rot_to_x())
    return cone

def make_cockpit():
    """Create angular cockpit with polygonal visor."""
    base = Part.makeBox(800, 600, 400)
    visor = Part.makeCone(0, 300, 200)
    visor.Placement = App.Placement(App.Vector(400, 300, 400), App.Rotation(App.Vector(0, 1, 0), 90))
    cockpit = base.fuse(visor)
    return safe_fillet(cockpit, 12.0)

def make_thruster_pair(cx, cy, cz):
    """Create vectorial thrusters like Sparrow."""
    nozzle = make_cone_x(300, 800, 600, cx, cy, cz)
    ring = Part.makeTorus(500, 60)
    ring.Placement = App.Placement(App.Vector(cx + 300, cy, cz), rot_to_x())
    thruster = nozzle.fuse(ring)
    return safe_fillet(thruster, 24.0)

def make_modular_panels(cx, cy, cz, count=6):
    """Create embedded modular panels."""
    panels = []
    for i in range(count):
        p = Part.makeBox(600, 40, 400)
        p.Placement = App.Placement(App.Vector(cx + i * 640, cy, cz), App.Rotation())
        panels.append(safe_fillet(p, 6.0))
    union = panels[0]
    for p in panels[1:]:
        union = union.fuse(p)
    return union

def make_energy_conduits(cx, cy, cz, length=2400):
    """Create visible energy conduits."""
    tube = Part.makeCylinder(60, length)
    tube.Placement = App.Placement(App.Vector(cx, cy, cz), rot_to_x())
    return safe_fillet(tube, 4.0)

def make_stylized_hull():
    """Create angular hull with Destiny silhouette."""
    # Base hull as a loft with trapezoidal profiles
    profile1 = Part.makePolygon([App.Vector(0, 0, 0), App.Vector(1200, 0, 0), App.Vector(1000, 600, 0), App.Vector(200, 600, 0)])
    profile2 = Part.makePolygon([App.Vector(0, 0, 2400), App.Vector(1000, 0, 2400), App.Vector(800, 500, 2400), App.Vector(200, 500, 2400)])
    hull = Part.makeLoft([profile1, profile2], True)
    return safe_fillet(hull, 20.0)

def make_solar_shield_layers(cx, cy, cz):
    """Create multi-layer solar shields with Destiny-style."""
    layers = []
    for i in range(5):
        layer = Part.makeCylinder(800 + i * 100, 50)
        layer.Placement = App.Placement(App.Vector(cx, cy, cz + i * 60), App.Rotation())
        layers.append(layer)
    shield = layers[0]
    for l in layers[1:]:
        shield = shield.fuse(l)
    return safe_fillet(shield, 10.0)

def build_destiny_probe():
    """Build the complete Destiny-style solar probe."""
    hull = make_stylized_hull()
    cockpit = make_cockpit()
    cockpit.Placement = App.Placement(App.Vector(200, 0, 200), App.Rotation())
    thrusters = make_thruster_pair(1200, -300, 600)
    thrusters_right = make_thruster_pair(1200, 300, 600)
    panels = make_modular_panels(0, -350, 800)
    conduits = make_energy_conduits(600, 0, 400)
    shield = make_solar_shield_layers(600, 0, 0)

    probe = hull.fuse(cockpit).fuse(thrusters).fuse(thrusters_right).fuse(panels).fuse(conduits).fuse(shield)

    # Set Destiny-style colors
    probe.ViewObject.ShapeColor = (0.1, 0.1, 0.1)  # Carbon matte exoskeleton
    cockpit.ViewObject.ShapeColor = (0.4, 0.4, 0.45)  # Titanium grey panels
    conduits.ViewObject.ShapeColor = (0.6, 0.7, 0.8)  # Iridescent thermal
    shield.ViewObject.ShapeColor = (0.88, 0.82, 0.60)  # Ablative ceramic

    return probe

# Execute the build
if __name__ == "__main__":
    doc = App.newDocument("Destiny_Solar_Probe")
    probe = build_destiny_probe()
    Part.show(probe)
    doc.recompute()
    # Export for Blender
    # probe.exportStl("destiny_probe.stl")  # Uncomment to export
