# ANEXO F — PLAN DE DESARROLLO TECNOLÓGICO (TIPO B)

**Título:** Cerebro: Plataforma de Inteligencia Agrícola para la Validación de Conocimiento Ecológico Tradicional mediante Sensores de Precisión en Jalisco

**Sector Estratégico:** Agroindustria
**Reto Social Principal:** II.I — Adaptación del campo jalisciense al cambio climático; conservación de suelos; monitoreo de plagas
**Reto Social Secundario:** II.II — Aprovechamiento sustentable del recurso hídrico en el campo
**TRL Inicial:** 3 → **TRL Final:** 4
**Duración:** 12 meses
**Monto COECYTJAL:** $2,000,000.00 MXN (70%)
**Aportación concurrente:** $857,143.00 MXN (30%)

---

## 1. Resumen del proyecto (máx. 250 palabras)

Cerebro es una plataforma de inteligencia agrícola que integra datos de drones multiespectrales, sensores térmicos, análisis de suelo y datos meteorológicos para generar recomendaciones basadas en prácticas de conocimiento ecológico tradicional (TEK) — milpa, rotación con leguminosas, composta de monte, abono verde — validadas con datos de sensores.

La hipótesis central es que las prácticas TEK, cuando se optimizan con datos de precisión, producen resultados medibles en salud del suelo, eficiencia hídrica y rendimiento que igualan o superan a la agricultura convencional basada en insumos sintéticos, con costos de insumos significativamente menores.

El prototipo actual (TRL 3) cuenta con 221 pruebas automatizadas, motor de puntuación de salud compuesta (NDVI + suelo + tendencia), base de conocimiento con 10 métodos de fertilización orgánica y 8 prácticas ancestrales mexicanas, recomendaciones de tratamiento 100% orgánico, planificador de rotación de cultivos, y optimizador de riego basado en datos.

La comunicación con agricultores se realizará vía WhatsApp en español sencillo con indicadores de color (rojo/amarillo/verde), eliminando barreras de alfabetización digital. El sistema no enseña prácticas ancestrales — las hace económicamente viables al demostrar con datos que funcionan.

El proyecto busca validar el sistema en entorno controlado (ITESO) y parcelas piloto en Valles Centrales de Jalisco, avanzando de TRL 3 a TRL 4. La vinculación con ITESO provee el marco académico para la validación TEK-sensor y la publicación de resultados.

---

## 2. Estado del arte y de la técnica, antecedentes tecnológicos

### Agricultura de precisión en Jalisco

La agricultura de precisión en México ha avanzado principalmente en operaciones agroindustriales de gran escala (berries, aguacate de exportación), donde empresas como Driscoll's utilizan tecnología multiespectral y térmica para optimizar rendimientos. Sin embargo, estos sistemas:

- Requieren inversiones de $500K+ USD en infraestructura tecnológica
- Dependen de plataformas diseñadas para operadores angloparlantes con alta alfabetización digital
- Ignoran completamente las prácticas agrícolas tradicionales como factor de optimización
- No están disponibles para pequeños y medianos agricultores (15-80 ha)

### Conocimiento Ecológico Tradicional (TEK) en la literatura

La integración de TEK con tecnología de sensores es un campo emergente con publicaciones crecientes:

- **Toledo & Barrera-Bassols (2008)** documentan la "memoria biocultural" de comunidades agrícolas mexicanas, incluyendo prácticas de manejo de suelo que mantienen la productividad sin insumos sintéticos.
- **Altieri (2018)** demuestra que sistemas agroecológicos basados en policultivos (como la milpa) producen rendimientos totales por hectárea comparables o superiores al monocultivo, con costos de insumos 40-60% menores.
- **Perfecto, Vandermeer & Wright (2019)** establecen que la biodiversidad funcional en agroecosistemas tradicionales proporciona servicios ecosistémicos (control de plagas, polinización, retención de agua) que sustituyen insumos químicos.

### Brecha identificada

No existe actualmente una plataforma que:
1. Valide prácticas TEK con datos cuantitativos de sensores (NDVI, térmico, suelo)
2. Comunique resultados a agricultores con baja alfabetización digital
3. Genere un ciclo cerrado de recomendación → aplicación → medición → mejora
4. Sea económicamente accesible para pequeños agricultores

Cerebro ocupa esta brecha.

### Antecedentes tecnológicos del prototipo

El prototipo Cerebro (TRL 3) fue desarrollado entre enero y marzo de 2026 utilizando una metodología de desarrollo autónomo (AutoAgent) que permitió la construcción de 221 pruebas automatizadas y 51 endpoints funcionales en un periodo acelerado. La plataforma está construida sobre Python/FastAPI con procesamiento de imágenes NumPy. La integración con WhatsApp Business API está diseñada y será implementada durante el proyecto.

