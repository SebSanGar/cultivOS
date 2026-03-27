"""Seasonal TEK calendar alerts — Jalisco phenology + ancestral planting windows.

Pure function: date in, alerts out. No I/O, no side effects.

Jalisco agricultural calendar:
- Temporal (Jun-Oct): rainy season, main planting cycle
- Secas (Nov-May): dry season, irrigation-dependent crops

Milpa system (maiz + frijol + calabaza) follows ancestral Mesoamerican
timing: land preparation in March-April, planting with first rains May-June.
"""

from datetime import date


# Jalisco phenology calendar: (crop, alert_type, start_month, end_month, season, message)
# month_range is inclusive on both ends
PHENOLOGY_CALENDAR: list[dict] = [
    # --- Milpa system (ancestral Mesoamerican calendar) ---
    {
        "crop": "Milpa",
        "alert_type": "preparacion",
        "months": (3, 4),
        "season": "secas",
        "message": (
            "Ventana optima para preparar tierras de milpa "
            "(maiz + frijol + calabaza). Tradicion ancestral mesoamericana: "
            "limpiar terreno, incorporar abono verde y trazar surcos "
            "antes de las primeras lluvias."
        ),
        "month_label": "Mar-Abr",
    },
    # --- Temporal crops: prep in Mar-Apr, plant in May-Jun, harvest Oct-Nov ---
    {
        "crop": "Maiz",
        "alert_type": "preparacion",
        "months": (3, 4),
        "season": "secas",
        "message": (
            "Epoca ideal para preparar tierras de maiz. "
            "Incorporar composta o bocashi al suelo. "
            "La siembra sera en mayo-junio con las primeras lluvias."
        ),
        "month_label": "Mar-Abr",
    },
    {
        "crop": "Maiz",
        "alert_type": "siembra",
        "months": (5, 6),
        "season": "temporal",
        "message": (
            "Ventana de siembra de maiz de temporal. "
            "Sembrar cuando el suelo tenga humedad de las primeras lluvias. "
            "Profundidad: 5-7 cm, distancia entre plantas: 25-30 cm."
        ),
        "month_label": "May-Jun",
    },
    {
        "crop": "Maiz",
        "alert_type": "cosecha",
        "months": (10, 11),
        "season": "temporal",
        "message": (
            "Periodo de cosecha de maiz. Verificar que la mazorca "
            "este seca (grano duro al presionar). Secar al sol si "
            "la humedad es mayor al 14%."
        ),
        "month_label": "Oct-Nov",
    },
    {
        "crop": "Frijol",
        "alert_type": "preparacion",
        "months": (3, 4),
        "season": "secas",
        "message": (
            "Preparar tierras para frijol. Como leguminosa, fija "
            "nitrogeno al suelo — ideal despues de maiz o sorgo. "
            "Inocular semilla con Rhizobium antes de sembrar."
        ),
        "month_label": "Mar-Abr",
    },
    {
        "crop": "Frijol",
        "alert_type": "siembra",
        "months": (5, 6),
        "season": "temporal",
        "message": (
            "Ventana de siembra de frijol de temporal. "
            "En sistema milpa, sembrar 15 dias despues del maiz. "
            "Profundidad: 3-5 cm."
        ),
        "month_label": "May-Jun",
    },
    {
        "crop": "Calabaza",
        "alert_type": "preparacion",
        "months": (3, 4),
        "season": "secas",
        "message": (
            "Preparar tierras para calabaza. En sistema milpa, "
            "la calabaza cubre el suelo reduciendo evaporacion "
            "y suprimiendo malezas — la tercera hermana."
        ),
        "month_label": "Mar-Abr",
    },
    {
        "crop": "Calabaza",
        "alert_type": "siembra",
        "months": (5, 6),
        "season": "temporal",
        "message": (
            "Ventana de siembra de calabaza. En milpa, sembrar "
            "al mismo tiempo que el frijol. Distancia: 2-3 metros "
            "entre plantas para permitir expansion de guias."
        ),
        "month_label": "May-Jun",
    },
    {
        "crop": "Chile",
        "alert_type": "preparacion",
        "months": (3, 4),
        "season": "secas",
        "message": (
            "Iniciar almacigos de chile en semillero protegido. "
            "Transplantar al campo en mayo cuando pase riesgo de heladas. "
            "Preparar tutores para variedades altas."
        ),
        "month_label": "Mar-Abr",
    },
    {
        "crop": "Chile",
        "alert_type": "siembra",
        "months": (5, 6),
        "season": "temporal",
        "message": (
            "Ventana para transplantar chile al campo definitivo. "
            "Asegurar riego inicial si las lluvias no han iniciado. "
            "Aplicar mulch organico al pie de planta."
        ),
        "month_label": "May-Jun",
    },
    {
        "crop": "Sorgo",
        "alert_type": "siembra",
        "months": (6, 7),
        "season": "temporal",
        "message": (
            "Ventana de siembra de sorgo de temporal. "
            "Cultivo resistente a sequia, alternativa al maiz "
            "en zonas con precipitacion limitada."
        ),
        "month_label": "Jun-Jul",
    },
    # --- Secas crops ---
    {
        "crop": "Garbanzo",
        "alert_type": "preparacion",
        "months": (10, 10),
        "season": "temporal",
        "message": (
            "Preparar tierras para garbanzo de invierno. "
            "Aprovechar humedad residual del temporal. "
            "Garbanzo fija nitrogeno — excelente rotacion despues de maiz."
        ),
        "month_label": "Oct",
    },
    {
        "crop": "Garbanzo",
        "alert_type": "siembra",
        "months": (11, 12),
        "season": "secas",
        "message": (
            "Ventana de siembra de garbanzo. Sembrar en suelo "
            "con humedad residual del temporal. Profundidad: 8-10 cm. "
            "No requiere riego si hay humedad almacenada."
        ),
        "month_label": "Nov-Dic",
    },
    {
        "crop": "Garbanzo",
        "alert_type": "cosecha",
        "months": (3, 4),
        "season": "secas",
        "message": (
            "Periodo de cosecha de garbanzo. Cosechar cuando "
            "las vainas esten secas y amarillas. Secar al sol "
            "2-3 dias antes de almacenar."
        ),
        "month_label": "Mar-Abr",
    },
    # --- Perennials ---
    {
        "crop": "Aguacate",
        "alert_type": "cosecha",
        "months": (10, 3),
        "season": "temporal",
        "message": (
            "Temporada de cosecha de aguacate. Cortar con tijeras "
            "dejando 1 cm de pedunculo. Manejar con cuidado para "
            "evitar golpes que causan oxidacion."
        ),
        "month_label": "Oct-Mar",
    },
    {
        "crop": "Aguacate",
        "alert_type": "mantenimiento",
        "months": (4, 5),
        "season": "secas",
        "message": (
            "Epoca de poda de formacion y limpieza del aguacate. "
            "Eliminar ramas secas y chupones. Aplicar pasta "
            "cicatrizante organica en cortes grandes."
        ),
        "month_label": "Abr-May",
    },
    {
        "crop": "Agave",
        "alert_type": "siembra",
        "months": (6, 8),
        "season": "temporal",
        "message": (
            "Ventana de plantacion de hijuelos de agave. "
            "Plantar con las primeras lluvias para asegurar "
            "enraizamiento. Distancia: 2.5-3 metros entre plantas."
        ),
        "month_label": "Jun-Ago",
    },
    {
        "crop": "Cana de azucar",
        "alert_type": "cosecha",
        "months": (11, 5),
        "season": "secas",
        "message": (
            "Temporada de zafra (cosecha de cana). Cortar cuando "
            "el contenido de azucar sea optimo (>14 Brix). "
            "La zona Costa Sur de Jalisco es region canera principal."
        ),
        "month_label": "Nov-May",
    },
    {
        "crop": "Nopal",
        "alert_type": "mantenimiento",
        "months": (3, 4),
        "season": "secas",
        "message": (
            "Epoca ideal para poda de nopal y plantacion de nuevas "
            "pencas. Cortar pencas maduras para consumo o venta. "
            "Dejar secar cortes 3-5 dias antes de plantar."
        ),
        "month_label": "Mar-Abr",
    },
]


