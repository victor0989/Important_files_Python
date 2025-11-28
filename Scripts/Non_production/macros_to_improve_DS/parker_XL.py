#!/usr/bin/env python3
"""
Parker XL - Advanced Solar Flare Shield Simulation and Analysis
Comprehensive toolkit for modeling solar flare protection systems for spacecraft
"""

import math
import random
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class RadiationType(Enum):
    """Types of solar radiation"""
    PROTONS = "protons"
    ELECTRONS = "electrons"
    HEAVY_IONS = "heavy_ions"
    X_RAYS = "x_rays"
    GAMMA_RAYS = "gamma_rays"

# Shield materials as dictionaries for easier access
SHIELD_MATERIALS = {
    "ALUMINUM": {"density": 2.7, "atomic_number": 13, "name": "Aluminum"},
    "TITANIUM": {"density": 4.5, "atomic_number": 22, "name": "Titanium"},
    "TUNGSTEN": {"density": 19.3, "atomic_number": 74, "name": "Tungsten"},
    "LEAD": {"density": 11.3, "atomic_number": 82, "name": "Lead"},
    "BORON_CARBIDE": {"density": 2.5, "atomic_number": 10.8, "name": "Boron Carbide"},
    "MULTILAYER_COMPOSITE": {"density": 3.2, "atomic_number": 15.5, "name": "Multilayer Composite"},
    "CARBON_COMPOSITE": {"density": 1.8, "atomic_number": 6.5, "name": "Carbon Composite"}
}

@dataclass
class SolarFlare:
    """Represents a solar flare event"""
    intensity: float  # Flare intensity in W/m²
    duration: float   # Duration in seconds
    peak_flux: float  # Peak particle flux (particles/cm²/s)
    radiation_type: RadiationType
    energy_spectrum: Dict[float, float]  # Energy (MeV) -> Flux

    def calculate_total_energy(self) -> float:
        """Calculate total energy released by the flare"""
        return self.intensity * self.duration

    def get_particle_flux_at_energy(self, energy_mev: float) -> float:
        """Get particle flux at specific energy level"""
        if energy_mev in self.energy_spectrum:
            return self.energy_spectrum[energy_mev]
        # Interpolate for missing energies
        energies = sorted(self.energy_spectrum.keys())
        if energy_mev < energies[0]:
            return self.energy_spectrum[energies[0]]
        if energy_mev > energies[-1]:
            return self.energy_spectrum[energies[-1]]

        for i in range(len(energies) - 1):
            if energies[i] <= energy_mev <= energies[i + 1]:
                e1, e2 = energies[i], energies[i + 1]
                f1, f2 = self.energy_spectrum[e1], self.energy_spectrum[e2]
                return f1 + (f2 - f1) * (energy_mev - e1) / (e2 - e1)
        return 0.0

