"""Seed data for the cultivOS knowledge base."""

from cultivos.db.models import AncestralMethod, CropType, Disease, Fertilizer


FERTILIZER_SEEDS = [
    Fertilizer(
        name="Compost maduro",
        description_es="Materia organica descompuesta que mejora estructura del suelo, retencion de agua y actividad microbiana. Base de la agricultura regenerativa.",
        application_method="Incorporar 5-10 ton/ha antes de siembra. Aplicar en superficie como acolchado entre hileras.",
        cost_per_ha_mxn=2500,
        nutrient_profile="N-P-K balanceado (1-1-1), micronutrientes, acidos humicos",
        suitable_crops=["maiz", "frijol", "agave", "aguacate", "calabaza", "chile", "tomate", "nopal"],
    ),
    Fertilizer(
        name="Manure (estiercol composteado)",
        description_es="Estiercol de vaca, caballo o cabra composteado minimo 6 meses. Alto en nitrogeno y materia organica.",
        application_method="Aplicar 3-5 ton/ha composteado. Nunca fresco — riesgo de patogenos y quemado de raices.",
        cost_per_ha_mxn=1500,
        nutrient_profile="Alto N (2-3%), P moderado, K bajo, materia organica 40-60%",
        suitable_crops=["maiz", "frijol", "calabaza", "chile", "tomate", "sorgo"],
    ),
    Fertilizer(
        name="Vermicompost (lombricomposta)",
        description_es="Composta procesada por lombrices rojas californianas. Concentrado en nutrientes y microorganismos beneficos.",
        application_method="Aplicar 1-3 ton/ha en banda junto a la hilera de siembra. Ideal para viveros y trasplante.",
        cost_per_ha_mxn=5000,
        nutrient_profile="N-P-K (1.5-2-1), acidos humicos y fulvicos, enzimas, microbioma rico",
        suitable_crops=["maiz", "frijol", "agave", "aguacate", "calabaza", "chile", "tomate", "nopal", "flores"],
    ),
    Fertilizer(
        name="Biochar (carbon vegetal)",
        description_es="Carbon producido por pirolisis de biomasa. Mejora retencion de agua, CIC del suelo y secuestra carbono por siglos.",
        application_method="Incorporar 2-5 ton/ha mezclado con composta (activar antes de aplicar). Una sola aplicacion dura decadas.",
        cost_per_ha_mxn=4000,
        nutrient_profile="Bajo en NPK directo, alto en CIC (capacidad intercambio cationico), retencion de nutrientes",
        suitable_crops=["maiz", "agave", "aguacate", "cafe", "frijol", "calabaza"],
    ),
    Fertilizer(
        name="Aquaculture cycling (acuaponia residual)",
        description_es="Agua rica en nutrientes del cultivo de peces (tilapia, carpa) usada para riego. Ciclo cerrado peces-plantas.",
        application_method="Riego por goteo con agua de estanque filtrada. Diluir 1:3 con agua limpia para cultivos sensibles.",
        cost_per_ha_mxn=3000,
        nutrient_profile="Alto N (amonio/nitrato), P moderado, K bajo, micronutrientes del alimento de peces",
        suitable_crops=["maiz", "tomate", "chile", "calabaza", "lechuga", "nopal"],
    ),
    Fertilizer(
        name="Bocashi",
        description_es="Composta fermentada japonesa adaptada a Mexico. Fermentacion anaerobia rapida (14 dias) con microorganismos de montana.",
        application_method="Aplicar 2-4 ton/ha incorporado al suelo 2 semanas antes de siembra. No dejar en superficie.",
        cost_per_ha_mxn=2000,
        nutrient_profile="N-P-K (1.5-1.5-1), enzimas, microorganismos beneficos, acidos organicos",
        suitable_crops=["maiz", "frijol", "agave", "calabaza", "chile", "tomate", "nopal", "sorgo"],
    ),
    Fertilizer(
        name="Te de composta",
        description_es="Extracto liquido aerobico de composta. Inocula microorganismos beneficos y aporta nutrientes solubles.",
        application_method="Aplicar foliar (200 L/ha) o al suelo via riego. Usar dentro de 4 horas de preparacion.",
        cost_per_ha_mxn=800,
        nutrient_profile="NPK soluble bajo, alto en microorganismos, acidos humicos, enzimas",
        suitable_crops=["maiz", "frijol", "agave", "aguacate", "calabaza", "chile", "tomate", "nopal", "flores", "cafe"],
    ),
    Fertilizer(
        name="Harina de hueso",
        description_es="Huesos molidos esterilizados. Fuente organica de fosforo de liberacion lenta y calcio.",
        application_method="Incorporar 500-1000 kg/ha en la zona de raices antes de siembra. Ideal para suelos acidos.",
        cost_per_ha_mxn=3500,
        nutrient_profile="P alto (11-15%), Ca alto (20-30%), N bajo (1-2%)",
        suitable_crops=["maiz", "frijol", "aguacate", "tomate", "chile", "calabaza"],
    ),
    Fertilizer(
        name="Abono verde (cultivo de cobertura)",
        description_es="Siembra de leguminosas (veza, trebol, frijol) que se incorporan al suelo antes de florar. Fija nitrogeno atmosferico.",
        application_method="Sembrar entre ciclos. Incorporar al suelo con rastra 2-3 semanas antes de siembra principal.",
        cost_per_ha_mxn=1200,
        nutrient_profile="N alto (fijacion biologica 50-200 kg N/ha), mejora estructura, materia organica",
        suitable_crops=["maiz", "agave", "aguacate", "sorgo", "calabaza"],
    ),
    Fertilizer(
        name="Ceniza de madera",
        description_es="Residuo de quema de madera no tratada. Fuente de potasio y corrector de pH para suelos acidos.",
        application_method="Aplicar 300-500 kg/ha espolvoreada y rastrillada. No usar en suelos alcalinos (pH > 7).",
        cost_per_ha_mxn=400,
        nutrient_profile="K alto (5-10%), Ca alto, Mg moderado, pH alcalino (10-12)",
        suitable_crops=["maiz", "frijol", "calabaza", "tomate", "chile", "nopal"],
    ),
    # --- Ontario / Canada ---
    Fertilizer(
        name="Composted cattle manure (Ontario)",
        description_es="Estiercol de ganado lechero composteado de granjas de Ontario. Alto en nitrogeno y materia organica, adaptado a suelos arcillosos glaciales.",
        application_method="Incorporar 5-8 ton/ha en otono antes de congelamiento o en primavera 3 semanas antes de siembra. No aplicar sobre suelo congelado.",
        cost_per_ha_mxn=2667,  # ~200 CAD/ha / 0.075
        nutrient_profile="N alto (2.5%), P moderado (1.5%), K moderado (2%), materia organica 50-65%",
        suitable_crops=["corn", "soybean", "wheat", "apple", "grape"],
    ),
    Fertilizer(
        name="Wood ash (hardwood)",
        description_es="Ceniza de madera dura (arce, roble) comun en Ontario. Corrector de pH y fuente de potasio para suelos acidos del escudo canadiense.",
        application_method="Aplicar 500-1000 kg/ha en otono. No mezclar con fertilizantes nitrogenados. Analizar pH del suelo antes de aplicar.",
        cost_per_ha_mxn=1333,  # ~100 CAD/ha / 0.075
        nutrient_profile="K alto (5-8%), Ca muy alto (25-45%), Mg moderado, pH alcalino (10-13)",
        suitable_crops=["corn", "soybean", "wheat", "apple", "grape"],
    ),
    Fertilizer(
        name="Cover crop mix (Ontario)",
        description_es="Mezcla de trebol carmin, avena y rabano forrajero como cultivo de cobertura invernal. Fija nitrogeno, rompe compactacion y protege suelo de erosion invernal.",
        application_method="Sembrar despues de cosecha de grano (Sep-Oct). Incorporar en primavera con cultivador antes de siembra principal.",
        cost_per_ha_mxn=1600,  # ~120 CAD/ha / 0.075
        nutrient_profile="N alto (fijacion biologica 60-120 kg N/ha), mejora estructura, rompe compactacion con raiz pivotante",
        suitable_crops=["corn", "soybean", "wheat"],
    ),
]


