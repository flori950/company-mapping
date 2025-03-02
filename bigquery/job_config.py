from google.cloud import bigquery
from .schemes import (
    crunchbase_schema
)


CRUNCHBASE_CONFIG = bigquery.LoadJobConfig(
    schema=crunchbase_schema.CRUNCHBASE_SCHEMA,
    autodetect=False,
    source_format=bigquery.SourceFormat.CSV,
    schema_update_options=[
        bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION],
    write_disposition="WRITE_APPEND",
)
