"""Seed data for the cultivOS knowledge base."""

from cultivos.db.models import AgronomistTip, AncestralMethod, CropType, CropVariety, Disease, FarmerVocabulary, Fertilizer


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


CROP_VARIETY_SEEDS = [
    # Maiz — 4 local Jalisco/LATAM varieties
    CropVariety(
        crop_name="maiz",
        name="Maiz Azul Criollo de Jalisco",
        region="Altos de Jalisco",
        altitude_m=1800,
        water_mm=700,
        diseases=["tizón_foliar", "carbón_de_la_espiga", "roya"],
        adaptation_notes="Variedad criollo azul de alta adaptación a altitudes de 1600-2000 msnm. Alta tolerancia a sequía moderada. Ciclo 110-120 días. Grano azul-morado rico en antocianinas. Usado en tortillas azules y tamales de maíz azul.",
    ),
    CropVariety(
        crop_name="maiz",
        name="Maiz Blanco de Temporal Jaliscience",
        region="Valles Centrales de Jalisco",
        altitude_m=1500,
        water_mm=650,
        diseases=["roya_común", "mancha_de_asfalto"],
        adaptation_notes="Ciclo corto (90-100 días), ideal para temporal junio-octubre en valles centrales. Grano blanco harinoso. Muy productivo bajo lluvia natural sin irrigación suplementaria.",
    ),
    CropVariety(
        crop_name="maiz",
        name="Maiz Olotillo Rojo de la Costa",
        region="Costa Sur de Jalisco",
        altitude_m=400,
        water_mm=1200,
        diseases=["pudrición_de_mazorca", "tizón_de_la_hoja_del_norte"],
        adaptation_notes="Variedad costera adaptada a temperaturas altas (28-35°C) y alta humedad. Olote rojo delgado, grano semi-dentado. Ciclo largo 130-140 días. Resistente a plagas de almacenaje.",
    ),
    CropVariety(
        crop_name="maiz",
        name="Maiz Cacahuazintle Criollo",
        region="Jalisco y Michoacán",
        altitude_m=2000,
        water_mm=600,
        diseases=["carbón_del_maíz", "fusarium_de_mazorca"],
        adaptation_notes="Maíz cacahuazintle (pozolero) de endospermo suave y harinoso. Preferido para pozole y atole. Altura de planta mayor a 2.5 m. Requiere suelos bien drenados. Tolerante a heladas tardías de primavera.",
    ),
    # Agave — 3 Jalisco varieties
    CropVariety(
        crop_name="agave",
        name="Agave Tequilana Weber Azul",
        region="Jalisco (DO Tequila)",
        altitude_m=1200,
        water_mm=800,
        diseases=["pudrición_de_raíz_por_Fusarium", "picudo_del_agave"],
        adaptation_notes="Única variedad autorizada para producción de tequila bajo Denominación de Origen. Cosecha a los 7-10 años. Muy sensible a pudrición radicular — requiere suelos bien drenados y sin compactación. Propagación por hijuelos (mecuates) exclusivamente.",
    ),
    CropVariety(
        crop_name="agave",
        name="Agave Tobaziche Silvestre",
        region="Sierra de Jalisco",
        altitude_m=1600,
        water_mm=400,
        diseases=["trips_del_agave"],
        adaptation_notes="Agave silvestre usado en producción artesanal de mezcal jalisciense. Ciclo muy largo (15-20 años). Alta tolerancia a sequía extrema. No se cultiva comercialmente — se cosecha silvestre o semi-cultivado. Alta demanda para mezcal premium.",
    ),
    CropVariety(
        crop_name="agave",
        name="Agave Angustifolia (Espadín Jalisciense)",
        region="Sierra Occidental de Jalisco",
        altitude_m=1000,
        water_mm=600,
        diseases=["bacteriosis_del_agave", "trips"],
        adaptation_notes="Especie versátil usada para mezcal artesanal en sierra occidental. Ciclo 8-12 años. Más tolerante a condiciones variables que el azul tequilana. Creciente demanda por boom del mezcal artesanal.",
    ),
    # Frijol — 3 local varieties
    CropVariety(
        crop_name="frijol",
        name="Frijol Negro de Jamapa Jaliscience",
        region="Valles Centrales de Jalisco",
        altitude_m=1400,
        water_mm=500,
        diseases=["antracnosis", "mosaico_común"],
        adaptation_notes="Variedad de frijol negro de ciclo corto (70-80 días). Grano pequeño negro brillante, sabor suave. Ideal para temporal. Resistente a pudrición radicular. Alta demanda en mercados locales y exportación.",
    ),
    CropVariety(
        crop_name="frijol",
        name="Frijol Bayo de Jalisco",
        region="Los Altos de Jalisco",
        altitude_m=1700,
        water_mm=550,
        diseases=["roya_del_frijol", "tizón_de_la_hoja"],
        adaptation_notes="Frijol bayo (beige) adaptado a las altitudes de Los Altos. Grano grande harinoso. Ciclo 85-95 días. Sabor cremoso, preferido para caldo tlalpeño y frijoles charros jaliscienses.",
    ),
    CropVariety(
        crop_name="frijol",
        name="Frijol Flor de Mayo Jaliscience",
        region="Jalisco",
        altitude_m=1500,
        water_mm=500,
        diseases=["antracnosis", "viruela_del_frijol"],
        adaptation_notes="Variedad rosada moteada de alta adaptabilidad en todo Jalisco. Una de las más cultivadas en la región. Ciclo 80-90 días. Buen rendimiento en condiciones de temporal variable.",
    ),
    # Chile — 3 local varieties
    CropVariety(
        crop_name="chile",
        name="Chiltepín Silvestre de Jalisco",
        region="Barrancas del Río Santiago",
        altitude_m=800,
        water_mm=900,
        diseases=["antracnosis_del_chile", "phytophthora"],
        adaptation_notes="Chile silvestre más picante del mundo (50,000-100,000 SHU). Recolección silvestre en barrancas y selva baja caducifolia. Fruto pequeño redondo rojo. Alta demanda gourmet y medicinal. En proceso de domesticación como cultivo semi-intensivo.",
    ),
    CropVariety(
        crop_name="chile",
        name="Chile Poblano de Jalisco",
        region="Jalisco",
        altitude_m=1600,
        water_mm=700,
        diseases=["virus_del_mosaico_del_pepino", "botrytis"],
        adaptation_notes="Variedad adaptada a condiciones jaliscienses. Fruto grande verde oscuro, suave-medio (1,000-2,000 SHU). Usado en rajas, chile en nogada y rellenos. Ciclo 80-90 días. Requiere soporte en campo.",
    ),
    CropVariety(
        crop_name="chile",
        name="Chile de Árbol Jaliscience",
        region="Lagos de Moreno, Jalisco",
        altitude_m=1800,
        water_mm=600,
        diseases=["trips", "oidio_del_chile"],
        adaptation_notes="Chile seco fino (15,000-30,000 SHU). Planta arbustiva de 60-90 cm. Ciclo 90-100 días. Fruto rojo intenso al secar. Ingrediente clave en salsas jaliscienses y como especia seca. Alta rentabilidad por kg.",
    ),
    # Tomate — 3 local varieties
    CropVariety(
        crop_name="tomate",
        name="Jitomate Bola Criollo de Jalisco",
        region="El Grullo y Autlán, Jalisco",
        altitude_m=900,
        water_mm=800,
        diseases=["tizón_tardío", "fusarium_del_tomate"],
        adaptation_notes="Tomate redondo tipo bola adaptado a valles costeros de Jalisco. Fruto 150-200 g, alta acidez y sabor intenso. Ciclo 70-80 días en campo. Preferido por consumidores locales sobre variedades comerciales. Resistencia moderada a virus.",
    ),
    CropVariety(
        crop_name="tomate",
        name="Jitomate Cherry Silvestre Jalisciense",
        region="Costa de Jalisco",
        altitude_m=300,
        water_mm=1000,
        diseases=["virus_del_rizado_de_la_hoja", "alternaria"],
        adaptation_notes="Tomate cherry pequeño (15-20 g) de sabor dulce intenso. Altamente productivo en climas cálidos de costa. Ciclo 60-70 días. Resistente a altas temperaturas (>35°C). Creciente demanda en mercados premium y restaurantes.",
    ),
    CropVariety(
        crop_name="tomate",
        name="Jitomate Guaje de Jalisco",
        region="Jalisco",
        altitude_m=1400,
        water_mm=700,
        diseases=["phytophthora_infestans", "cladosporium"],
        adaptation_notes="Tomate tipo guaje (pera) muy productivo y carnoso. Bajo contenido de agua — ideal para salsas y cocción. Ciclo 75-85 días. Buena vida de anaquel (10-14 días) para mercados locales. Base de la salsa jalisco tradicional.",
    ),
]


