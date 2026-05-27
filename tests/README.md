# README - Pruebas Unitarias ShopStream

## Descripción

Este documento describe las pruebas unitarias implementadas para el proyecto **ShopStream Big Data Pipeline**.

El objetivo de estas pruebas es validar la lógica principal del proyecto sin depender directamente de servicios reales de AWS durante la ejecución del pipeline de CI/CD.

Las pruebas cubren:

- API Flask desplegada con Zappa.
- Generador de datos sintéticos.
- Lambda de validación de archivos.
- Funciones auxiliares del procesamiento PySpark.

---

## Estructura de pruebas

La carpeta de pruebas está ubicada en:

```text
tests/
├── test_api.py
├── test_generator.py
├── test_lambda_validation.py
└── test_pyspark_logic.py
