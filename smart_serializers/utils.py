"""
Helper utilities and classes for smart_serializers.
"""

from django.db import models, transaction, IntegrityError
from django.utils.encoding import smart_str


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

def _object_lookup_to_pk(model, lookup):
    """Performs a lookup if `lookup` is not simply a primary key otherwise is
    returned directly."""
    try:
        pk = int(lookup)
    except (TypeError, ValueError):
    # otherwise, attempt a lookup
        try:
            pk = model._default_manager.get(**lookup).pk
        except model.DoesNotExist:
            pk = None
    return pk

class DeserializedObject(object):
    """
    A deserialized model.

    Basically a container for holding the pre-saved deserialized data along
    with the many-to-many data saved with the object.

    Call ``save()`` to save the object (with the many-to-many data) to the
    database; call ``save(save_m2m=False)`` to save just the object fields
    (and not touch the many-to-many stuff.)
    """

    def __init__(self, model, data, m2m_data=None):
        self.model = model
        self.data = data
        self.m2m_data = m2m_data

    def __repr__(self):
        return "<DeserializedObject: %s>" % smart_str(self.model(**self.data))

    def save(self, save_m2m=True):
        # Call save on the Model baseclass directly. This bypasses any
        # model-defined save. The save is also forced to be raw.
        # This ensures that the data that is deserialized is literally
        # what came from the file, not post-processed by pre_save/save
        # methods.

        created = False
        try:
            obj = self.model._default_manager.get(**self.data)
        except self.model.DoesNotExist:
            try:
                obj = self.model(**self.data)
                sid = transaction.savepoint()
                #@todo should we use force_insert?
                models.Model.save_base(obj, raw=True)
                transaction.savepoint_commit(sid)
                created = True
            except IntegrityError, e:
                transaction.savepoint_rollback(sid)

        if self.m2m_data and save_m2m:
            for accessor_name, object_list in self.m2m_data.items():
                rel_model = obj._meta.get_field(accessor_name).rel.to
                object_list = [_object_lookup_to_pk(rel_model, rel_obj) for rel_obj in object_list]
                setattr(obj, accessor_name, filter(lambda x: x, object_list))

        # prevent a second (possibly accidental) call to save() from saving
        # the m2m data twice.
        self.m2m_data = None