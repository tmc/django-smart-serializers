__version__ = (0, 0, 1)


def get_unique_fields(model):
    "Collects the fields that can describe a model uniquely."
    fields = tuple()

    # attempt to collect the fields that are unique but not the primary key
    for field in model._meta.fields:
        if field.unique and not field.primary_key:
            fields += (field.name,)

    if model._meta.unique_together:
        fields = fields + model._meta.unique_together[0]

    # otherwise fall back to the primary key
    if not fields:
        fields = ('pk',)
    return fields