AGRONOMIST_TIP_SEEDS = [
    AgronomistTip(
        crop="maiz", problem="drought",
        tip_text_es="Aplique acolchado (mulch) de rastrojo para reducir la evaporacion del suelo hasta un 40%. Mantenga una capa de 5-8 cm entre hileras.",
        source="INIFAP Jalisco", region="jalisco", season="dry",
    ),
    AgronomistTip(
        crop="maiz", problem="drought",
        tip_text_es="Riegue en la madrugada (4-6 am) para minimizar la evaporacion. En temporal, deje de regar cuando el suelo tenga humedad hasta 30 cm de profundidad.",
        source="CIMMYT", region="jalisco", season="dry",
    ),
    AgronomistTip(
        crop="maiz", problem="nutrient_deficiency",
        tip_text_es="Aplique vermicompost (2 ton/ha) en banda junto a la hilera al momento de la siembra. El nitrogeno organico se libera gradualmente evitando el lavado.",
        source="INIFAP Jalisco", region="jalisco", season="all",
    ),
    AgronomistTip(
        crop="maiz", problem="disease",
        tip_text_es="Para prevenir carbon (Ustilago maydis), use semilla criolla resistente y evite el exceso de nitrogeno sintetico. Rote con frijol o calabaza.",
        source="CIMMYT", region="jalisco", season="wet",
    ),
    AgronomistTip(
        crop="maiz", problem="water_stress",
        tip_text_es="Durante floracion y llenado de grano (etapas VT-R3), el maiz es mas sensible al estres hidrico. Garantice riego cada 7-10 dias en esta ventana critica.",
        source="INIFAP Jalisco", region="jalisco", season="wet",
    ),
    AgronomistTip(
        crop="agave", problem="drought",
        tip_text_es="El agave azul tolera sequia severa pero en los primeros 2 anos requiere un riego de apoyo mensual (20-30 L/planta) en secas. Use agua de lluvia captada.",
        source="CIATEJ", region="jalisco", season="dry",
    ),
    AgronomistTip(
        crop="agave", problem="disease",
        tip_text_es="La punta roja (Fusarium) se previene con espaciado adecuado (3x3 m) y eliminando hijuelos infectados inmediatamente. No use machetes sin desinfectar.",
        source="CIATEJ", region="jalisco", season="all",
    ),
    AgronomistTip(
        crop="agave", problem="nutrient_deficiency",
        tip_text_es="Aplique composta de cachaza o estiercol de bovino maduro (3 ton/ha/ano) en corona alrededor de la planta. El agave responde bien a materia organica de liberacion lenta.",
        source="Universidad de Guadalajara", region="jalisco", season="all",
    ),
    AgronomistTip(
        crop="frijol", problem="drought",
        tip_text_es="El frijol es sensible al estres hidrico en floracion. Si hay sequia en esta etapa, aplique un riego de emergencia de 20-25 mm. Prefiera variedades criollas de temporal.",
        source="INIFAP Jalisco", region="jalisco", season="dry",
    ),
    AgronomistTip(
        crop="frijol", problem="disease",
        tip_text_es="La antracnosis (Colletotrichum) se controla con rotacion de cultivos, semilla sana y no trabajar el campo cuando hay rocio matutino. Elimine residuos de cosecha.",
        source="INIFAP Jalisco", region="jalisco", season="wet",
    ),
    AgronomistTip(
        crop="frijol", problem="nutrient_deficiency",
        tip_text_es="El frijol es leguminosa — inocule con Rhizobium phaseoli al momento de la siembra para fijar nitrogeno atmosferico. Reduce o elimina la necesidad de nitrogeno externo.",
        source="CIMMYT", region="jalisco", season="all",
    ),
    AgronomistTip(
        crop="chile", problem="drought",
        tip_text_es="El chile requiere humedad constante — deficits en floracion causan caida de flores. Use riego por goteo (2-3 L/planta/dia) para optimizar el agua disponible.",
        source="SAGARPA Jalisco", region="jalisco", season="dry",
    ),
    AgronomistTip(
        crop="chile", problem="disease",
        tip_text_es="Para Phytophthora capsici (marchitez), mejore el drenaje del suelo, evite riego excesivo y aplique cal agricola (2 ton/ha) para elevar el pH a 6.5-7.0.",
        source="INIFAP Jalisco", region="jalisco", season="wet",
    ),
    AgronomistTip(
        crop="chile", problem="water_stress",
        tip_text_es="Aplique acolchado plastico negro o de paja para mantener humedad del suelo, reducir maleza y elevar temperatura del suelo 2-3 grados en temporada fria.",
        source="SAGARPA Jalisco", region="jalisco", season="dry",
    ),
    AgronomistTip(
        crop="tomate", problem="nutrient_deficiency",
        tip_text_es="Aplique te de compost (1:10 compost:agua, 48 horas aireado) cada 15 dias al follaje y suelo. Aporta micronutrientes biodisponibles y activa microbioma benefico.",
        source="Agricultura regenerativa Jalisco", region="jalisco", season="all",
    ),
    AgronomistTip(
        crop="tomate", problem="disease",
        tip_text_es="Para mancha bacteriana (Xanthomonas), evite el riego por aspersion, podas excesivas y use caldo bordeles (sulfato de cobre + cal) como preventivo organico.",
        source="INIFAP Jalisco", region="jalisco", season="wet",
    ),
]