def _month_in_range(month: int, start: int, end: int) -> bool:
    """Check if month falls within range, handling year-wrapping (e.g. Oct-Mar)."""
    if start <= end:
        return start <= month <= end
    else:
        # Wraps around year boundary (e.g. 10-3 means Oct through Mar)
        return month >= start or month <= end


def _classify_current_season(month: int) -> str:
    """Classify current month into Jalisco season."""
    if 6 <= month <= 10:
        return "temporal"
    return "secas"


def generate_seasonal_alerts(reference_date: date | None = None) -> list[dict]:
    """Generate seasonal TEK calendar alerts for Jalisco crops.

    Pure function: takes a reference date (defaults to today),
    returns a list of active alerts based on the Jalisco phenology
    calendar and ancestral planting traditions.

    Each alert contains:
        - crop: crop name
        - alert_type: preparacion | siembra | cosecha | mantenimiento
        - message: actionable Spanish-language guidance
        - season: temporal | secas
        - month_range: human-readable month range
    """
    if reference_date is None:
        reference_date = date.today()

    month = reference_date.month
    alerts = []

    for entry in PHENOLOGY_CALENDAR:
        start_month, end_month = entry["months"]
        if _month_in_range(month, start_month, end_month):
            alerts.append({
                "crop": entry["crop"],
                "alert_type": entry["alert_type"],
                "message": entry["message"],
                "season": entry["season"],
                "month_range": entry["month_label"],
            })

    return alerts