def seed_fertilizers(db_session) -> int:
    """Load fertilizer seed data if table is empty. Returns count of records inserted."""
    existing = db_session.query(Fertilizer).count()
    if existing > 0:
        return 0
    for fert in FERTILIZER_SEEDS:
        db_session.add(Fertilizer(
            name=fert.name,
            description_es=fert.description_es,
            application_method=fert.application_method,
            cost_per_ha_mxn=fert.cost_per_ha_mxn,
            nutrient_profile=fert.nutrient_profile,
            suitable_crops=fert.suitable_crops,
        ))
    db_session.commit()
    return len(FERTILIZER_SEEDS)


ANCESTRAL_METHOD_SEEDS = [
    AncestralMethod(
        name="Milpa",
        description_es="Sistema de policultivo mesoamericano que combina maiz, frijol y calabaza (las tres hermanas). El maiz da estructura al frijol, el frijol fija nitrogeno, la calabaza cubre el suelo reduciendo evaporacion y malezas.",
        region="Mesoamerica / Jalisco",
        practice_type="intercropping",
        crops=["maiz", "frijol", "calabaza"],
        benefits_es="Fijacion biologica de nitrogeno, control natural de malezas, diversificacion de cosecha, resiliencia ante sequias.",
        scientific_basis="Validado por FAO e INIFAP — la milpa produce mas calorias/ha que el monocultivo de maiz y regenera nitrogeno del suelo sin fertilizantes sinteticos.",
    ),
    AncestralMethod(
        name="Chinampa",
        description_es="Islas artificiales flotantes construidas en lagos y zonas pantanosas. Capas de vegetacion acuatica, lodo y estacas crean parcelas extremadamente fertiles con riego natural por capilaridad.",
        region="Valle de Mexico",
        practice_type="water_management",
        crops=["maiz", "frijol", "calabaza", "chile", "tomate", "flores"],
        benefits_es="Productividad hasta 4 cosechas/ano, riego pasivo, reciclaje de materia organica acuatica, biodiversidad acuatica-terrestre.",
        scientific_basis="UNESCO Patrimonio de la Humanidad. Estudios de la UNAM demuestran que las chinampas activas en Xochimilco mantienen rendimientos comparables a agricultura convencional sin insumos sinteticos.",
    ),
    AncestralMethod(
        name="Terrazas de cultivo",
        description_es="Plataformas escalonadas en laderas para retener suelo y agua. Usadas desde epocas prehispanicas en zonas montanosas de Mesoamerica para cultivar en pendientes pronunciadas.",
        region="Mesoamerica / Jalisco",
        practice_type="soil_management",
        crops=["maiz", "frijol", "agave", "nopal"],
        benefits_es="Prevencion de erosion, retencion de agua de lluvia, creacion de microclimas, aprovechamiento de terrenos en pendiente.",
        scientific_basis="CONABIO documenta que las terrazas reducen erosion hidrica hasta 90% en laderas con pendiente >15%. Patron similar a terrazas incas validadas por estudios en Peru y Bolivia.",
    ),
    AncestralMethod(
        name="Roza-tumba-quema controlada",
        description_es="Sistema rotativo donde se tala y quema vegetacion secundaria para liberar nutrientes al suelo. Con periodos de descanso (barbecho) de 5-15 anos permite regeneracion natural del bosque.",
        region="Sureste de Mexico / Jalisco",
        practice_type="soil_management",
        crops=["maiz", "frijol", "calabaza", "chile"],
        benefits_es="Liberacion rapida de nutrientes (ceniza rica en K y Ca), control de plagas por calor, regeneracion de bosque secundario en ciclos largos.",
        scientific_basis="INIFAP y estudios de la Selva Maya demuestran que con barbecho adecuado (>10 anos) el sistema es sustentable. El problema moderno es la reduccion de periodos de descanso por presion demografica.",
    ),
    AncestralMethod(
        name="Abonos verdes ancestrales",
        description_es="Siembra de leguminosas nativas (frijol terciopelo, canavalia, crotalaria) como cultivo de cobertura entre ciclos para fijar nitrogeno y proteger el suelo.",
        region="Mesoamerica / Jalisco",
        practice_type="soil_management",
        crops=["maiz", "frijol", "calabaza", "sorgo"],
        benefits_es="Fijacion biologica de nitrogeno (80-200 kg N/ha), supresion de malezas, prevencion de erosion, aporte de materia organica.",
        scientific_basis="Mucuna pruriens (frijol terciopelo) fija hasta 200 kg N/ha segun estudios de CIMMYT en Mesoamerica. Reduccion documentada de fertilizantes sinteticos hasta 50% en rotaciones maiz-mucuna.",
    ),
    AncestralMethod(
        name="Cultivo en callejones",
        description_es="Hileras de arboles o arbustos leguminosos (leucaena, gliricidia) intercalados con cultivos anuales. Las podas aportan materia organica y nitrogeno al suelo entre las filas.",
        region="Mesoamerica / Jalisco",
        practice_type="intercropping",
        crops=["maiz", "frijol", "calabaza", "chile"],
        benefits_es="Aporte continuo de nitrogeno, sombra parcial para cultivos sensibles, leña como subproducto, barrera cortavientos.",
        scientific_basis="Investigaciones de ICRAF (World Agroforestry) confirman que la leucaena en callejones aporta 100-300 kg N/ha/ano mediante podas incorporadas al suelo.",
    ),
    AncestralMethod(
        name="Asociacion de cultivos",
        description_es="Siembra de multiples especies compatibles en la misma parcela basada en conocimiento tradicional de companerismo entre plantas — mas alla de la milpa clasica.",
        region="Jalisco",
        practice_type="intercropping",
        crops=["maiz", "frijol", "calabaza", "chile", "tomate", "nopal"],
        benefits_es="Control biologico de plagas, uso eficiente de espacio y luz, diversificacion de ingresos, resiliencia ante clima extremo.",
        scientific_basis="Meta-analisis de Altieri (UC Berkeley) demuestra que policultivos reducen incidencia de plagas 30-60% comparado con monocultivos, con rendimientos equivalentes o superiores por unidad de area total.",
    ),
    AncestralMethod(
        name="Labranza cero tradicional",
        description_es="Siembra directa sin arar el suelo, usando coa (palo plantador) o espeque. El suelo mantiene su estructura, vida microbiana y cobertura organica intactas.",
        region="Mesoamerica / Jalisco",
        practice_type="soil_management",
        crops=["maiz", "frijol", "calabaza", "agave"],
        benefits_es="Conservacion de estructura del suelo, retencion de humedad, proteccion de vida microbiana, reduccion de erosion.",
        scientific_basis="CIMMYT demuestra que la labranza cero incrementa materia organica del suelo 0.2-0.5% en 5 anos y reduce erosion hidrica hasta 80% comparada con labranza convencional en laderas de Jalisco.",
    ),
    # --- Ontario / Canada ---
    AncestralMethod(
        name="Cover cropping (Ontario)",
        description_es="Siembra de cultivos de cobertura invernal (trebol carmin, centeno, rabano forrajero) despues de cosecha de grano para proteger el suelo durante el invierno canadiense y fijar nitrogeno.",
        region="Ontario",
        practice_type="soil_management",
        crops=["corn", "soybean", "wheat"],
        benefits_es="Proteccion contra erosion invernal, fijacion de nitrogeno (60-120 kg N/ha), ruptura de compactacion, supresion de malezas en primavera.",
        scientific_basis="University of Guelph y OMAFRA documentan que cultivos de cobertura reducen erosion 50-90% y aumentan materia organica 0.3% en 5 anos en suelos arcillosos de Ontario.",
    ),
    AncestralMethod(
        name="Rotacion maiz-soya-trigo",
        description_es="Sistema de rotacion trianual clasico del cinturon agricola de Ontario. Maiz aprovecha nitrogeno residual de soya, trigo rompe ciclos de plagas, soya fija nitrogeno para el siguiente ciclo.",
        region="Ontario",
        practice_type="soil_management",
        crops=["corn", "soybean", "wheat"],
        benefits_es="Ruptura de ciclos de plagas, balance de nutrientes sin fertilizantes sinteticos, diversificacion de ingresos, mejora de estructura del suelo.",
        scientific_basis="Ridgetown Campus (U of Guelph) demuestra que la rotacion trianual incrementa rendimiento de maiz 10-15% vs monocultivo y reduce uso de fungicidas 40% en ensayos de largo plazo.",
    ),
    AncestralMethod(
        name="Companion planting (Ontario)",
        description_es="Asociacion de cultivos basada en tradiciones indigenas y conocimiento de agricultores de Ontario. Incluye intercalado de trebol en huertos de manzana y mostaza en vinedos para control biologico.",
        region="Ontario",
        practice_type="intercropping",
        crops=["apple", "grape", "corn", "soybean"],
        benefits_es="Control biologico de plagas, habitat para polinizadores, fijacion de nitrogeno en huertos, reduccion de erosion entre hileras.",
        scientific_basis="Vineland Research Station documenta que coberturas de trebol en huertos de manzana reducen necesidad de fertilizante nitrogenado 30-50% y aumentan poblaciones de polinizadores nativos.",
    ),
    AncestralMethod(
        name="Windbreaks (cortinas rompevientos)",
        description_es="Hileras de arboles nativos (arce, cedro, roble) plantadas en bordes de campos para reducir erosion eolica, proteger cultivos del viento frio y crear habitat para fauna benefica.",
        region="Ontario",
        practice_type="soil_management",
        crops=["corn", "soybean", "wheat", "apple"],
        benefits_es="Reduccion de erosion eolica 50-80%, proteccion de cultivos contra vientos frios de invierno, habitat para aves insectivoras, microclima mas calido para adelantar siembra.",
        scientific_basis="AAFC (Agriculture and Agri-Food Canada) documenta que cortinas rompevientos reducen erosion eolica hasta 80% y pueden incrementar rendimiento de maiz 6-12% en campos protegidos del suroeste de Ontario.",
    ),
]


