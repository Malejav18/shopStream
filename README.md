# ShopStream Big Data Pipeline

## Descripción

Este proyecto implementa un pipeline batch de Big Data para la empresa ficticia ShopStream, usando servicios de AWS para ingesta, validación, procesamiento, catalogación, almacenamiento analítico y exposición de métricas mediante API REST.

## Arquitectura

S3 Raw → Lambda Validator → S3 Validated → EMR Studio / PySpark → S3 Processed Parquet → Glue Crawler → Glue Visual ETL → RDS PostgreSQL → Lambda + API Gateway con Zappa.

## Servicios usados

- Amazon S3
- AWS Lambda
- Amazon CloudWatch
- Amazon EMR Studio
- Apache Spark / PySpark
- AWS Glue Data Catalog
- AWS Glue Studio
- AWS Glue Workflow
- Amazon RDS PostgreSQL
- Amazon API Gateway
- Zappa
- GitHub Actions

## Estructura del proyecto

```text
shopstream/
├── api/
├── data_generator/
├── emr_jobs/
├── lambda_ingestion/
├── tests/
├── pytest.ini
└── README.md
