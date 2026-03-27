# FODECIJAL 2026 — Proyecto en Extenso (Tipo B)
# Plan de Desarrollo Tecnológico

**Título del Proyecto:** Cerebro: Plataforma de Inteligencia Agrícola para la Validación de Conocimiento Ecológico Tradicional mediante Sensores de Precisión en Jalisco

**Sector Estratégico:** Agroindustria

**Reto Social:** II.I — Adaptación del campo jalisciense a las condiciones medioambientales y cambio climático, mediante la recuperación, tratamiento y conservación de suelos agrícolas; prevención, monitoreo y control de enfermedades y plagas de cultivos.

**Reto Social Secundario:** II.II — Aprovechamiento sustentable del recurso hídrico en el campo y en comunidades rurales.

**TRL Inicial:** 3 (Prueba de concepto funcional)
**TRL Final:** 4 (Validación en entorno controlado)

**Duración:** 12 meses

**Monto solicitado a COECYTJAL:** $2,000,000.00 MXN (70%)
**Aportación concurrente (CultivOS + ITESO):** $857,143.00 MXN (30%)
**Monto total del proyecto:** $2,857,143.00 MXN

---

## 1. ANTECEDENTES Y JUSTIFICACIÓN

### 1.1 Contexto del problema

Jalisco enfrenta una crisis agrícola multidimensional:

- **84% de los municipios de Jalisco reportaron condiciones de sequía en 2024** (CONAGUA, Monitor de Sequía de México). La eficiencia hídrica ya no es una aspiración — es una necesidad de supervivencia.

- **57% del agua utilizada en agricultura se desperdicia** por riego ineficiente (CONAGUA, 2023). Los agricultores riegan por costumbre y calendario, no por datos.

- **La degradación del suelo avanza silenciosamente.** La agricultura intensiva basada en monocultivos y fertilizantes sintéticos ha reducido la materia orgánica promedio de los suelos agrícolas de Jalisco de 4.5% a menos de 2% en las últimas tres décadas (INIFAP, 2022). Sin materia orgánica, el suelo pierde su capacidad de retener agua — un círculo vicioso que agrava la sequía.

- **El conocimiento ecológico tradicional (TEK) se está perdiendo.** Prácticas ancestrales como la milpa (policultivo maíz-frijol-calabaza), la rotación con abono verde, y el uso de composta de monte han sido desplazadas por insumos sintéticos. Sin embargo, estudios recientes (Altieri, 2018; Vandermeer, 2012) demuestran que estos sistemas producen rendimientos comparables con costos de insumos 40-60% menores y beneficios medibles en salud del suelo.

- **Los pequeños agricultores están excluidos de la agricultura de precisión.** Las plataformas existentes requieren aplicaciones móviles, alfabetización digital y conectividad estable — barreras insuperables para agricultores como Don Carlos (42 ha, Valles Centrales) que sabe leer su tierra pero no una pantalla.

### 1.2 Oportunidad científica-tecnológica

El proyecto Cerebro propone una hipótesis comprobable: **las prácticas de conocimiento ecológico tradicional (TEK), cuando se validan y optimizan con datos de sensores de precisión (NDVI multiespectral, térmico, análisis de suelo, meteorología), producen resultados medibles en salud del suelo, eficiencia hídrica y rendimiento que son iguales o superiores a los de la agricultura convencional basada en insumos sintéticos.**

Esta hipótesis se valida mediante un sistema de inteligencia artificial que:
1. **Recopila** datos de múltiples fuentes (drones multiespectrales, sensores térmicos, análisis de suelo, datos meteorológicos, observaciones de agricultores vía WhatsApp)
2. **Procesa** con algoritmos de puntuación de salud que integran NDVI, estrés térmico, composición del suelo y tendencias temporales
3. **Recomienda** prácticas regenerativas y ancestrales específicas al tipo de cultivo, temporada y condición del suelo
4. **Mide** el impacto de cada recomendación comparando la salud del campo antes y después del tratamiento
5. **Comunica** resultados al agricultor en español sencillo vía WhatsApp, con indicadores de color (rojo/amarillo/verde) que no requieren alfabetización