class SolarShield:
    """Advanced solar shield with multiple protection layers"""

    def __init__(self, layers: List[Dict[str, any]]):
        """
        Initialize shield with multiple layers

        Args:
            layers: List of layer dictionaries with keys:
                   'material': ShieldMaterial enum
                   'thickness': thickness in cm
                   'density_override': optional density override
        """
        self.layers = layers
        self._validate_layers()

    def _validate_layers(self):
        """Validate layer configuration"""
        if not self.layers:
            raise ValueError("Shield must have at least one layer")

        for i, layer in enumerate(self.layers):
            required_keys = ['material', 'thickness']
            if not all(key in layer for key in required_keys):
                raise ValueError(f"Layer {i} missing required keys: {required_keys}")

            if layer['thickness'] <= 0:
                raise ValueError(f"Layer {i} thickness must be positive")

    def get_total_thickness(self) -> float:
        """Get total shield thickness in cm"""
        return sum(layer['thickness'] for layer in self.layers)

    def get_total_mass(self, area: float) -> float:
        """Calculate total mass for given area in kg"""
        total_mass = 0.0
        for layer in self.layers:
            material = layer['material']
            thickness = layer['thickness']
            density = layer.get('density_override', material['density'])
            volume = area * thickness / 100  # Convert cm to m for volume
            mass = density * volume
            total_mass += mass
        return total_mass

    def calculate_attenuation(self, energy_mev: float, radiation_type: RadiationType) -> float:
        """
        Calculate radiation attenuation factor (0-1, where 1 is complete attenuation)

        Args:
            energy_mev: Particle energy in MeV
            radiation_type: Type of radiation

        Returns:
            Attenuation factor (fraction of radiation blocked)
        """
        attenuation = 1.0

        for layer in self.layers:
            material = layer['material']
            thickness = layer['thickness']
            atomic_number = material['atomic_number']

            # Calculate mass attenuation coefficient based on radiation type
            if radiation_type == RadiationType.PROTONS:
                mu = self._proton_attenuation_coefficient(energy_mev, atomic_number)
            elif radiation_type == RadiationType.ELECTRONS:
                mu = self._electron_attenuation_coefficient(energy_mev, atomic_number)
            elif radiation_type == RadiationType.HEAVY_IONS:
                mu = self._heavy_ion_attenuation_coefficient(energy_mev, atomic_number)
            elif radiation_type in [RadiationType.X_RAYS, RadiationType.GAMMA_RAYS]:
                mu = self._photon_attenuation_coefficient(energy_mev, atomic_number)
            else:
                mu = 0.1  # Default attenuation

            density = layer.get('density_override', material['density'])
            mass_thickness = density * thickness  # g/cm²

            layer_attenuation = math.exp(-mu * mass_thickness)
            attenuation *= layer_attenuation

        return 1.0 - attenuation  # Convert to fraction blocked

    def _proton_attenuation_coefficient(self, energy_mev: float, atomic_number: float) -> float:
        """Calculate proton mass attenuation coefficient"""
        # Simplified Bethe-Bloch formula approximation
        if energy_mev < 1:
            return 100.0 / atomic_number
        elif energy_mev < 10:
            return 50.0 / atomic_number
        else:
            return 20.0 / atomic_number

    def _electron_attenuation_coefficient(self, energy_mev: float, atomic_number: float) -> float:
        """Calculate electron mass attenuation coefficient"""
        # Simplified for electrons
        return 10.0 * math.log(energy_mev + 1) / atomic_number

    def _heavy_ion_attenuation_coefficient(self, energy_mev: float, atomic_number: float) -> float:
        """Calculate heavy ion mass attenuation coefficient"""
        return 200.0 / (energy_mev * atomic_number)

    def _photon_attenuation_coefficient(self, energy_mev: float, atomic_number: float) -> float:
        """Calculate photon mass attenuation coefficient"""
        # Convert MeV to keV for photon calculations
        energy_kev = energy_mev * 1000
        if energy_kev < 100:
            return 100.0 * atomic_number
        else:
            return 10.0 * atomic_number / math.sqrt(energy_kev)

    def simulate_flare_impact(self, flare: SolarFlare, exposure_time: float) -> Dict[str, float]:
        """
        Simulate the impact of a solar flare on the shield

        Args:
            flare: SolarFlare object
            exposure_time: Exposure time in seconds

        Returns:
            Dictionary with impact metrics
        """
        results = {
            'total_radiation_blocked': 0.0,
            'radiation_transmitted': 0.0,
            'shield_temperature_increase': 0.0,
            'structural_integrity': 100.0,  # Percentage
            'estimated_lifetime_reduction': 0.0
        }

        # Calculate radiation transmission
        energies = list(flare.energy_spectrum.keys())
        for energy in energies:
            flux = flare.energy_spectrum[energy]
            attenuation = self.calculate_attenuation(energy, flare.radiation_type)

            blocked_flux = flux * attenuation * exposure_time
            transmitted_flux = flux * (1 - attenuation) * exposure_time

            results['total_radiation_blocked'] += blocked_flux
            results['radiation_transmitted'] += transmitted_flux

        # Calculate thermal effects
        absorbed_energy = results['total_radiation_blocked'] * 1.6e-13  # Convert to Joules
        shield_mass = self.get_total_mass(1.0)  # Assume 1 m² area
        specific_heat = 900  # J/kg/K for typical shield materials
        results['shield_temperature_increase'] = absorbed_energy / (shield_mass * specific_heat)

        # Estimate structural integrity reduction
        if results['shield_temperature_increase'] > 1000:
            results['structural_integrity'] = max(0, 100 - (results['shield_temperature_increase'] - 1000) / 10)
            results['estimated_lifetime_reduction'] = (100 - results['structural_integrity']) * 0.01

        return results