def seed_agronomist_tips(db_session) -> int:
    """Load agronomist tip seed data if table is empty. Returns count inserted."""
    existing = db_session.query(AgronomistTip).count()
    if existing > 0:
        return 0
    for tip in AGRONOMIST_TIP_SEEDS:
        db_session.add(AgronomistTip(
            crop=tip.crop,
            problem=tip.problem,
            tip_text_es=tip.tip_text_es,
            source=tip.source,
            region=tip.region,
            season=tip.season,
        ))
    db_session.commit()
    return len(AGRONOMIST_TIP_SEEDS)


def seed_crop_varieties(db_session) -> int:
    """Load Jalisco/LATAM crop variety seed data if table is empty. Returns count inserted."""
    existing = db_session.query(CropVariety).count()
    if existing > 0:
        return 0
    for variety in CROP_VARIETY_SEEDS:
        db_session.add(CropVariety(
            crop_name=variety.crop_name,
            name=variety.name,
            region=variety.region,
            altitude_m=variety.altitude_m,
            water_mm=variety.water_mm,
            diseases=variety.diseases,
            adaptation_notes=variety.adaptation_notes,
        ))
    db_session.commit()
    return len(CROP_VARIETY_SEEDS)


AGRONOMIST_TIP_SEEDS = [
    # Maiz — drought
    AgronomistTip(crop="maiz", problem="drought", tip_text_es="Aplique mulch organico (zacate seco o rastrojo) alrededor de las plantas para retener humedad del suelo y reducir evaporacion hasta 40%.", source="CIMMYT", region="jalisco", season="dry"),
    AgronomistTip(crop="maiz", problem="drought", tip_text_es="Riegue en las horas frescas — antes de las 8am o despues de las 6pm — para minimizar perdidas por evaporacion.", source="INIFAP Jalisco", region="jalisco", season="dry"),
    AgronomistTip(crop="maiz", problem="drought", tip_text_es="Siembre variedades criollas adaptadas a sequia (Maiz Azul Criollo, Olotillo) que resisten estres hidrico mejor que hibridos comerciales.", source="CIMMYT", region="jalisco", season="dry"),
    # Maiz — disease
    AgronomistTip(crop="maiz", problem="disease", tip_text_es="Para prevenir tizoncillo (Fusarium), trate la semilla con Trichoderma harzianum antes de siembra — hongo benefico que compite con patogenos.", source="INIFAP Jalisco", region="jalisco", season="all"),
    AgronomistTip(crop="maiz", problem="disease", tip_text_es="Rote cultivos con frijol o calabaza cada dos ciclos para romper ciclos de plagas y enfermedades del suelo sin fungicidas.", source="CIMMYT", region="jalisco", season="all"),
    # Maiz — nutrient deficiency
    AgronomistTip(crop="maiz", problem="nutrient_deficiency", tip_text_es="Si las hojas viejas amarillan desde la punta, es deficiencia de nitrogeno. Aplique lombricomposta (1-2 ton/ha) en banda a los 15 dias de emergencia.", source="INIFAP Jalisco", region="jalisco", season="wet"),
    AgronomistTip(crop="maiz", problem="nutrient_deficiency", tip_text_es="Hojas con rayas purpuras indican deficiencia de fosforo. Incorpore huesos calcinados molidos (harina osea) 200 kg/ha al momento de siembra.", source="CIMMYT", region="jalisco", season="all"),
    # Agave — drought
    AgronomistTip(crop="agave", problem="drought", tip_text_es="El agave azul es tolerante a sequia pero durante el primer ano necesita 2-3 riegos de establecimiento. Use ollas de barro enterradas para liberacion lenta.", source="CRT — Consejo Regulador del Tequila", region="jalisco", season="dry"),
    AgronomistTip(crop="agave", problem="drought", tip_text_es="En temporada seca extrema cubra la base del agave con piedra caliza (tezontle) para reflejar calor y retener humedad nocturna del suelo.", source="Agricultores de Los Altos", region="jalisco", season="dry"),
    # Agave — disease
    AgronomistTip(crop="agave", problem="disease", tip_text_es="Para prevenir pudricion de pina (Pectobacterium agglomerans), evite dano mecanico durante deshije. Aplique cal viva en heridas para desinfectar.", source="CRT", region="jalisco", season="all"),
    AgronomistTip(crop="agave", problem="disease", tip_text_es="El picudo del agave (Scyphophorus acupunctatus) se controla con nematodos entomopatogenos (Steinernema carpocapsae). Aplicar en riego de la zona radicular.", source="INIFAP Jalisco", region="jalisco", season="wet"),
    # Frijol — disease
    AgronomistTip(crop="frijol", problem="disease", tip_text_es="Para prevenir bacteriosis (Xanthomonas), evite riego por aspersion cuando la planta esta en floracion. Use riego por goteo o surcos.", source="INIFAP Jalisco", region="jalisco", season="wet"),
    AgronomistTip(crop="frijol", problem="nutrient_deficiency", tip_text_es="Inocule la semilla con Rhizobium antes de siembra para maximizar fijacion biologica de nitrogeno. Reduce o elimina la necesidad de fertilizante nitrogenado.", source="CIMMYT", region="jalisco", season="all"),
    # Chile — water stress
    AgronomistTip(crop="chile", problem="water_stress", tip_text_es="El chile es muy sensible a encharcamiento. Use camellones altos y suelos con buen drenaje. Si hay exceso de humedad, aplique Trichoderma al suelo para prevenir damping-off.", source="SAGARPA Jalisco", region="jalisco", season="wet"),
    AgronomistTip(crop="chile", problem="drought", tip_text_es="Durante floracion y cuaje de fruto el chile necesita humedad constante. Instale riego por goteo y aplique mulch organico para evitar estres hidrico que causa caida de flores.", source="INIFAP Jalisco", region="jalisco", season="dry"),
    # Tomate — disease
    AgronomistTip(crop="tomate", problem="disease", tip_text_es="Para tizon tardio (Phytophthora infestans), aplique caldo bordelés (sulfato de cobre + cal) cada 10 dias en epoca de lluvias como preventivo organico.", source="SAGARPA Jalisco", region="jalisco", season="wet"),
    AgronomistTip(crop="tomate", problem="nutrient_deficiency", tip_text_es="Hojas con clorosis intervenal en hojas jovenes indica deficiencia de hierro — problema comun en suelos calcareos de Jalisco. Aplique quelato de hierro via foliar.", source="INIFAP Jalisco", region="jalisco", season="all"),
]