---

## 3. Problemática del reto general y/o específico asociado al proyecto

### Reto II.I — Adaptación del campo al cambio climático y conservación de suelos

**Dato clave:** 84% de los municipios de Jalisco reportaron condiciones de sequía en 2024 (CONAGUA, Monitor de Sequía de México).

La degradación del suelo agrícola en Jalisco avanza por tres vectores simultáneos:

1. **Pérdida de materia orgánica:** La agricultura intensiva basada en monocultivo y fertilizantes sintéticos ha reducido la materia orgánica promedio de los suelos de 4.5% a menos de 2% en tres décadas (INIFAP, 2022). Sin materia orgánica, el suelo pierde capacidad de retener agua.

2. **Erosión de conocimiento:** Las prácticas tradicionales de manejo de suelo (milpa, rotación, composta de monte) están siendo abandonadas por una generación de agricultores que las percibe como "atrasadas" frente a insumos sintéticos, a pesar de evidencia científica que demuestra su efectividad.

3. **Exclusión tecnológica:** Las herramientas de diagnóstico de suelo y cultivo están diseñadas para agroindustria, no para el agricultor de 42 hectáreas que sabe leer su tierra pero no una aplicación móvil.

### Reto II.II — Aprovechamiento sustentable del agua

**Dato clave:** 57% del agua utilizada en agricultura jalisciense se desperdicia por riego ineficiente (CONAGUA, 2023).

Los agricultores riegan por calendario y costumbre, no por datos. Un sistema que integre datos térmicos (estrés hídrico visible desde drone), meteorológicos (pronóstico de lluvia) y de suelo (capacidad de retención según textura) puede reducir el consumo hídrico entre 15-30% sin afectar rendimiento.

---

## 4. Nivel de Madurez de la Tecnología

### TRL 3 — Prueba de concepto funcional (actual)

Evidencia documentada:

| Componente | Estado | Evidencia |
|-----------|--------|-----------|
| Motor NDVI | Funcional | 22 pruebas automatizadas. Procesa bandas NIR+Red, clasifica en 5 zonas de salud. |
| Motor térmico | Funcional | 5 pruebas. Detecta zonas de estrés hídrico (variación >5°C). |
| Puntuación de salud compuesta | Funcional | 28 pruebas. Score 0-100 integrando NDVI + suelo + tendencia con degradación graceful. |
| Recomendaciones de tratamiento | Funcional | 5 pruebas. 100% orgánico, formato en español con costo/ha en MXN. |
| Base de conocimiento TEK | Funcional | 10 métodos orgánicos + 8 prácticas ancestrales + 11 cultivos de Jalisco. |
| Rotación de cultivos | Funcional | 4 pruebas. Plan de 3 temporadas con lógica de leguminosas. |
| Optimizador de riego | Funcional | 4 pruebas. Calendario de 7 días desde clima + suelo + térmico. |
| Detección de anomalías | Funcional | Alertas automáticas por caída de salud. |
| Panel de inteligencia | Funcional | Dashboard para investigadores con tendencias cruzadas entre granjas. |
| Autenticación por roles | Funcional | 5 pruebas. Admin/investigador/agricultor con JWT. |
| **Total pruebas automatizadas** | **221** | Suite completa ejecutable con `pytest` |

### TRL 4 — Validación en entorno controlado (meta)

Para alcanzar TRL 4, Cerebro debe demostrar:
1. Correlación medible entre predicciones del motor de salud y rendimiento real en parcelas
2. Funcionamiento del ciclo completo: vuelo → procesamiento → recomendación → WhatsApp → acción del agricultor → medición de resultado
3. Validación en al menos 5 parcelas con datos completos de una temporada
4. Publicación de resultados en formato académico revisado

---

## 5. Búsqueda tecnológica y análisis relacionado con el prototipo a desarrollar

### Plataformas existentes de agricultura de precisión

| Plataforma | Origen | Fortaleza | Limitación para nuestro contexto |
|-----------|--------|-----------|----------------------------------|
| CropX | Israel/EE.UU. | Sensores de suelo IoT | Sin soporte español, sin TEK, precio prohibitivo para pequeños agricultores |
| Kilimo | Argentina | Recomendaciones de riego via SMS | No integra TEK, no usa drones, limitado a riego |
| Prospera (Bayer) | Alemania | IA para detección de plagas | Propiedad de agroindustria, promueve insumos sintéticos |
| FarmLogs | EE.UU. | Gestión de granja completa | Diseñado para farms >500 acres, inglés solamente |