### 1.3 Estado del arte

El prototipo Cerebro (TRL 3) ya cuenta con:
- **221 pruebas automatizadas** que validan el funcionamiento del sistema
- **51 endpoints de API** funcionales en 18 módulos
- Motor de puntuación de salud compuesta (NDVI + suelo + tendencia temporal)
- Base de datos de 10 métodos de fertilización orgánica + 8 prácticas ancestrales mexicanas
- 11 tipos de cultivo de Jalisco documentados con temporadas de siembra/cosecha
- Sistema de recomendaciones de tratamiento (100% orgánico)
- Planificador de rotación de cultivos con lógica de leguminosas y cobertura
- Optimizador de riego basado en clima + suelo + estrés térmico
- Detección de anomalías en salud de cultivos
- Panel de inteligencia para investigadores (vista de solo lectura)
- Sistema de autenticación con roles (administrador/investigador/agricultor)

---

## 2. OBJETIVOS

### 2.1 Objetivo general

Validar en entorno controlado la plataforma de inteligencia agrícola Cerebro, demostrando que la integración de datos de sensores de precisión con conocimiento ecológico tradicional (TEK) produce recomendaciones que mejoran mediblemente la salud del suelo, la eficiencia hídrica y el rendimiento de cultivos en parcelas piloto de Jalisco.

### 2.2 Objetivos específicos

1. **Validar el motor de puntuación de salud** en al menos 5 parcelas piloto, correlacionando las predicciones del sistema con datos reales de rendimiento al final de la temporada (temporal 2026).

2. **Documentar la efectividad de prácticas TEK** (milpa, rotación con leguminosas, composta de monte, abono verde) mediante mediciones comparativas de suelo antes/después con sensores NDVI y análisis de laboratorio.

3. **Optimizar el consumo hídrico** en parcelas piloto, demostrando una reducción medible del agua utilizada para riego mediante recomendaciones basadas en datos térmicos, meteorológicos y de humedad del suelo.

4. **Validar la comunicación vía WhatsApp** como canal efectivo para la transferencia de inteligencia agrícola a agricultores con baja alfabetización digital.

5. **Generar un dataset abierto** de correlaciones TEK-sensor que pueda ser utilizado por la comunidad científica jalisciense para futuras investigaciones.

---

## 3. METODOLOGÍA

### 3.1 Diseño experimental

**Sitios de validación:**
- **ITESO campus** — Jardín y laboratorio de drones. Entorno controlado para calibración de sensores y algoritmos (TRL 4).
- **3-5 parcelas piloto** en Valles Centrales de Jalisco (Tlajomulco, Zapopan, Tonalá). Seleccionadas con apoyo de agentes de extensión de SAGARPA.

**Variables independientes:**
- Tipo de práctica: TEK (milpa, rotación, composta) vs. convencional (monocultivo, fertilizante sintético)
- Tipo de cultivo: maíz, agave, aguacate, tomate, frijol (representativos de Jalisco)
- Temporada: temporal (jun-oct) vs. secas (nov-may)

**Variables dependientes (medidas por Cerebro):**
- Índice de salud compuesta (0-100) calculado por el motor de puntuación
- NDVI medio y desviación estándar por parcela
- Estrés térmico (variación > 5°C indica déficit hídrico)
- pH del suelo, materia orgánica %, NPK
- Volumen de agua utilizado para riego (litros/hectárea)
- Rendimiento al final de temporada (kg/hectárea)

### 3.2 Componentes tecnológicos

**Hardware (existente — aportación concurrente):**
- DJI Mavic 3 Multispectral — mapeo NDVI (4 bandas + RGB, 200 ha/vuelo)
- DJI Mavic 3 Thermal — detección de estrés hídrico (640x512 sensor)
- DJI Agras T100 — aplicación de precisión de bioinsumos (100L, LiDAR)
- Sensores IoT de campo — humedad, temperatura, pH

