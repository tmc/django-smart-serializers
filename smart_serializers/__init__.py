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

    #@todo should we sort on the way out?
    return fields

def described_only_by_pk(model):
    """Helper function to determine if a model can be described uniquely by a
    subset of it's fields apart from the primary key"""
    return get_unique_fields(model) == ('pk',)

def lookup_pattern_from_instance(instance):
    """Given a model instance, constructs a lookup pattern.

    If the instance can reliably be described with a subset of fields a
    dictionary mapping field names to values for the instance. Otherwise a
    single integer representing the instance's primary key is returned.
    """
    # if we can only describe with the pk, return it's value
    if described_only_by_pk(instance):
        return instance.pk
    else:
        return dict((field, getattr(instance, field))
                    for field in get_unique_fields(instance))