### Diferenciador de Cerebro

Ninguna plataforma existente:
- Integra TEK como variable de optimización (no solo como folklore)
- Comunica vía WhatsApp con indicadores de color para agricultores con baja alfabetización
- Genera un dataset de correlaciones TEK-sensor publicable y reutilizable
- Tiene raíces en Jalisco y comprende el contexto de cultivos locales (agave, maíz temporal, aguacate)

### Propiedad intelectual

- **Algoritmos de Cerebro:** Registro de derechos de autor ante INDAUTOR (en proceso)
- **Búsqueda tecnológica:** Se realizará búsqueda formal ante autoridad institucional (ITESO) como evidencia para el proyecto

---

## 6. Relación de la tecnología o prototipo con el Reto Social a solucionar

### Cadena de impacto

```
RETO: Suelos degradados + agua desperdiciada + TEK abandonado
                            ↓
CEREBRO: Sensores miden → IA procesa → TEK validado → WhatsApp comunica
                            ↓
RESULTADO: Agricultor aplica práctica ancestral CON datos que demuestran que funciona
                            ↓
IMPACTO: Suelo recupera materia orgánica → retiene más agua → menos riego → más rendimiento
```

**Específicamente:**

1. **Conservación de suelo (II.I):** Cerebro mide materia orgánica, pH y nutrientes antes/después de aplicar prácticas TEK (milpa, composta de monte, rotación con leguminosas). El agricultor ve en su WhatsApp: "Su suelo subió de 2.1% a 2.8% de materia orgánica después de la rotación con frijol. [SALUD NORMAL 🟢]"

2. **Eficiencia hídrica (II.II):** El optimizador de riego integra datos térmicos del dron + pronóstico meteorológico + textura del suelo para recomendar cuándo y cuánto regar. Resultado: "Don Carlos, no riegue hoy — lluvia pronosticada mañana. Ahorro estimado: 15,000 litros."

3. **Monitoreo de plagas (II.I):** La detección de anomalías en NDVI identifica zonas con patrones de estrés consistentes con plagas conocidas de Jalisco, y recomienda tratamientos biológicos (Beauveria bassiana, Trichoderma) antes de que el daño sea visible.

---

## 7. Objetivos del proyecto

### Objetivo general

Validar en entorno controlado (ITESO) y parcelas piloto (Valles Centrales) la plataforma Cerebro, demostrando que la integración de sensores de precisión con conocimiento ecológico tradicional produce recomendaciones que mejoran mediblemente la salud del suelo, la eficiencia hídrica y el rendimiento de cultivos.

### Objetivos específicos

1. Validar el motor de puntuación de salud en ≥5 parcelas, correlacionando predicciones con rendimiento real (R² ≥ 0.70).
2. Documentar la efectividad de ≥8 prácticas TEK mediante mediciones de suelo antes/después con sensores.
3. Demostrar ≥15% de reducción en consumo hídrico en parcelas piloto con optimizador de riego.
4. Validar WhatsApp como canal de transferencia de inteligencia agrícola con ≥10 agricultores.
5. Publicar ≥1 artículo científico con dataset de correlaciones TEK-sensor.

---

## 8. Justificación técnica

### ¿Por qué esta tecnología es la solución adecuada?

1. **Drones multiespectrales son la herramienta correcta.** A diferencia de imágenes satelitales (resolución 10m, revisita 5 días), el Mavic 3 Multispectral captura a 3cm/pixel con frecuencia semanal, permitiendo detectar estrés en etapas tempranas cuando la intervención aún es posible.

2. **WhatsApp es la interfaz correcta.** No existe curva de aprendizaje — los agricultores de Jalisco ya usan WhatsApp diariamente. El sistema utiliza indicadores de color (rojo/amarillo/verde) como lenguaje primario, antes que cualquier número. Los mensajes tienen sentido leídos en voz alta — porque muchos agricultores comparten la pantalla del teléfono.

3. **TEK es el marco correcto.** No proponemos nuevas prácticas — validamos las que los agricultores ya conocen. La confianza se construye cuando Cerebro confirma con datos lo que Don Carlos ya sabe por experiencia: "Sí, la cal ayuda a subir el pH. El sensor muestra pH 6.1 — vamos bien para el ajo."

4. **La arquitectura es escalable.** El prototipo procesa datos de campo en segundos, no horas. 221 pruebas automatizadas garantizan que cada actualización no rompe funcionalidad existente. El sistema está diseñado para 1 granja o 170 granjas con la misma base de código.