def seed_ancestral_methods(db_session) -> int:
    """Load ancestral method seed data if table is empty. Returns count of records inserted."""
    existing = db_session.query(AncestralMethod).count()
    if existing > 0:
        return 0
    for method in ANCESTRAL_METHOD_SEEDS:
        db_session.add(AncestralMethod(
            name=method.name,
            description_es=method.description_es,
            region=method.region,
            practice_type=method.practice_type,
            crops=method.crops,
            benefits_es=method.benefits_es,
            scientific_basis=method.scientific_basis,
        ))
    db_session.commit()
    return len(ANCESTRAL_METHOD_SEEDS)


CROP_TYPE_SEEDS = [
    CropType(
        name="Maiz",
        family="Poaceae",
        growing_season="Temporal (Jun-Oct)",
        water_needs="media",
        regions=["Jalisco", "Mesoamerica", "Ontario"],
        companions=["frijol", "calabaza", "chile"],
        days_to_harvest=120,
        optimal_temp_min=18.0,
        optimal_temp_max=32.0,
        description_es="Cereal base de la alimentacion mexicana. Cultivo de temporal por excelencia en Jalisco. Se asocia tradicionalmente con frijol y calabaza en el sistema milpa.",
    ),
    CropType(
        name="Frijol",
        family="Fabaceae",
        growing_season="Temporal (Jun-Oct)",
        water_needs="media",
        regions=["Jalisco", "Mesoamerica", "Ontario"],
        companions=["maiz", "calabaza", "zanahoria"],
        days_to_harvest=90,
        optimal_temp_min=15.0,
        optimal_temp_max=27.0,
        description_es="Leguminosa clave en la dieta mexicana y en la agricultura regenerativa — fija nitrogeno atmosferico en el suelo, beneficiando cultivos asociados.",
    ),
    CropType(
        name="Calabaza",
        family="Cucurbitaceae",
        growing_season="Temporal (Jun-Oct)",
        water_needs="media",
        regions=["Jalisco", "Mesoamerica"],
        companions=["maiz", "frijol", "girasol"],
        days_to_harvest=100,
        optimal_temp_min=18.0,
        optimal_temp_max=35.0,
        description_es="Tercera hermana de la milpa. Sus hojas grandes cubren el suelo reduciendo evaporacion y malezas. Frutos, flores y semillas son comestibles.",
    ),
    CropType(
        name="Chile",
        family="Solanaceae",
        growing_season="Temporal (Jun-Oct) o riego",
        water_needs="media",
        regions=["Jalisco", "Mesoamerica"],
        companions=["tomate", "albahaca", "zanahoria"],
        days_to_harvest=80,
        optimal_temp_min=20.0,
        optimal_temp_max=35.0,
        description_es="Hortaliza fundamental en la gastronomia mexicana. Jalisco produce chile de arbol, serrano y cascabel. Sensible a exceso de humedad.",
    ),
    CropType(
        name="Jitomate",
        family="Solanaceae",
        growing_season="Todo el ano (con riego)",
        water_needs="alta",
        regions=["Jalisco", "Mesoamerica"],
        companions=["albahaca", "zanahoria", "cebolla"],
        days_to_harvest=75,
        optimal_temp_min=18.0,
        optimal_temp_max=30.0,
        description_es="Hortaliza de alto valor comercial. Requiere tutoreo y manejo sanitario cuidadoso. Vulnerable a tizon tardio y mosca blanca en Jalisco.",
    ),
    CropType(
        name="Aguacate",
        family="Lauraceae",
        growing_season="Perenne (cosecha Oct-Mar)",
        water_needs="alta",
        regions=["Jalisco", "Michoacan"],
        companions=["cafe", "platano", "macadamia"],
        days_to_harvest=365,
        optimal_temp_min=16.0,
        optimal_temp_max=28.0,
        description_es="Arbol frutal de alto valor economico. Jalisco es zona de expansion del aguacate Hass. Requiere suelo bien drenado y es susceptible a antracnosis.",
    ),
    CropType(
        name="Agave",
        family="Asparagaceae",
        growing_season="Perenne (cosecha 6-8 anos)",
        water_needs="baja",
        regions=["Jalisco"],
        companions=["frijol", "calabaza", "nopal"],
        days_to_harvest=2555,
        optimal_temp_min=15.0,
        optimal_temp_max=35.0,
        description_es="Agave tequilana Weber variedad azul. Cultivo emblematico de Jalisco para la industria tequilera. Extremadamente resistente a sequia. Denominacion de origen protegida.",
    ),
    CropType(
        name="Sorgo",
        family="Poaceae",
        growing_season="Temporal (Jun-Oct)",
        water_needs="baja",
        regions=["Jalisco", "Ontario"],
        companions=["frijol", "girasol", "calabaza"],
        days_to_harvest=110,
        optimal_temp_min=20.0,
        optimal_temp_max=38.0,
        description_es="Cereal resistente a sequia usado como forraje y grano. Alternativa al maiz en zonas de Jalisco con precipitacion limitada.",
    ),
    CropType(
        name="Garbanzo",
        family="Fabaceae",
        growing_season="Secas (Nov-Mar)",
        water_needs="baja",
        regions=["Jalisco", "Ontario"],
        companions=["trigo", "cebada", "girasol"],
        days_to_harvest=100,
        optimal_temp_min=10.0,
        optimal_temp_max=25.0,
        description_es="Leguminosa de ciclo invernal. Fija nitrogeno en el suelo. Jalisco es productor importante de garbanzo blanco para exportacion.",
    ),
    CropType(
        name="Cana de azucar",
        family="Poaceae",
        growing_season="Perenne (cosecha Nov-May)",
        water_needs="alta",
        regions=["Jalisco"],
        companions=["frijol", "soya", "cacahuate"],
        days_to_harvest=365,
        optimal_temp_min=20.0,
        optimal_temp_max=38.0,
        description_es="Graminea tropical de alto rendimiento. Jalisco es uno de los principales productores en Mexico. La region Costa Sur es zona canera importante.",
    ),
    CropType(
        name="Nopal",
        family="Cactaceae",
        growing_season="Perenne (cosecha todo el ano)",
        water_needs="baja",
        regions=["Jalisco", "Mesoamerica"],
        companions=["agave", "frijol", "maiz"],
        days_to_harvest=180,
        optimal_temp_min=12.0,
        optimal_temp_max=38.0,
        description_es="Cactacea comestible (pencas y tunas) extremadamente resistente a sequia. Cultivo ideal para zonas aridas de Jalisco. Rico en fibra y antioxidantes.",
    ),
    # --- Ontario / Canada ---
    CropType(
        name="Corn (Field)",
        family="Poaceae",
        growing_season="May-Oct (siembra mayo, cosecha octubre)",
        water_needs="media",
        regions=["Ontario"],
        companions=["soybean", "wheat", "clover"],
        days_to_harvest=120,
        optimal_temp_min=10.0,
        optimal_temp_max=30.0,
        description_es="Maiz de campo para grano y ensilaje. Cultivo principal del suroeste de Ontario. Requiere acumulacion de unidades de calor (CHU 2700-3100). Sensible a heladas tardias de mayo.",
    ),
    CropType(
        name="Soybean",
        family="Fabaceae",
        growing_season="May-Oct (siembra mayo-junio, cosecha septiembre-octubre)",
        water_needs="media",
        regions=["Ontario"],
        companions=["corn", "wheat", "clover"],
        days_to_harvest=110,
        optimal_temp_min=10.0,
        optimal_temp_max=30.0,
        description_es="Leguminosa oleaginosa clave en la rotacion de Ontario. Fija nitrogeno atmosferico (50-80 kg N/ha). Segundo cultivo mas importante de la provincia despues del maiz.",
    ),
    CropType(
        name="Winter Wheat",
        family="Poaceae",
        growing_season="Sep-Jul (siembra otono, cosecha verano siguiente)",
        water_needs="baja",
        regions=["Ontario"],
        companions=["clover", "soybean", "corn"],
        days_to_harvest=300,
        optimal_temp_min=-5.0,
        optimal_temp_max=25.0,
        description_es="Trigo de invierno sembrado en otono y cosechado en julio. Cobertura invernal que protege el suelo de erosion. Requiere vernalizacion (periodo de frio) para florecer.",
    ),
    CropType(
        name="Apple",
        family="Rosaceae",
        growing_season="Perenne (cosecha Sep-Oct)",
        water_needs="media",
        regions=["Ontario"],
        companions=["clover", "comfrey", "nasturtium"],
        days_to_harvest=365,
        optimal_temp_min=-2.0,
        optimal_temp_max=28.0,
        description_es="Manzana de Ontario — variedades principales: Honeycrisp, Gala, McIntosh, Empire. Region de Niagara y condado de Norfolk son zonas principales. Requiere poda invernal y control de sarna (apple scab).",
    ),
    CropType(
        name="Grape",
        family="Vitaceae",
        growing_season="Perenne (cosecha Sep-Oct)",
        water_needs="baja",
        regions=["Ontario", "Niagara"],
        companions=["clover", "mustard", "fescue"],
        days_to_harvest=365,
        optimal_temp_min=-3.0,
        optimal_temp_max=30.0,
        description_es="Vid para vino y mesa. Region de Niagara Peninsula y Prince Edward County son denominaciones principales. Variedades: Riesling, Chardonnay, Pinot Noir, Cabernet Franc. Icewine es especialidad de Ontario.",
    ),
    CropType(
        name="Greenhouse Tomato",
        family="Solanaceae",
        growing_season="Todo el ano (invernadero climatizado)",
        water_needs="alta",
        regions=["Ontario"],
        companions=["basil", "marigold", "pepper"],
        days_to_harvest=75,
        optimal_temp_min=18.0,
        optimal_temp_max=28.0,
        description_es="Tomate de invernadero — Ontario es lider canadiense en produccion bajo invernadero. Region de Leamington (condado de Essex) es la capital del invernadero de Canada. Produccion anual con sistemas hidroponicos.",
    ),
]


