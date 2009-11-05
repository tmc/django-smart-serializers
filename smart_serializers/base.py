"""
Module for abstract serializer/unserializer base classes.
"""

from StringIO import StringIO

from django.db import models, transaction, IntegrityError
from django.utils.encoding import smart_str, smart_unicode
from django.utils import datetime_safe

class SerializationError(Exception):
    """Something bad happened during serialization."""
    pass

class DeserializationError(Exception):
    """Something bad happened during deserialization."""
    pass

class Serializer(object):
    """
    Abstract serializer base class.
    """

    # Indicates if the implemented serializer is only available for
    # internal Django use.
    internal_use_only = False

    def serialize(self, queryset, **options):
        """
        Serialize a queryset.
        """
        self.options = options

        self.stream = options.get("stream", StringIO())
        self.selected_fields = options.get("fields")

        self.start_serialization()
        for obj in queryset:
            self.start_object(obj)
            for field in obj._meta.local_fields:
                if field.serialize:
                    if field.rel is None:
                        if self.selected_fields is None or field.attname in self.selected_fields:
                            self.handle_field(obj, field)
                    else:
                        if self.selected_fields is None or field.attname[:-3] in self.selected_fields:
                            self.handle_fk_field(obj, field)
            for field in obj._meta.many_to_many:
                if field.serialize:
                    if self.selected_fields is None or field.attname in self.selected_fields:
                        self.handle_m2m_field(obj, field)
            self.end_object(obj)
        self.end_serialization()
        return self.getvalue()

    def get_string_value(self, obj, field):
        """
        Convert a field's value to a string.
        """
        return smart_unicode(field.value_to_string(obj))

    def start_serialization(self):
        """
        Called when serializing of the queryset starts.
        """
        raise NotImplementedError

    def end_serialization(self):
        """
        Called when serializing of the queryset ends.
        """
        pass

    def start_object(self, obj):
        """
        Called when serializing of an object starts.
        """
        raise NotImplementedError

    def end_object(self, obj):
        """
        Called when serializing of an object ends.
        """
        pass

    def handle_field(self, obj, field):
        """
        Called to handle each individual (non-relational) field on an object.
        """
        raise NotImplementedError

    def handle_fk_field(self, obj, field):
        """
        Called to handle a ForeignKey field.
        """
        raise NotImplementedError

    def handle_m2m_field(self, obj, field):
        """
        Called to handle a ManyToManyField.
        """
        raise NotImplementedError

    def getvalue(self):
        """
        Return the fully serialized queryset (or None if the output stream is
        not seekable).
        """
        if callable(getattr(self.stream, 'getvalue', None)):
            return self.stream.getvalue()

class Deserializer(object):
    """
    Abstract base deserializer class.
    """

    def __init__(self, stream_or_string, **options):
        """
        Init this serializer given a stream or a string
        """
        self.options = options
        if isinstance(stream_or_string, basestring):
            self.stream = StringIO(stream_or_string)
        else:
            self.stream = stream_or_string
        # hack to make sure that the models have all been loaded before
        # deserialization starts (otherwise subclass calls to get_model()
        # and friends might fail...)
        models.get_apps()

    def __iter__(self):
        return self

    def next(self):
        """Iteration iterface -- return the next item in the stream"""
        raise NotImplementedError

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