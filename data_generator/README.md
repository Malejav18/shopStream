## Punto 1 - Diseño y generación de datos

Este módulo genera un dataset sintético para ShopStream con entidades relacionadas:

- users
- products
- sessions
- events
- transactions
- cart_items

El archivo principal de eventos se genera en formato JSON Lines y se particiona por fecha:

raw/events/year=2026/month=05/day=25/events.jsonl

Para generar 500.000 registros:

```bash
python3 data_generator/generate_shopstream_data.py --date 2026-05-25 --records 500000
