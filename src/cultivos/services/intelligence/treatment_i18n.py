"""ES->EN lookup for seeded treatment (tratamiento) strings.

The DB stores treatment names in Spanish (the farmer-facing original). The intel
and effectiveness OUT models carry an optional ``tratamiento_en`` that the
frontend i18n ``loc()`` helper prefers when the UI is in English. This module is
that translate pass: an exact-match map over the known seeded techniques.

Unknown strings return ``None`` so callers (and ``loc()``) fall back to the
Spanish original rather than showing a blank — no regression for free-text
treatments that aren't in the map.
"""

# Keys are the exact Spanish strings seeded in scripts/seed_demo.py.
TREATMENT_EN: dict[str, str] = {
    "Aplicar estiercol composteado 6 ton/ha + sembrar rabano forrajero como descompactador biologico":
        "Apply composted manure 6 t/ha + sow forage radish as a biological subsoiler",
    "Aplicar ceniza de madera dura 800 kg/ha + caliza dolomitica 2 ton/ha":
        "Apply hardwood ash 800 kg/ha + dolomitic lime 2 t/ha",
    "Inocular con micorriza 2 kg/ha en primavera + te de composta cada 2 semanas":
        "Inoculate with mycorrhiza 2 kg/ha in spring + compost tea every 2 weeks",
    "Aplicar composta 5 ton/ha + planificar cultivo de cobertura de trebol post-cosecha":
        "Apply compost 5 t/ha + plan a clover cover crop post-harvest",
    "Aplicar composta madura 8 ton/ha + acolchado organico (mulch) de 10cm":
        "Apply mature compost 8 t/ha + 10 cm organic mulch",
    "Inocular con micorriza arbuscular 2kg/ha + te de composta semanal":
        "Inoculate with arbuscular mycorrhiza 2 kg/ha + weekly compost tea",
    "Instalar riego por goteo + biochar 3 ton/ha para retencion hidrica":
        "Install drip irrigation + biochar 3 t/ha for water retention",
    "Aplicar bocashi 4 ton/ha + siembra de frijol de abono intercalado":
        "Apply bokashi 4 t/ha + intercropped green-manure bean",
}


def treatment_en(es: str | None) -> str | None:
    """Return the English variant of a Spanish treatment string, or None."""
    if not es:
        return None
    return TREATMENT_EN.get(es.strip())