def seed_crops(db_session) -> int:
    """Load crop type seed data if table is empty. Returns count of records inserted."""
    existing = db_session.query(CropType).count()
    if existing > 0:
        return 0
    for crop in CROP_TYPE_SEEDS:
        db_session.add(CropType(
            name=crop.name,
            family=crop.family,
            growing_season=crop.growing_season,
            water_needs=crop.water_needs,
            regions=crop.regions,
            companions=crop.companions,
            days_to_harvest=crop.days_to_harvest,
            optimal_temp_min=crop.optimal_temp_min,
            optimal_temp_max=crop.optimal_temp_max,
            description_es=crop.description_es,
        ))
    db_session.commit()
    return len(CROP_TYPE_SEEDS)


DISEASE_SEEDS = [
    Disease(
        name="Roya del maiz",
        description_es="Enfermedad fungica causada por Puccinia sorghi. Produce pustulas anaranjadas-rojizas en el enves de las hojas que liberan esporas. Reduce rendimiento 10-40% en ataques severos.",
        symptoms=["hojas amarillas", "pustulas naranjas", "manchas", "secamiento de hojas"],
        affected_crops=["maiz", "sorgo"],
        treatments=[
            {"name": "Caldo bordeles", "description_es": "Mezcla de sulfato de cobre y cal hidratada al 1%. Aplicar preventivamente cada 15 dias durante temporada humeda.", "organic": True},
            {"name": "Extracto de cola de caballo", "description_es": "Decoccion de Equisetum al 10%. Fungicida natural rico en silice. Aplicar foliar cada 7-10 dias.", "organic": True},
            {"name": "Rotacion de cultivos", "description_es": "Alternar maiz con leguminosas (frijol, garbanzo) para romper ciclo del patogeno en el suelo.", "organic": True},
        ],
        region="Jalisco",
        severity="media",
    ),
    Disease(
        name="Tizon tardio",
        description_es="Enfermedad devastadora causada por Phytophthora infestans. Afecta hojas, tallos y frutos con lesiones acuosas oscuras. Puede destruir un cultivo en dias bajo condiciones humedas y frias.",
        symptoms=["manchas oscuras", "lesiones acuosas", "marchitamiento", "pudricion de frutos", "hojas amarillas"],
        affected_crops=["tomate", "chile", "papa"],
        treatments=[
            {"name": "Caldo bordeles", "description_es": "Sulfato de cobre + cal al 1-2%. Aplicar cada 7-10 dias en temporada de lluvias como preventivo.", "organic": True},
            {"name": "Trichoderma harzianum", "description_es": "Hongo benefico antagonista. Aplicar al suelo y foliar (1x10^8 esporas/ml) cada 15 dias.", "organic": True},
            {"name": "Eliminacion de material infectado", "description_es": "Retirar y quemar plantas infectadas inmediatamente. No compostar material enfermo.", "organic": True},
        ],
        region="Jalisco",
        severity="alta",
    ),
    Disease(
        name="Fusarium",
        description_es="Marchitez vascular causada por Fusarium oxysporum. El hongo coloniza el xilema bloqueando el transporte de agua. Sintomas unilaterales — una mitad de la planta se marchita primero.",
        symptoms=["marchitamiento", "hojas amarillas", "oscurecimiento vascular", "muerte de planta"],
        affected_crops=["tomate", "chile", "frijol", "calabaza", "agave"],
        treatments=[
            {"name": "Trichoderma harzianum", "description_es": "Inocular suelo con Trichoderma (2 kg/ha) antes de siembra. Compite con Fusarium por espacio y nutrientes.", "organic": True},
            {"name": "Solarizacion del suelo", "description_es": "Cubrir suelo humedo con plastico transparente por 4-6 semanas en temporada caliente. Elimina patogenos por calor.", "organic": True},
            {"name": "Bocashi + microorganismos de montana", "description_es": "Enriquecer suelo con bocashi (3 ton/ha) y microorganismos nativos para suprimir patogenos mediante competencia.", "organic": True},
        ],
        region="Jalisco",
        severity="alta",
    ),
    Disease(
        name="Mosca blanca",
        description_es="Plaga causada por Bemisia tabaci y Trialeurodes vaporariorum. Succiona savia, excreta mielecilla que favorece fumagina, y transmite virus (TYLCV, begomovirus). Vector principal de enfermedades virales.",
        symptoms=["hojas amarillas", "mielecilla", "fumagina", "deformacion de hojas", "moscas blancas en enves"],
        affected_crops=["tomate", "chile", "calabaza", "frijol"],
        treatments=[
            {"name": "Extracto de neem", "description_es": "Azadiractina al 0.3%. Aplicar foliar cada 7 dias enfocando el enves de las hojas. Repelente e inhibidor de crecimiento.", "organic": True},
            {"name": "Trampas amarillas", "description_es": "Colocar trampas adhesivas amarillas (40x25 cm) a la altura del cultivo, 20-30 trampas/ha para monitoreo y captura masiva.", "organic": True},
            {"name": "Beauveria bassiana", "description_es": "Hongo entomopatogeno. Aplicar suspension (1x10^8 esporas/ml) foliar en las ultimas horas de la tarde. Parasita adultos y ninfas.", "organic": True},
        ],
        region="Jalisco",
        severity="alta",
    ),
    Disease(
        name="Gusano cogollero",
        description_es="Plaga causada por Spodoptera frugiperda. Larva devora el cogollo (meristemo apical) del maiz causando dano severo al crecimiento. Plaga numero 1 del maiz en Mexico.",
        symptoms=["hojas perforadas", "excremento en cogollo", "dano en cogollo", "larvas visibles"],
        affected_crops=["maiz", "sorgo"],
        treatments=[
            {"name": "Bacillus thuringiensis (Bt)", "description_es": "Bacteria entomopatogena. Aplicar al cogollo (1-2 L/ha de formulado comercial) cuando larvas son menores a 1.5 cm.", "organic": True},
            {"name": "Liberacion de Trichogramma", "description_es": "Avispa parasitoide que ataca huevos. Liberar 50,000-100,000 avispas/ha en 3-4 liberaciones durante temporada.", "organic": True},
            {"name": "Extracto de neem", "description_es": "Azadiractina inhibe la muda de larvas. Aplicar al cogollo cada 7 dias desde emergencia hasta que la planta cierre.", "organic": True},
        ],
        region="Jalisco",
        severity="alta",
    ),
    Disease(
        name="Mancha de asfalto",
        description_es="Complejo fungico (Phyllachora maydis + Monographella maydis + Coniothyrium phyllachorae). Produce manchas negras brillantes en hojas que se expanden rapidamente. Puede causar perdidas de 50-100% en variedades susceptibles.",
        symptoms=["manchas negras", "manchas", "secamiento de hojas", "hojas amarillas"],
        affected_crops=["maiz"],
        treatments=[
            {"name": "Caldo bordeles", "description_es": "Sulfato de cobre + cal al 1%. Aplicar preventivamente antes de floracion. 2-3 aplicaciones cada 10 dias.", "organic": True},
            {"name": "Extracto de ajo-chile", "description_es": "Macerado de 500g ajo + 500g chile en 20L agua. Colar y aplicar foliar. Fungicida y repelente de amplio espectro.", "organic": True},
            {"name": "Variedades resistentes", "description_es": "Usar semilla criolla local adaptada. Las variedades nativas de Jalisco tienen mejor tolerancia que hibridos comerciales.", "organic": True},
        ],
        region="Jalisco",
        severity="alta",
    ),
    Disease(
        name="Antracnosis del aguacate",
        description_es="Enfermedad fungica causada por Colletotrichum gloeosporioides. Produce manchas hundidas oscuras en frutos y necrosis en hojas. Principal enfermedad postcosecha del aguacate en Jalisco.",
        symptoms=["manchas oscuras", "manchas en frutos", "necrosis de hojas", "pudricion de frutos"],
        affected_crops=["aguacate", "mango"],
        treatments=[
            {"name": "Caldo bordeles", "description_es": "Sulfato de cobre al 1%. Aplicar cada 15 dias desde floracion hasta cosecha. Protege frutos en desarrollo.", "organic": True},
            {"name": "Poda sanitaria", "description_es": "Eliminar ramas infectadas y frutos danados. Desinfectar herramientas con alcohol al 70% entre cortes.", "organic": True},
            {"name": "Trichoderma + Bacillus subtilis", "description_es": "Mezcla de biocontroladores. Aplicar foliar cada 15 dias (1L/ha de cada formulado). Control preventivo y curativo.", "organic": True},
        ],
        region="Jalisco",
        severity="media",
    ),
    Disease(
        name="Trips del chile",
        description_es="Plaga causada por Frankliniella occidentalis. Raspa tejido foliar causando plateado de hojas. Transmite virus (TSWV). Plaga clave en produccion de chile en Jalisco.",
        symptoms=["hojas plateadas", "deformacion de hojas", "puntos negros en hojas", "flores danadas"],
        affected_crops=["chile", "tomate", "calabaza"],
        treatments=[
            {"name": "Beauveria bassiana", "description_es": "Hongo entomopatogeno. Aplicar al follaje (1x10^8 esporas/ml) en horas frescas. Efectivo contra ninfas y adultos.", "organic": True},
            {"name": "Trampas azules", "description_es": "Colocar trampas adhesivas azules (color atractivo para trips) a nivel del cultivo. 20-30 trampas/ha.", "organic": True},
            {"name": "Extracto de neem + jabon potasico", "description_es": "Neem al 0.3% + jabon potasico al 1%. Aplicar juntos para efecto sinergico: neem repele, jabon rompe cutícula.", "organic": True},
        ],
        region="Jalisco",
        severity="media",
    ),
    # --- Ontario / Canada ---
    Disease(
        name="Corn rootworm",
        description_es="Plaga causada por Diabrotica virgifera. Las larvas se alimentan de raices del maiz causando volcamiento y reduccion severa de rendimiento. Plaga numero 1 del maiz en Ontario.",
        symptoms=["volcamiento de plantas", "raices danadas", "crecimiento irregular", "escarabajos adultos en estigmas"],
        affected_crops=["corn"],
        treatments=[
            {"name": "Rotacion de cultivos", "description_es": "Rotar maiz con soya o trigo. La larva solo sobrevive en raices de maiz — un ano sin maiz rompe el ciclo.", "organic": True},
            {"name": "Nematodos entomopatogenos", "description_es": "Aplicar Heterorhabditis bacteriophora al suelo en primavera (2.5 billones/ha). Parasitan larvas en la rizosfera.", "organic": True},
            {"name": "Variedades tolerantes", "description_es": "Usar hibridos con sistema radicular vigoroso que tolera dano moderado sin volcamiento. Consultar listado OMAFRA.", "organic": True},
        ],
        region="Ontario",
        severity="alta",
    ),
    Disease(
        name="Soybean aphid",
        description_es="Plaga causada por Aphis glycines. Colonia de afidos en enves de hojas que succiona savia y reduce rendimiento 10-40%. Puede alcanzar miles de individuos por planta.",
        symptoms=["hojas enrolladas", "mielecilla", "fumagina", "colonias de afidos en enves", "reduccion de vainas"],
        affected_crops=["soybean"],
        treatments=[
            {"name": "Mariquitas (Coccinellidae)", "description_es": "Conservar habitat de depredadores naturales. Una mariquita consume 50-60 afidos/dia. Evitar insecticidas de amplio espectro.", "organic": True},
            {"name": "Extracto de neem", "description_es": "Azadiractina al 0.3%. Aplicar foliar cuando poblacion supere umbral economico (250 afidos/planta). Repetir cada 7 dias.", "organic": True},
            {"name": "Jabon potasico", "description_es": "Aplicar jabon potasico al 2% foliar. Rompe cutícula del afido por contacto. Aplicar en horas frescas con buena cobertura.", "organic": True},
        ],
        region="Ontario",
        severity="media",
    ),
    Disease(
        name="Apple scab",
        description_es="Enfermedad fungica causada por Venturia inaequalis. Produce lesiones olivaceas en hojas y frutos de manzana. Enfermedad mas importante de manzana en Ontario — puede destruir cosecha comercial.",
        symptoms=["manchas olivaceas en hojas", "lesiones en frutos", "defoliacion prematura", "frutos deformes", "costras en piel"],
        affected_crops=["apple"],
        treatments=[
            {"name": "Azufre mojable", "description_es": "Aplicar azufre micronizado (3-5 kg/ha) preventivamente desde boton rosa. Intervalos de 7-10 dias durante periodo de infeccion primaria (abril-junio).", "organic": True},
            {"name": "Caldo bordeles", "description_es": "Sulfato de cobre + cal al 1%. Aplicar en dormancia (marzo) y pre-floracion. No aplicar despues de floracion por riesgo de russet en frutos.", "organic": True},
            {"name": "Sanidad de huerto", "description_es": "Retirar y compostar hojas caidas en otono (fuente de inoculo primario). Aplicar urea 5% foliar en otono para acelerar descomposicion de hojarasca.", "organic": True},
        ],
        region="Ontario",
        severity="alta",
    ),
    Disease(
        name="Powdery mildew (grape)",
        description_es="Enfermedad fungica causada por Erysiphe necator. Produce polvo blanco en hojas, brotes y racimos de uva. Reduce calidad del vino y rendimiento. Problematica en vinedos de Niagara.",
        symptoms=["polvo blanco en hojas", "deformacion de brotes", "racimos cubiertos", "sabor alterado en uva", "hojas amarillas"],
        affected_crops=["grape"],
        treatments=[
            {"name": "Azufre mojable", "description_es": "Aplicar 3-5 kg/ha cada 10-14 dias desde brote de 15 cm hasta envero. No aplicar a >30C (fitotoxicidad).", "organic": True},
            {"name": "Bicarbonato de potasio", "description_es": "Aplicar solucion al 0.5% foliar como curativo. Altera pH de la superficie foliar inhibiendo germinacion de esporas.", "organic": True},
            {"name": "Manejo de canopia", "description_es": "Deshoje de zona de racimos para mejorar circulacion de aire. Reducir densidad de brotes. Exponer racimos al sol.", "organic": True},
        ],
        region="Ontario",
        severity="media",
    ),
    Disease(
        name="Late blight (Ontario)",
        description_es="Enfermedad causada por Phytophthora infestans — mismo patogeno que en Mexico pero cepas adaptadas al clima templado de Ontario. Afecta tomate de invernadero y papa. Se propaga rapidamente en condiciones frias y humedas.",
        symptoms=["manchas oscuras acuosas", "lesiones en tallos", "pudricion de frutos", "micelio blanco en enves", "olor fetido"],
        affected_crops=["tomato", "potato"],
        treatments=[
            {"name": "Caldo bordeles", "description_es": "Sulfato de cobre + cal al 1%. Aplicar preventivamente cada 7 dias cuando humedad relativa >90% y temperatura <20C.", "organic": True},
            {"name": "Bacillus subtilis", "description_es": "Bacteria antagonista. Aplicar foliar (2 L/ha formulado comercial) cada 7-10 dias. Compite con Phytophthora por nicho ecologico.", "organic": True},
            {"name": "Ventilacion de invernadero", "description_es": "Mantener humedad <85% en invernadero. Aumentar circulacion de aire. Evitar riego por aspersion — usar goteo.", "organic": True},
        ],
        region="Ontario",
        severity="alta",
    ),
    Disease(
        name="Downy mildew (grape)",
        description_es="Enfermedad fungica causada por Plasmopara viticola. Produce manchas aceitosas amarillas en haz de hojas y esporulacion algodonosa blanca en enves. Mas severa que powdery mildew en anos humedos.",
        symptoms=["manchas aceitosas amarillas", "esporulacion blanca en enves", "necrosis de hojas", "racimos secos", "defoliacion"],
        affected_crops=["grape"],
        treatments=[
            {"name": "Caldo bordeles", "description_es": "Sulfato de cobre + cal al 1-2%. Aplicar preventivamente cada 10-14 dias desde brote de 10 cm. Tratamiento clasico de vinedos.", "organic": True},
            {"name": "Fosfito de potasio", "description_es": "Aplicar foliar (3 L/ha) cada 10 dias. Estimula defensas naturales de la planta (SAR) y tiene efecto fungicida directo.", "organic": True},
            {"name": "Drenaje y circulacion de aire", "description_es": "Mejorar drenaje del suelo. Deshoje y manejo de canopia para reducir humedad en zona de racimos. Orientar hileras N-S.", "organic": True},
        ],
        region="Ontario",
        severity="alta",
    ),
]


def seed_diseases(db_session) -> int:
    """Load disease seed data if table is empty. Returns count of records inserted."""
    existing = db_session.query(Disease).count()
    if existing > 0:
        return 0
    for disease in DISEASE_SEEDS:
        db_session.add(Disease(
            name=disease.name,
            description_es=disease.description_es,
            symptoms=disease.symptoms,
            affected_crops=disease.affected_crops,
            treatments=disease.treatments,
            region=disease.region,
            severity=disease.severity,
        ))
    db_session.commit()
    return len(DISEASE_SEEDS)
