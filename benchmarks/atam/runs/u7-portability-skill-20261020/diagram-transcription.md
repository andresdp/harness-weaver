# Page 1 architecture diagram transcription

Source: `case-studies/atam-evaluator/archevaluation-llms/input-artifacts/G1-anonymized-blind-eng.pdf`, page 1. This is a manual, text-only transcription from visual inspection; fine-grained member names and connector semantics that were not legible are omitted.

- Client area: Mobile Client and PC Client appear behind KONG ACL 3.8.x, which connects to the business-logic area.
- Business logic includes Cliente, CircuitBreaker, Estadística, a Módulo de Pedidos, and a Módulo de Repartos y Rutas.
- The order module shows Pedido, a Fase interface, FasePedido, an EstadoPedido enumeration, Stripe Connect, and the ordered phases Preprocesamiento, Autorización, and Aceptación.
- The delivery and routes module shows Reparto, Ruta, Flota, Incidencia, a Strategy_Ruta interface, and AlgorithmA/AlgorithmB implementations. A note says the algorithm is selected based on delay.
- A separate Acceso a Datos area contains PostgreSQL 42.7.4. A nearby note says one driver has two distinct tables and is compatible with Windows and Java.
- The drawing shows connectors among these components, but not every connector is sufficiently clear in the rendered page to transcribe as a reliable interaction contract.

This transcription is a manual substitution for image understanding. It should be reviewed against the source diagram before being used as authoritative architecture data.