def seed_agronomist_tips(db_session) -> int:
    """Load agronomist tip seed data if table is empty. Returns count of records inserted."""
    existing = db_session.query(AgronomistTip).count()
    if existing > 0:
        return 0
    for tip in AGRONOMIST_TIP_SEEDS:
        db_session.add(AgronomistTip(
            crop=tip.crop,
            problem=tip.problem,
            tip_text_es=tip.tip_text_es,
            source=tip.source,
            region=tip.region,
            season=tip.season,
        ))
    db_session.commit()
    return len(AGRONOMIST_TIP_SEEDS)


# ---------------------------------------------------------------------------
# Farmer vocabulary — Jalisco colloquial speech patterns
# ---------------------------------------------------------------------------
FARMER_VOCABULARY_SEEDS = [
    # --- Yellowing / clorosis ---
    FarmerVocabulary(phrase="se está amarillando", formal_term_es="clorosis", likely_cause="deficiencia de nitrógeno o hierro", recommended_action="Aplicar composta madura o té de composta al suelo. Para clorosis intervenal en hojas jóvenes aplicar quelato de hierro foliar.", crop=None, symptom="yellowing"),
    FarmerVocabulary(phrase="la hoja está güera", formal_term_es="clorosis", likely_cause="deficiencia de nitrógeno", recommended_action="Incorporar composta o estiércol bien fermentado. Rotar con leguminosas para enriquecer el suelo con nitrógeno biológico.", crop="maiz", symptom="yellowing"),
    FarmerVocabulary(phrase="se pone amarillo el maíz", formal_term_es="clorosis nitrogenada", likely_cause="suelo pobre en nitrógeno orgánico", recommended_action="Aplicar estiércol composteado o harina de sangre como fuente orgánica de nitrógeno.", crop="maiz", symptom="yellowing"),
    FarmerVocabulary(phrase="las hojas se blanquean", formal_term_es="blanqueamiento foliar", likely_cause="exceso de luz directa o deficiencia de magnesio", recommended_action="Aplicar ceniza de madera (fuente de magnesio y potasio) o cal agrícola al suelo.", crop=None, symptom="yellowing"),
    # --- Pest / plaga ---
    FarmerVocabulary(phrase="tiene plaga", formal_term_es="infestación de plagas", likely_cause="insectos plaga o patógenos no identificados", recommended_action="Identificar el insecto o patógeno específico. Aplicar extracto de nim (azadiractina) o caldo sulfocálcico como primera respuesta orgánica.", crop=None, symptom="pest"),
    FarmerVocabulary(phrase="está lleno de bichos", formal_term_es="infestación de insectos", likely_cause="aphidos, trips, mosca blanca o gusano cogollero", recommended_action="Liberar insectos benéficos (crisopa, catarina). Aplicar jabón potásico o extracto de ajo y chile.", crop=None, symptom="pest"),
    FarmerVocabulary(phrase="lo está comiendo el gusano", formal_term_es="daño por lepidópteros", likely_cause="gusano cogollero (Spodoptera frugiperda) u oruga defoliadora", recommended_action="Aplicar Bacillus thuringiensis (Bt) en las primeras horas de la mañana. Revisar el cogollo diariamente.", crop="maiz", symptom="pest"),
    FarmerVocabulary(phrase="le cayó el piojo", formal_term_es="infestación de áfidos", likely_cause="áfidos chupadores de savia", recommended_action="Aplicar jabón potásico diluido (2%) o caldo de ajo-chile. Conservar vegetación arvense que alberga enemigos naturales.", crop=None, symptom="pest"),
    FarmerVocabulary(phrase="se lo está comiendo la hormiga", formal_term_es="daño por hormigas cortadoras", likely_cause="hormigas arrieras (Atta spp.)", recommended_action="Aplicar polvo de tierra de diatomeas alrededor de la planta. Localizar y destruir el hormiguero con agua hirviendo.", crop=None, symptom="pest"),
    # --- Drought / water stress ---
    FarmerVocabulary(phrase="le falta agua", formal_term_es="estrés hídrico", likely_cause="déficit de humedad en el suelo", recommended_action="Aplicar riego profundo y reducido en frecuencia. Cubrir el suelo con mulch orgánico para retener humedad.", crop=None, symptom="drought"),
    FarmerVocabulary(phrase="se está secando", formal_term_es="marchitamiento por sequía", likely_cause="estrés hídrico severo o daño radicular", recommended_action="Regar inmediatamente con agua tibia. Agregar composta para mejorar capacidad de retención hídrica del suelo.", crop=None, symptom="drought"),
    FarmerVocabulary(phrase="está muy resseca la tierra", formal_term_es="suelo seco compactado", likely_cause="compactación superficial y pérdida de materia orgánica", recommended_action="Escarificar superficialmente y aplicar composta. Implantar labranza mínima para conservar humedad.", crop=None, symptom="drought"),
    FarmerVocabulary(phrase="la hoja está colgada", formal_term_es="turgencia pérdida, marchitez hídrica", likely_cause="déficit de agua en la planta", recommended_action="Regar de inmediato. Aplicar mulch grueso (10 cm) para reducir evaporación. Verificar que el riego llegue a la zona radicular.", crop=None, symptom="drought"),
    # --- Dying / plant death ---
    FarmerVocabulary(phrase="se está petateando", formal_term_es="muerte de la planta", likely_cause="daño radicular por encharcamiento, hongo de suelo o estrés severo", recommended_action="Revisar raíces. Si hay pudredumbre, aplicar Trichoderma al suelo. Mejorar drenaje y agregar materia orgánica.", crop=None, symptom="dying"),
    FarmerVocabulary(phrase="ya se peló", formal_term_es="planta muerta o pérdida de cultivo", likely_cause="estrés severo acumulado, helada, plaga o enfermedad no controlada", recommended_action="Documentar la causa antes de remover la planta. Rotar cultivo en esa zona. Incorporar abono verde para recuperar el suelo.", crop=None, symptom="dying"),
    FarmerVocabulary(phrase="se dobló la planta", formal_term_es="acame o volcamiento", likely_cause="viento fuerte, raíces débiles o suelo blando por exceso de lluvia", recommended_action="Aporcar tierra alrededor del tallo para dar soporte. En maíz, el acame tardío no requiere intervención urgente.", crop="maiz", symptom="dying"),
    # --- Tip blight / burn ---
    FarmerVocabulary(phrase="se secó la punta", formal_term_es="quemado de ápice foliar", likely_cause="deficiencia de potasio, salinidad alta o estrés térmico", recommended_action="Aplicar ceniza de madera (fuente de potasio) o agua de lavado de ceniza foliar. Riegos más frecuentes en calor extremo.", crop=None, symptom="tip_blight"),
    FarmerVocabulary(phrase="la punta está negra", formal_term_es="necrosis apical", likely_cause="Botrytis spp. o deficiencia de calcio", recommended_action="Aplicar caldo bordelés diluido. Mejorar ventilación entre plantas y evitar mojar el follaje al regar.", crop=None, symptom="tip_blight"),
    # --- Disease / fungal ---
    FarmerVocabulary(phrase="tiene hongos", formal_term_es="enfermedad fúngica", likely_cause="Fusarium, Botrytis, Phytophthora u otro hongo según síntoma", recommended_action="Aplicar caldo sulfocálcico o caldo bordelés como fungicida orgánico. Mejorar drenaje y reducir humedad foliar.", crop=None, symptom="disease"),
    FarmerVocabulary(phrase="se está pudriendo la raíz", formal_term_es="pudrición radicular", likely_cause="Phytophthora o Pythium por encharcamiento", recommended_action="Mejorar drenaje inmediatamente. Aplicar Trichoderma harzianum al suelo. Reducir riego y evitar compactación.", crop=None, symptom="disease"),
    FarmerVocabulary(phrase="tiene manchas café", formal_term_es="lesiones necróticas foliares", likely_cause="Alternaria, Cercospora u otro hongo foliar", recommended_action="Retirar hojas infectadas. Aplicar caldo bordelés cada 10 días como preventivo en época de lluvias.", crop=None, symptom="disease"),
    FarmerVocabulary(phrase="sale espuma en el maguey", formal_term_es="salivazo o insecto chupador en agave", likely_cause="picudo del agave (Scyphophorus acupunctatus) o cochinilla", recommended_action="Retirar plantas muy afectadas para evitar propagación. Aplicar neem o tierra de diatomeas en la base del agave.", crop="agave", symptom="disease"),
    FarmerVocabulary(phrase="tiene manchas blancas", formal_term_es="oidio o mildiu polvoriento", likely_cause="Erysiphe spp. u hongo oidio", recommended_action="Aplicar bicarbonato de sodio diluido (5 g/L) + unas gotas de jabón. En frijol y chile es común en secas.", crop=None, symptom="disease"),
    # --- Nutrient deficiency ---
    FarmerVocabulary(phrase="le falta fuerza", formal_term_es="deficiencia nutricional generalizada", likely_cause="suelo empobrecido o pH inadecuado", recommended_action="Analizar el suelo antes de actuar. Aplicar composta madura y estiércol. Si el pH es extremo, cal agrícola para suelos ácidos o azufre para alcalinos.", crop=None, symptom="nutrient"),
    FarmerVocabulary(phrase="no agarra", formal_term_es="falla en establecimiento o nutrición", likely_cause="suelo compactado, deficiencia de fósforo o mal trasplante", recommended_action="Agregar harina de hueso (fósforo orgánico) en el hoyo de trasplante. Aplicar micorrizas para mejorar absorción radical.", crop=None, symptom="nutrient"),
    FarmerVocabulary(phrase="no está creciendo", formal_term_es="enanismo o desarrollo retrasado", likely_cause="deficiencia de nitrógeno, compactación o estrés", recommended_action="Aplicar té de composta o worm casting. Escarificar el suelo para airearlo. Revisar si hay plagas radiculares.", crop=None, symptom="nutrient"),
    # --- Overwatering / flooding ---
    FarmerVocabulary(phrase="le cayó mucha agua", formal_term_es="anegamiento temporal", likely_cause="exceso de lluvia o riego", recommended_action="Abrir surcos para drenar el exceso. Aplicar cal al suelo para prevenir hongos. Evitar pisar el suelo mojado para no compactarlo.", crop=None, symptom="flooding"),
    FarmerVocabulary(phrase="está encharcado", formal_term_es="encharcamiento persistente", likely_cause="mal drenaje o suelo arcilloso compactado", recommended_action="Formar camellones o bordes de drenaje. Incorporar materia orgánica gruesa para mejorar la estructura del suelo.", crop=None, symptom="flooding"),
    # --- Harvest / quality ---
    FarmerVocabulary(phrase="no llenó bien el elote", formal_term_es="llenado deficiente de grano", likely_cause="estrés hídrico o nutricional en floración o deficiencia de boro", recommended_action="En siguiente ciclo, asegurar agua en floración. Aplicar composta de calidad antes de siembra.", crop="maiz", symptom="harvest"),
    FarmerVocabulary(phrase="salió poco grano", formal_term_es="rendimiento bajo", likely_cause="estrés múltiple (agua, nutrición, plaga) durante llenado de grano", recommended_action="Documentar el momento del estrés para el siguiente ciclo. Mejorar suelo con abonos orgánicos y rotación de cultivos.", crop="maiz", symptom="harvest"),
]


def seed_farmer_vocabulary(db_session) -> int:
    """Load farmer vocabulary seed data if table is empty. Returns count of records inserted."""
    existing = db_session.query(FarmerVocabulary).count()
    if existing > 0:
        return 0
    for entry in FARMER_VOCABULARY_SEEDS:
        db_session.add(FarmerVocabulary(
            phrase=entry.phrase,
            formal_term_es=entry.formal_term_es,
            likely_cause=entry.likely_cause,
            recommended_action=entry.recommended_action,
            crop=entry.crop,
            symptom=entry.symptom,
        ))
    db_session.commit()
    return len(FARMER_VOCABULARY_SEEDS)