def generate_random_flare(intensity_class: str = 'M') -> SolarFlare:
    """
    Generate a random solar flare based on intensity class

    Args:
        intensity_class: 'C', 'M', or 'X' class flare

    Returns:
        SolarFlare object
    """
    # Base intensities for different classes (W/m²)
    base_intensities = {'C': 1e-6, 'M': 1e-5, 'X': 1e-4}

    if intensity_class not in base_intensities:
        intensity_class = 'M'

    base_intensity = base_intensities[intensity_class]
    intensity = base_intensity * random.uniform(0.1, 10.0)
    duration = random.uniform(600, 7200)  # 10 minutes to 2 hours
    peak_flux = intensity * 1e10  # Rough conversion

    # Generate energy spectrum
    energy_spectrum = {}
    for energy in [0.1, 1.0, 10.0, 100.0, 1000.0]:  # MeV
        flux = peak_flux * math.exp(-energy / 10.0) * random.uniform(0.5, 2.0)
        energy_spectrum[energy] = flux

    radiation_type = random.choice(list(RadiationType))

    return SolarFlare(
        intensity=intensity,
        duration=duration,
        peak_flux=peak_flux,
        radiation_type=radiation_type,
        energy_spectrum=energy_spectrum
    )

def optimize_shield_design(target_attenuation: float, max_mass: float,
                          area: float = 1.0) -> SolarShield:
    """
    Optimize shield design for target attenuation with mass constraint

    Args:
        target_attenuation: Desired attenuation factor (0-1)
        max_mass: Maximum allowed mass in kg
        area: Shield area in m²

    Returns:
        Optimized SolarShield object
    """
    # Start with simple aluminum shield
    layers = [{'material': SHIELD_MATERIALS["ALUMINUM"], 'thickness': 1.0}]

    shield = SolarShield(layers)

    # Iteratively adjust thickness
    while shield.get_total_mass(area) < max_mass:
        current_attenuation = shield.calculate_attenuation(10.0, RadiationType.PROTONS)

        if current_attenuation >= target_attenuation:
            break

        # Increase thickness
        shield.layers[0]['thickness'] *= 1.1

        if shield.get_total_mass(area) > max_mass:
            shield.layers[0]['thickness'] /= 1.1
            break

    return shield

def calculate_mission_risk(flares: List[SolarFlare], shield: SolarShield,
                          mission_duration: float, critical_dose: float) -> Dict[str, float]:
    """
    Calculate mission radiation risk

    Args:
        flares: List of expected solar flares
        shield: SolarShield object
        mission_duration: Mission duration in seconds
        critical_dose: Critical radiation dose in Sv

    Returns:
        Risk assessment dictionary
    """
    total_dose = 0.0
    max_temperature = 0.0

    for flare in flares:
        impact = shield.simulate_flare_impact(flare, flare.duration)
        total_dose += impact['radiation_transmitted'] * 1e-12  # Convert to Sv
        max_temperature = max(max_temperature, impact['shield_temperature_increase'])

    risk_level = min(100, (total_dose / critical_dose) * 100)

    return {
        'total_accumulated_dose': total_dose,
        'max_shield_temperature': max_temperature,
        'mission_risk_percentage': risk_level,
        'mission_success_probability': max(0, 100 - risk_level)
    }

def create_parker_probe_shield() -> SolarShield:
    """
    Create a shield design inspired by Parker Solar Probe

    Returns:
        SolarShield with multiple layers
    """
    layers = [
        {'material': SHIELD_MATERIALS["CARBON_COMPOSITE"], 'thickness': 2.0},
        {'material': SHIELD_MATERIALS["ALUMINUM"], 'thickness': 5.0},
        {'material': SHIELD_MATERIALS["TUNGSTEN"], 'thickness': 1.0},
        {'material': SHIELD_MATERIALS["MULTILAYER_COMPOSITE"], 'thickness': 3.0}
    ]

    return SolarShield(layers)

# Example usage and testing functions
def run_shield_analysis():
    """Run comprehensive shield analysis"""
    print("=== Parker XL Solar Shield Analysis ===\n")

    # Create Parker-inspired shield
    shield = create_parker_probe_shield()
    print(f"Shield Configuration:")
    print(f"Total Thickness: {shield.get_total_thickness():.2f} cm")
    print(f"Total Mass (1 m²): {shield.get_total_mass(1.0):.2f} kg\n")

    # Generate test flares
    flares = [generate_random_flare('M') for _ in range(5)]

    print("Testing against 5 random M-class flares:")
    for i, flare in enumerate(flares, 1):
        impact = shield.simulate_flare_impact(flare, flare.duration)
        print(f"Flare {i}:")
        print(".2f")
        print(".2f")
        print(".1f")
        print(".1f")
        print()

    # Mission risk assessment
    mission_risk = calculate_mission_risk(flares, shield, 365*24*3600, 1.0)  # 1 year, 1 Sv limit
    print("Mission Risk Assessment (1 year, 1 Sv limit):")
    print(".3f")
    print(".1f")
    print(".1f")
    print(".1f")

if __name__ == "__main__":
    run_shield_analysis()