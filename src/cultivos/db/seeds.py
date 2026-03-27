"""Seed data for the cultivOS knowledge base."""

from cultivos.db.models import AncestralMethod, Fertilizer


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
