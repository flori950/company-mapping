from enum import Enum
from google.cloud.bigquery import SchemaField


class FieldType(Enum):
    STRING = 'STRING'
    INT64 = 'INT64'
    FLOAT64 = 'FLOAT64'
    BOOL = 'BOOL'
    DATETIME = 'DATETIME'
    TIMESTAMP = 'TIMESTAMP'


class FieldMode(Enum):
    NULLABLE = 'NULLABLE'
    REQUIRED = 'REQUIRED'


class StringField(SchemaField):
    def __init__(self, name, mode=FieldMode.NULLABLE):
        super().__init__(name, FieldType.STRING.value, mode=mode.value)


class IntField(SchemaField):
    def __init__(self, name, mode=FieldMode.NULLABLE):
        super().__init__(name, FieldType.INT64.value, mode=mode.value)


class FloatField(SchemaField):
    def __init__(self, name, mode=FieldMode.NULLABLE):
        super().__init__(name, FieldType.FLOAT64.value, mode=mode.value)


class BoolField(SchemaField):
    def __init__(self, name, mode=FieldMode.NULLABLE):
        super().__init__(name, FieldType.BOOL.value, mode=mode.value)


class DateTimeField(SchemaField):
    def __init__(self, name, mode=FieldMode.NULLABLE):
        super().__init__(name, FieldType.DATETIME.value, mode=mode.value)


class TimestampField(SchemaField):
    def __init__(self, name, mode=FieldMode.NULLABLE):
        super().__init__(name, FieldType.TIMESTAMP.value, mode=mode.value)