**Software (Cerebro — TRL 3 demostrado):**
| Módulo | Función | Estado |
|--------|---------|--------|
| Motor NDVI | Procesamiento de imágenes multiespectrales → índice de vegetación | Funcional, 22 pruebas |
| Motor térmico | Detección de estrés hídrico desde imágenes térmicas | Funcional, 5 pruebas |
| Puntuación de salud | Score compuesto 0-100 con degradación graceful | Funcional, 28 pruebas |
| Recomendaciones | Tratamientos orgánicos basados en salud + suelo + cultivo | Funcional, 5 pruebas |
| Rotación de cultivos | Plan de 3 temporadas basado en historial de suelo | Funcional, 4 pruebas |
| Optimizador de riego | Calendario de 7 días desde clima + suelo + térmico | Funcional, 4 pruebas |
| Base de conocimiento | 10 fertilizantes orgánicos + 8 prácticas ancestrales + 11 cultivos | Funcional, 4 pruebas |
| Detección de anomalías | Alertas automáticas por caída de salud o NDVI | Funcional |
| Panel de inteligencia | Dashboard para investigadores con tendencias cruzadas | Funcional |
| Autenticación | JWT con roles: admin/investigador/agricultor | Funcional, 5 pruebas |

### 3.3 Cronograma de actividades (12 meses)

| Mes | Actividad | Entregable |
|-----|-----------|-----------|
| 1-2 | Calibración de sensores en ITESO. Selección de parcelas piloto. Línea base de suelo. | Informe de calibración. Análisis de suelo base. |
| 2-3 | Integración WhatsApp Business API. Piloto de comunicación con 5 agricultores. | MVP de chatbot funcionando. |
| 3-4 | Primer ciclo de vuelos NDVI + térmico en parcelas piloto. Validación de puntuación de salud vs. observación de campo. | Dataset de correlaciones NDVI-salud real. |
| 4-6 | Implementación de prácticas TEK en parcelas seleccionadas. Monitoreo quincenal con drones. Recomendaciones vía WhatsApp. | Registro de prácticas aplicadas + scores antes/después. |
| 6-8 | Temporada de lluvias (temporal). Monitoreo intensivo. Optimización de riego en tiempo real. | Datos de eficiencia hídrica. Comparativa temporal vs. secas. |
| 8-10 | Cosecha. Medición de rendimiento. Análisis de suelo post-temporada. | Dataset de rendimiento vs. predicciones de Cerebro. |
| 10-11 | Análisis estadístico de resultados. Calibración del motor de puntuación con datos reales. | Modelo calibrado con R² y MAE documentados. |
| 11-12 | Documentación. Transferencia a ITESO (dataset + acceso investigador). Publicación de resultados. | Artículo científico. Dataset abierto. Informe final. |

---

## 4. VINCULACIÓN EFECTIVA

### 4.1 Institución vinculada: ITESO, Universidad Jesuita de Guadalajara

**Tipo de vinculación:** Colaboración científica para validación de tecnología en entorno controlado.

**Contactos:**
- Juan José Solórzano Zepeda — Coordinador ITESO LINK (Innovación Abierta)
- Luis Luque — Coordinador del Laboratorio de Drones ITESO

**Rol de ITESO:**
1. Proveer el entorno controlado (campus jardín + laboratorio de drones) para calibración TRL 4
2. Asesoría metodológica para el diseño experimental de validación TEK-sensor
3. Acceso de investigadores al panel de inteligencia de Cerebro (rol de solo lectura)
4. Co-autoría en publicaciones derivadas de los datos generados
5. Infraestructura computacional de respaldo

**Aportación concurrente de ITESO:** Infraestructura de laboratorio, horas de investigador, equipo de cómputo. Estimado: $300,000 MXN en especie.

### 4.2 Marco académico

El proyecto se enmarca en la validación de **Conocimiento Ecológico Tradicional (TEK)** mediante datos de sensores — un enfoque legítimo y publicable dentro de la literatura de agroecología y etnoecología. Referencias clave:

- Altieri, M.A. (2018). *Agroecology: The Science of Sustainable Agriculture*
- Toledo, V.M. & Barrera-Bassols, N. (2008). *La memoria biocultural: la importancia ecológica de las sabidurías tradicionales*
- Vandermeer, J. (2012). *The Ecology of Agroecosystems*

---

## 5. INSTITUCIONES USUARIAS

### 5.1 Agricultores piloto (3-5 parcelas en Valles Centrales)

**Perfil:** Pequeños y medianos agricultores (15-80 ha) que practican parcial o totalmente métodos tradicionales. Seleccionados con apoyo de agentes de extensión SAGARPA.

**Perfiles representativos:**
- **Don Carlos** — Rancho El Mezquite, 42 ha, cultivos mixtos. Usa cal y rotación intuitiva. Receptivo a tecnología que valide lo que ya sabe.
- **Doña Irene** — Rancho La Esperanza, Atotonilco el Alto, 18 ha, agave y arándano. Manejo tradicional de tierra. Prefiere indicadores visuales simples.

**Compromiso del usuario:** Permitir vuelos de dron quincenales, compartir datos de rendimiento al final de temporada, participar en prueba de comunicación WhatsApp.

---

## 6. EQUIPO DE TRABAJO

| Rol | Nombre | Responsabilidad |
|-----|--------|----------------|
| **Representante Legal** | Sebastián Sánchez García | CEO CultivOS Mexico S.A. de C.V. Dirección general del proyecto. |
| **Responsable Técnico** | [Por designar — investigador ITESO o SNII] | Diseño experimental, supervisión metodológica, publicación. |
| **Responsable Administrativo** | [Por designar] | Gestión financiera, reportes, documentación fiscal. |
| **Operador de Drones** | Víctor Hernández Quintana | Operaciones de campo, vuelos AFAC, recolección de datos. (Certificación AFAC en proceso) |
| **Desarrollo Tecnológico** | Sebastián Sánchez García + Mubeen Zulfiqar (CTO) | Desarrollo y mantenimiento de la plataforma Cerebro. |

**Nota:** El Responsable Técnico debe cumplir requisitos SNII o equivalentes para proyectos Tipo B. Se recomienda designar a un investigador de ITESO con perfil en agroecología, ciencias del suelo o ingeniería agrícola.

---

## 7. PRESUPUESTO ESTIMADO

### 7.1 Desglose por concepto (COECYTJAL — $2,000,000 MXN)

| Concepto | Monto | % | Justificación |
|----------|-------|---|---------------|
| Equipamiento tecnológico | $200,000 | 10% | Sensores IoT adicionales, estación meteorológica, equipo de cómputo para procesamiento |
| Licenciamientos | $150,000 | 7.5% | WhatsApp Business API, servicios cloud (S3, compute), APIs meteorológicas |
| Materiales de uso directo | $180,000 | 9% | Kits de análisis de suelo, baterías de dron, refacciones, insumos biológicos para pruebas |
| Servicios externos especializados | $300,000 | 15% | Análisis de laboratorio de suelo (certificado), servicios de transcripción de audio |
| Vinculación (ITESO) | $800,000 | 40% | Actividades de colaboración, acceso a infraestructura, horas de investigador |
| Apoyo a estudiantes | $100,000 | 5% | 2 estudiantes de maestría ITESO (agroecología, ingeniería de datos) |
| Capacitación | $45,000 | 2.25% | Certificación AFAC piloto RPAS (Víctor), capacitación en análisis de suelo |
| Publicaciones | $25,000 | 1.25% | Publicación de artículo en revista indexada, materiales de difusión |
| Contingencias | $100,000 | 5% | Imprevistos operativos, reparaciones de equipo |
| Auditoría contable | $50,000 | 2.5% | Auditoría de cierre requerida |
| **Gastos de operación** | $50,000 | 2.5% | Transporte a parcelas, combustible, viáticos de campo |
| **TOTAL COECYTJAL** | **$2,000,000** | **100%** | |

### 7.2 Aportación concurrente ($857,143 MXN — 30%)