---

## 9. Planteamiento de Maduración Tecnológica

### De TRL 3 a TRL 4: qué falta demostrar

| TRL 3 (actual) | TRL 4 (meta) | Cómo lo demostramos |
|----------------|--------------|---------------------|
| Algoritmos funcionan con datos sintéticos | Algoritmos funcionan con datos reales de campo | Vuelos quincenales en parcelas + análisis de suelo de laboratorio |
| WhatsApp envía mensajes | Agricultores entienden y actúan según mensajes | Estudio de usabilidad con ≥10 agricultores |
| Recomendaciones son técnicamente correctas | Recomendaciones producen mejoras medibles | Comparativa antes/después en ≥5 parcelas |
| Sistema opera en computadora de desarrollo | Sistema opera en producción con datos concurrentes | Despliegue en servidor con datos reales de múltiples granjas |
| Base de conocimiento compilada de literatura | Base de conocimiento validada con datos locales | Correlaciones TEK-sensor documentadas y publicadas |

### Riesgos y mitigación

| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| Temporada de lluvias irregular (La Niña) | Media | Parcelas en diferentes microclimas de Valles Centrales |
| Agricultores no responden vía WhatsApp | Baja | Selección de agricultores con relación previa, incentivo económico |
| Datos de dron insuficientes para correlación | Baja | Frecuencia quincenal garantiza ≥10 puntos de datos por parcela en 6 meses |
| ITESO no puede asignar investigador SNII | Media | Investigador alternativo de UdeG o CIATEJ |

---

## 10. Objetivos y actividades

| # | Actividad | Responsable | Meses | Entregable |
|---|-----------|-------------|-------|-----------|
| 1 | Calibración de sensores y algoritmos en ITESO | Resp. Técnico + Seb | 1-2 | Informe de calibración |
| 2 | Selección de parcelas y línea base de suelo | Equipo CultivOS + Resp. Técnico | 1-2 | Análisis de suelo base para ≥5 parcelas |
| 3 | Integración WhatsApp Business API | Seb + Mubeen | 2-3 | MVP chatbot funcionando |
| 4* | Diseño experimental de validación TEK-sensor | ITESO (vinculación) | 2-3 | Protocolo experimental aprobado |
| 5 | Primer ciclo de vuelos NDVI + térmico | Piloto AFAC (servicio externo) | 3-4 | Dataset de correlaciones iniciales |
| 6 | Implementación de prácticas TEK en parcelas | Agricultores + Resp. Técnico | 4-6 | Registro de prácticas aplicadas |
| 7 | Monitoreo quincenal durante temporal | Piloto AFAC + Sistema Cerebro | 6-8 | Datos de eficiencia hídrica |
| 8 | Cosecha y medición de rendimiento | Agricultores + Resp. Técnico | 8-10 | Dataset rendimiento vs. predicciones |
| 9* | Análisis estadístico y calibración de modelo | ITESO (vinculación) | 10-11 | Modelo calibrado con R² y MAE |
| 10* | Publicación y transferencia de dataset | ITESO + Seb | 11-12 | Artículo + dataset abierto |

*Actividades de vinculación con ITESO

---

## 11. Cronograma

| Actividad | M1 | M2 | M3 | M4 | M5 | M6 | M7 | M8 | M9 | M10 | M11 | M12 |
|-----------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:---:|:---:|:---:|
| 1. Calibración ITESO | ██ | ██ | | | | | | | | | | |
| 2. Selección parcelas + suelo base | ██ | ██ | | | | | | | | | | |
| 3. WhatsApp API | | ██ | ██ | | | | | | | | | |
| 4. Diseño experimental* | | ██ | ██ | | | | | | | | | |
| 5. Vuelos NDVI + térmico | | | ██ | ██ | | | | | | | | |
| 6. Implementación TEK | | | | ██ | ██ | ██ | | | | | | |
| 7. Monitoreo temporal | | | | | | ██ | ██ | ██ | | | | |
| 8. Cosecha + rendimiento | | | | | | | | ██ | ██ | ██ | | |
| 9. Análisis estadístico* | | | | | | | | | | ██ | ██ | |
| 10. Publicación + transferencia* | | | | | | | | | | | ██ | ██ |

---

## 12. Recursos Necesarios

### 12.1 Equipo de trabajo

