"""Seasonal TEK calendar alerts — region-aware phenology + ancestral planting windows.

Pure function: date in, alerts out. No I/O, no side effects.

Jalisco agricultural calendar:
- Temporal (Jun-Oct): rainy season, main planting cycle
- Secas (Nov-May): dry season, irrigation-dependent crops

Ontario agricultural calendar:
- Spring prep (Mar-Apr): soil thaws, plan and prepare
- Growing (May-Sep): frost-free ~140 days, main planting and growth
- Fall harvest (Oct-Nov): harvest, cover crop planting
- Winter (Dec-Feb): dormant, snow cover benefits soil biology

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


# Ontario phenology calendar: short growing season (May-Sep), frost risk, corn-soy-wheat belt
ONTARIO_PHENOLOGY_CALENDAR: list[dict] = [
    # --- Spring preparation ---
    {
        "crop": "Corn (Field)",
        "alert_type": "preparacion",
        "months": (4, 5),
        "season": "spring_prep",
        "message": (
            "Preparar tierras para maiz de campo. Aplicar composta "
            "o estiercol composteado cuando el suelo este seco al tacto. "
            "No trabajar suelo humedo — riesgo de compactacion en arcillas glaciales."
        ),
        "month_label": "Apr-May",
    },
    {
        "crop": "Corn (Field)",
        "alert_type": "siembra",
        "months": (5, 6),
        "season": "growing",
        "message": (
            "Ventana de siembra de maiz. Sembrar cuando temperatura "
            "del suelo sea >10C a 5 cm de profundidad. Fecha optima: "
            "mayo 1-20 en suroeste de Ontario. Cada dia de retraso "
            "despues del 20 de mayo reduce rendimiento ~1%."
        ),
        "month_label": "May-Jun",
    },
    {
        "crop": "Corn (Field)",
        "alert_type": "cosecha",
        "months": (10, 11),
        "season": "fall_harvest",
        "message": (
            "Periodo de cosecha de maiz. Cosechar cuando humedad "
            "del grano sea <25% (ideal <20% para almacenamiento). "
            "Secar a 15.5% para almacenamiento seguro."
        ),
        "month_label": "Oct-Nov",
    },
    # --- Soybean ---
    {
        "crop": "Soybean",
        "alert_type": "preparacion",
        "months": (4, 5),
        "season": "spring_prep",
        "message": (
            "Preparar tierras para soya. Inocular semilla con "
            "Bradyrhizobium japonicum si es primer ano de soya "
            "en la parcela. Verificar pH del suelo (optimo 6.0-6.5)."
        ),
        "month_label": "Apr-May",
    },
    {
        "crop": "Soybean",
        "alert_type": "siembra",
        "months": (5, 6),
        "season": "growing",
        "message": (
            "Ventana de siembra de soya. Sembrar cuando suelo >12C. "
            "Fecha optima: mayo 10-31. Profundidad: 3-4 cm. "
            "Soya tolera siembra tardia mejor que maiz."
        ),
        "month_label": "May-Jun",
    },
    {
        "crop": "Soybean",
        "alert_type": "cosecha",
        "months": (9, 10),
        "season": "fall_harvest",
        "message": (
            "Periodo de cosecha de soya. Cosechar cuando vainas "
            "esten secas y semillas sueltas al agitar. Humedad "
            "optima de cosecha: 13-14%."
        ),
        "month_label": "Sep-Oct",
    },
    # --- Winter Wheat ---
    {
        "crop": "Winter Wheat",
        "alert_type": "siembra",
        "months": (9, 10),
        "season": "fall_harvest",
        "message": (
            "Ventana de siembra de trigo de invierno. Sembrar "
            "despues de cosecha de soya. Fecha optima: septiembre "
            "25 - octubre 10 en suroeste de Ontario. El trigo necesita "
            "establecer 3-4 hojas antes del invierno."
        ),
        "month_label": "Sep-Oct",
    },
    {
        "crop": "Winter Wheat",
        "alert_type": "mantenimiento",
        "months": (4, 5),
        "season": "spring_prep",
        "message": (
            "Evaluacion de sobrevivencia invernal del trigo. "
            "Verificar densidad de plantas al derretir la nieve. "
            "Aplicar fertilizante nitrogenado si stand es adecuado (>75%)."
        ),
        "month_label": "Apr-May",
    },
    {
        "crop": "Winter Wheat",
        "alert_type": "cosecha",
        "months": (7, 8),
        "season": "growing",
        "message": (
            "Periodo de cosecha de trigo de invierno. Cosechar "
            "cuando grano este duro y humedad <14.5%. Sembrar "
            "cultivo de cobertura inmediatamente despues si es posible."
        ),
        "month_label": "Jul-Aug",
    },
    # --- Apple ---
    {
        "crop": "Apple",
        "alert_type": "mantenimiento",
        "months": (3, 4),
        "season": "spring_prep",
        "message": (
            "Poda invernal de manzanos antes de brotacion. "
            "Aplicar aceite de dormancia para control de insectos "
            "(cochinillas, acaros). Primera aplicacion de azufre "
            "contra sarna (apple scab) en boton verde."
        ),
        "month_label": "Mar-Apr",
    },
    {
        "crop": "Apple",
        "alert_type": "cosecha",
        "months": (9, 10),
        "season": "fall_harvest",
        "message": (
            "Temporada de cosecha de manzana. Cosechar por variedad: "
            "Gala (agosto-septiembre), McIntosh y Empire (septiembre), "
            "Honeycrisp (octubre). Almacenar a 0-2C con humedad 90-95%."
        ),
        "month_label": "Sep-Oct",
    },
    # --- Grape ---
    {
        "crop": "Grape",
        "alert_type": "mantenimiento",
        "months": (4, 5),
        "season": "spring_prep",
        "message": (
            "Desatar vides y poda de primavera si no se hizo en "
            "invierno. Primera aplicacion preventiva de azufre contra "
            "powdery mildew cuando brotes tengan 15 cm."
        ),
        "month_label": "Apr-May",
    },
    {
        "crop": "Grape",
        "alert_type": "cosecha",
        "months": (9, 10),
        "season": "fall_harvest",
        "message": (
            "Vendimia en Ontario. Medir Brix semanalmente — cosechar "
            "tintas a 22-24 Brix, blancas a 20-22 Brix. Icewine: "
            "dejar racimos para cosecha en diciembre-enero a <-8C."
        ),
        "month_label": "Sep-Oct",
    },
    # --- Greenhouse Tomato ---
    {
        "crop": "Greenhouse Tomato",
        "alert_type": "mantenimiento",
        "months": (1, 12),
        "season": "growing",
        "message": (
            "Monitoreo continuo de invernadero. Mantener temperatura "
            "18-25C, humedad 65-80%. Vigilar trips, mosca blanca y "
            "botrytis. Podar chupones semanalmente."
        ),
        "month_label": "Year-round",
    },
    # --- Frost warnings ---
    {
        "crop": "All",
        "alert_type": "frost_warning",
        "months": (4, 5),
        "season": "spring_prep",
        "message": (
            "ALERTA DE HELADA — riesgo de helada tardia en Ontario. "
            "Fecha promedio de ultima helada: mayo 10-24 segun zona. "
            "Proteger plantulas y flores de frutales. No sembrar "
            "cultivos sensibles hasta despues de fecha segura."
        ),
        "month_label": "Apr-May",
    },
    {
        "crop": "All",
        "alert_type": "frost_warning",
        "months": (9, 10),
        "season": "fall_harvest",
        "message": (
            "ALERTA DE HELADA — riesgo de primera helada de otono. "
            "Fecha promedio: septiembre 25 - octubre 15 segun zona. "
            "Acelerar cosecha de cultivos sensibles. Cubrir "
            "hortalizas vulnerables si se pronostica helada."
        ),
        "month_label": "Sep-Oct",
    },
    # --- Cover crop window ---
    {
        "crop": "Cover Crop",
        "alert_type": "siembra",
        "months": (8, 9),
        "season": "growing",
        "message": (
            "Ventana optima para sembrar cultivos de cobertura "
            "despues de cosecha de trigo o grano temprano. "
            "Mezcla recomendada: trebol carmin + centeno + rabano "
            "forrajero. Sembrar antes de septiembre 15 para "
            "establecimiento adecuado antes del invierno."
        ),
        "month_label": "Aug-Sep",
    },
]


def _month_in_range(month: int, start: int, end: int) -> bool:
    """Check if month falls within range, handling year-wrapping (e.g. Oct-Mar)."""
    if start <= end:
        return start <= month <= end
    else:
        # Wraps around year boundary (e.g. 10-3 means Oct through Mar)
        return month >= start or month <= end


def _classify_current_season(month: int, region: str = "jalisco") -> str:
    """Classify current month into agricultural season for the given region."""
    if region == "ontario":
        if month in (3, 4):
            return "spring_prep"
        if 5 <= month <= 9:
            return "growing"
        if month in (10, 11):
            return "fall_harvest"
        return "winter"
    # Jalisco (default)
    if 6 <= month <= 10:
        return "temporal"
    return "secas"


def generate_seasonal_alerts(
    reference_date: date | None = None,
    region: str = "jalisco",
) -> list[dict]:
    """Generate seasonal calendar alerts for the given region.

    Pure function: takes a reference date (defaults to today) and region,
    returns a list of active alerts based on the regional phenology
    calendar and planting traditions.

    Args:
        reference_date: Date to check alerts for (defaults to today).
        region: Agricultural region — "jalisco" (default) or "ontario".

    Each alert contains:
        - crop: crop name
        - alert_type: preparacion | siembra | cosecha | mantenimiento | frost_warning
        - message: actionable Spanish-language guidance
        - season: region-specific season label
        - month_range: human-readable month range
    """
    if reference_date is None:
        reference_date = date.today()

    calendar = ONTARIO_PHENOLOGY_CALENDAR if region == "ontario" else PHENOLOGY_CALENDAR
    month = reference_date.month
    alerts = []

    for entry in calendar:
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