| Fuente | Monto | Tipo |
|--------|-------|------|
| CultivOS Mexico S.A. de C.V. | $557,143 | Efectivo + especie (equipo de drones existente, desarrollo de software, horas de equipo) |
| ITESO | $300,000 | Especie (infraestructura de laboratorio, horas de investigador, equipo de cómputo) |
| **TOTAL** | **$857,143** | |

---

## 8. IMPACTO ESPERADO

### 8.1 Indicadores de impacto (para sección "Indicadores" del sistema)

| Indicador | Meta | Método de medición |
|-----------|------|-------------------|
| Parcelas piloto validadas | ≥ 5 | Registro de parcelas con datos completos (suelo base + vuelos + rendimiento) |
| Precisión del motor de salud | R² ≥ 0.70 | Correlación entre score predicho y rendimiento real |
| Reducción de uso de agua | ≥ 15% | Comparativa litros/ha con y sin optimizador de riego |
| Prácticas TEK documentadas | ≥ 8 | Base de datos con correlaciones TEK-sensor medibles |
| Agricultores comunicados vía WhatsApp | ≥ 10 | Registro de mensajes enviados/respondidos |
| Publicación científica | ≥ 1 | Artículo sometido a revista indexada |
| Dataset abierto publicado | 1 | Repositorio con datos de correlación TEK-sensor |
| Estudiantes formados | ≥ 2 | Tesis de maestría vinculadas al proyecto |
| TRL alcanzado | 4 | Informe de validación en entorno controlado |

### 8.2 Impacto social

- **Agricultores beneficiados directamente:** 10-20 en Valles Centrales (piloto)
- **Potencial de escalamiento:** 20 granjas en Año 1, 170 en Año 5 (plan de negocio)
- **Ahorro estimado por granja:** $414,000 MXN/año (reducción de agua + insumos + mejora de rendimiento)
- **Conservación de suelo:** Medición de incremento en materia orgánica después de prácticas TEK
- **Preservación cultural:** Documentación y validación científica de prácticas ancestrales en riesgo de desaparición

### 8.3 Alineación con ODS

- **ODS 2** — Hambre Cero: Mejora de rendimiento agrícola sostenible
- **ODS 6** — Agua Limpia: Reducción de desperdicio hídrico en agricultura
- **ODS 12** — Producción Responsable: Transición de insumos sintéticos a orgánicos
- **ODS 13** — Acción por el Clima: Adaptación agrícola al cambio climático
- **ODS 15** — Vida de Ecosistemas Terrestres: Conservación y recuperación de suelos

---

## 9. PROPIEDAD INTELECTUAL

La propiedad intelectual generada por el proyecto (algoritmos, modelos, bases de datos) será titularidad de instituciones con domicilio fiscal en Jalisco, conforme al Anexo C de la convocatoria.

- **Software (Cerebro):** Registro de derechos de autor ante INDAUTOR. Titularidad: CultivOS Mexico S.A. de C.V.
- **Datasets:** Licencia abierta para uso académico. Titularidad compartida CultivOS + ITESO.
- **Publicaciones:** Co-autoría CultivOS + ITESO.

---

## 10. SUSTENTABILIDAD DEL PROYECTO

Al término del apoyo FODECIJAL, el proyecto es autosustentable mediante:

1. **Modelo de ingresos establecido:** Servicios de agricultura de precisión a-la-carte ($130K-$260K MXN/año por granja)
2. **Equipo de drones existente:** Ya adquirido, no depende del fondo
3. **Plataforma tecnológica operativa:** 221 pruebas automatizadas, desarrollo continuo mediante AutoAgent
4. **Pipeline de clientes:** 20+ granjas interesadas en Valles Centrales
5. **Red de socios:** ITESO (académico), SAGARPA (extensión), ISM Fertilizantes (insumos, en desarrollo)
6. **Financiamiento complementario:** Aplicación simultánea a Impulsora de Innovación ($6M MXN), NRC-IRAP (Canadá), SR&ED (créditos fiscales canadienses)

---

*Documento preparado por CultivOS Mexico S.A. de C.V.*
*Guadalajara, Jalisco — Marzo 2026*