| Rol | Nombre | Perfil | Dedicación |
|-----|--------|--------|-----------|
| Representante Legal | Sebastián Sánchez García | CEO CultivOS Mexico S.A. de C.V. Ingeniero de software. Guadalajara-Toronto. | 50% |
| Responsable Técnico | [Por designar — investigador ITESO/SNII] | Perfil en agroecología, ciencias del suelo o ingeniería agrícola | 30% |
| Responsable Administrativo | Sebastián Sánchez García + contador externo | Gestión financiera, reportes fiscales, documentación COECYTJAL | 20% |
| CTO | Mubeen Zulfiqar | MSc CS Waterloo. Arquitectura de plataforma Cerebro. | 30% |
| Operador de drones | Piloto AFAC certificado (por contratar) | Vuelos NDVI y térmicos en parcelas piloto. Subcontratado como servicio externo. | Por vuelo |

### 12.2 Infraestructura y equipamiento del sujeto de apoyo

| Equipo | Valor estimado | Estado |
|--------|---------------|--------|
| Plataforma Cerebro (software) | Desarrollo propio | Funcional (TRL 3), 221 pruebas automatizadas |
| Equipo de cómputo | $50,000 MXN | Existente |

**Nota:** El equipo de drones (Mavic 3 Multispectral, Mavic 3 Thermal, Agras T100) se adquirirá mediante financiamiento separado (Impulsora de Innovación). Para efectos de este proyecto, los vuelos de dron se contratan como servicio externo especializado con piloto AFAC certificado.

### 12.3 Infraestructura y equipamiento externo

| Recurso | Proveedor | Uso |
|---------|-----------|-----|
| Jardín campus + laboratorio de drones | ITESO | Calibración TRL 4, entorno controlado |
| Parcelas experimentales | 3-5 agricultores de Valles Centrales | Validación en campo |
| Laboratorio de análisis de suelo | Laboratorio certificado Jalisco | Análisis fisicoquímicos |

---

## 13. Impactos esperados del proyecto

### Impacto científico-tecnológico
- Dataset abierto de correlaciones TEK-sensor (primero en su tipo para Jalisco)
- Modelo de puntuación de salud calibrado con datos reales (R², MAE publicados)
- Metodología replicable para validación de prácticas ancestrales con sensores

### Impacto social
- 10-20 agricultores de Valles Centrales reciben inteligencia agrícola vía WhatsApp
- Validación de que prácticas ancestrales son económicamente viables con datos
- Reducción medible de uso de agua en parcelas piloto

### Impacto económico
- Ahorro potencial estimado de $414,000 MXN por granja/año para granjas que utilicen la plataforma (reducción de agua + insumos sintéticos + mejora de rendimiento). A validar durante el proyecto.
- Modelo de negocio validado para escalamiento post-proyecto (20 granjas Año 1)
- Reducción de dependencia de insumos sintéticos importados

### Impacto ambiental
- Conservación de suelos agrícolas mediante prácticas regenerativas medibles
- Reducción de contaminación por agroquímicos
- Contribución a la adaptación climática del campo jalisciense

---

## 14. Resultados e indicadores de Proyecto Tipo B

### 14.1 Obligatorias

| Indicador | Meta | Método de verificación |
|-----------|------|----------------------|
| TRL alcanzado | 4 | Informe de validación en entorno controlado |
| Parcelas piloto con datos completos | ≥ 5 | Registro con suelo base + vuelos + rendimiento |
| Precisión del motor de salud | R² ≥ 0.70 | Análisis estadístico correlación predicción-rendimiento |
| Reducción de consumo hídrico | ≥ 15% | Comparativa litros/ha con y sin optimizador |
| Prácticas TEK validadas con datos | ≥ 8 | Base de datos con mediciones antes/después |
| Agricultores alcanzados vía WhatsApp | ≥ 10 | Registro de mensajes enviados/respondidos |
| Artículo científico | ≥ 1 | Sometido a revista indexada |
| Dataset abierto publicado | 1 | Repositorio con datos TEK-sensor |
| Estudiantes formados | ≥ 2 | Tesis de maestría vinculadas |
| Registro de propiedad intelectual | 1 | Registro de derechos de autor (software) ante INDAUTOR |

---

## 15. Otros logros

- Fortalecimiento de la relación CultivOS-ITESO como modelo de vinculación empresa-academia en AgTech
- Creación de capacidades locales en análisis de datos agrícolas con sensores de precisión
- Base para solicitud futura a FODECIJAL Tipo C (TRL 5-6) para validación en entorno real ampliado
- Modelo replicable para otros estados con retos agrícolas similares (Michoacán, Guanajuato, Sinaloa)
- Contribución al catálogo de prácticas regenerativas de Jalisco con evidencia cuantitativa

---

*Documento preparado por CultivOS Mexico S.A. de C.V.*
*Guadalajara, Jalisco — Marzo 2026*
