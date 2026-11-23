"""Thermal free-length bound for a round wire caught between two fixed contact locations."""
from math import hypot, pi, sqrt

def maximum_bow(chord_mm, temperature_C, alpha_per_K, cold_excess_mm=0.0):
    """Any excursion requires at least two straight legs from the endpoints to the apex."""
    length = (chord_mm + cold_excess_mm) * (1 + alpha_per_K * (temperature_C - 25.0))
    return sqrt(max(0.0, (length - chord_mm) * (length + chord_mm))) / 2

def screen(chord_mm, min_stop_mm, land_max_mm, wire_max_mm, roof_inward_mm, nominal_gap_mm):
    # 17.2 ppm/K exceeds the manufacturer's 20–750 °C typical value of 16 ppm/K.
    alpha = 17.2e-6
    rows=[]
    for T in (25.,450.,600.,750.):
        allowed_height = min_stop_mm - land_max_mm - wire_max_mm * (1+alpha*(T-25)) - roof_inward_mm
        max_slack = (2*hypot(chord_mm/2,allowed_height))/(1+alpha*(T-25))-chord_mm
        for excess in (0.,.005,.010,.020):
            bow = maximum_bow(chord_mm,T,alpha,excess)
            rows.append(dict(wire_C=T,cold_excess_mm=excess,bow_upper_mm=bow,
                upper_clearance_mm=allowed_height-bow,max_cold_excess_for_noncontact_mm=max_slack))
    return dict(contact_chord_mm=chord_mm,nominal_cold_crown_clearance_mm=nominal_gap_mm,
        minimum_installed_gap_mm=min_stop_mm,land_max_mm=land_max_mm,wire_max_mm=wire_max_mm,
        combined_roof_inward_mm=roof_inward_mm,alpha_per_K=alpha,
        pinned_Euler_critical_strain=pi*pi*(wire_max_mm/chord_mm)**2/16,rows=rows)
