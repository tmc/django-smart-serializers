DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = 'test.db'

INSTALLED_APPS = [
    'smart_serializers',
    'core',
]

SERIALIZATION_MODULES = {
        "json" : "smart_serializers.json",
}

