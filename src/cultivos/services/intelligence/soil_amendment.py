"""Soil amendment calculator — organic-only prescriptions from soil analysis.

Pure function: soil values in → amendment prescriptions out.
All amendments are organic/regenerative — no synthetic fertilizers.
"""


_COSTS = {
    "cal_agricola": 3.0,
    "azufre": 25.0,
    "composta": 1.5,
    "harina_sangre": 35.0,
    "harina_hueso": 20.0,
    "ceniza_madera": 5.0,
}


def calculate_soil_amendments(
    current_ph: float,
    target_ph: float,
    current_om_pct: float = 3.0,
    target_om_pct: float = 3.0,
    current_n_ppm: float = 30.0,
    target_n_ppm: float = 30.0,
    current_p_ppm: float = 20.0,
    target_p_ppm: float = 20.0,
    current_k_ppm: float = 150.0,
    target_k_ppm: float = 150.0,
) -> dict:
    """Calculate organic soil amendments to reach target values.

    Returns dict with:
      - amendments: list of {name, kg_per_ha, reason_es, cost_mxn_per_ha, organic}
      - summary_es: human-readable summary in Spanish
      - total_cost_mxn_per_ha: total estimated cost
    """
    amendments: list[dict] = []

    # pH correction
    ph_delta = target_ph - current_ph
    if ph_delta > 0.3:
        kg = round(ph_delta * 1000, 0)
        amendments.append({
            "name": "Cal agricola",
            "kg_per_ha": kg,
            "reason_es": f"Elevar pH de {current_ph:.1f} a {target_ph:.1f} (suelo acido)",
            "cost_mxn_per_ha": round(kg * _COSTS["cal_agricola"], 2),
            "organic": True,
        })
    elif ph_delta < -0.3:
        kg = round(abs(ph_delta) * 150, 0)
        amendments.append({
            "name": "Azufre elemental",
            "kg_per_ha": kg,
            "reason_es": f"Reducir pH de {current_ph:.1f} a {target_ph:.1f} (suelo alcalino)",
            "cost_mxn_per_ha": round(kg * _COSTS["azufre"], 2),
            "organic": True,
        })

    # Organic matter
    om_delta = target_om_pct - current_om_pct
    if om_delta > 0.5:
        kg = round(om_delta * 10000, 0)
        amendments.append({
            "name": "Composta madura",
            "kg_per_ha": kg,
            "reason_es": f"Aumentar materia organica de {current_om_pct:.1f}% a {target_om_pct:.1f}%",
            "cost_mxn_per_ha": round(kg * _COSTS["composta"], 2),
            "organic": True,
        })

    # Nitrogen
    n_delta = target_n_ppm - current_n_ppm
    if n_delta > 5:
        kg_n_needed = n_delta * 2
        kg = round(kg_n_needed / 0.12, 0)
        amendments.append({
            "name": "Harina de sangre",
            "kg_per_ha": kg,
            "reason_es": f"Aportar nitrogeno: de {current_n_ppm:.0f} a {target_n_ppm:.0f} ppm",
            "cost_mxn_per_ha": round(kg * _COSTS["harina_sangre"], 2),
            "organic": True,
        })

    # Phosphorus
    p_delta = target_p_ppm - current_p_ppm
    if p_delta > 3:
        kg = round((p_delta * 2) / 0.15, 0)
        amendments.append({
            "name": "Harina de hueso",
            "kg_per_ha": kg,
            "reason_es": f"Aportar fosforo: de {current_p_ppm:.0f} a {target_p_ppm:.0f} ppm",
            "cost_mxn_per_ha": round(kg * _COSTS["harina_hueso"], 2),
            "organic": True,
        })

    # Potassium
    k_delta = target_k_ppm - current_k_ppm
    if k_delta > 10:
        kg = round((k_delta * 2) / 0.05, 0)
        amendments.append({
            "name": "Ceniza de madera",
            "kg_per_ha": kg,
            "reason_es": f"Aportar potasio: de {current_k_ppm:.0f} a {target_k_ppm:.0f} ppm",
            "cost_mxn_per_ha": round(kg * _COSTS["ceniza_madera"], 2),
            "organic": True,
        })

    total_cost = round(sum(a["cost_mxn_per_ha"] for a in amendments), 2)

    if not amendments:
        summary = "El suelo cumple con los valores objetivo. No se requieren enmiendas."
    else:
        names = ", ".join(a["name"] for a in amendments)
        summary = (
            f"Se recomiendan {len(amendments)} enmiendas organicas: {names}. "
            f"Costo estimado: ${total_cost:,.0f} MXN/ha."
        )

    return {
        "amendments": amendments,
        "summary_es": summary,
        "total_cost_mxn_per_ha": total_cost,
    }
