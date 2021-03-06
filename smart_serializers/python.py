"""
A Python "serializer". Doesn't do much serializing per se -- just converts to
and from basic Python data types (lists, dicts, strings, etc.). Useful as a basis for
other serializers.
"""

from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.core.serializers import base
from django.utils.encoding import smart_unicode, is_protected_type

from smart_serializers import utils

class Serializer(base.Serializer):
    """
    Serializes a QuerySet to basic Python objects.
    """

    internal_use_only = True

    def start_serialization(self):
        self._current = None
        self.objects = []

    def end_serialization(self):
        pass

    def start_object(self, obj):
        self._current = {}

    def end_object(self, obj):
        object_dict = {
            "model"  : smart_unicode(obj._meta),
            "fields" : self._current
        }
        if utils.described_only_by_pk(obj):
            object_dict['pk'] = smart_unicode(obj._get_pk_val(),
                                              strings_only=True)
        self.objects.append(object_dict)
        self._current = None

    def handle_field(self, obj, field):
        value = field._get_val_from_obj(obj)
        # Protected types (i.e., primitives like None, numbers, dates,
        # and Decimals) are passed through as is. All other values are
        # converted to string first.
        if is_protected_type(value):
            self._current[field.name] = value
        else:
            self._current[field.name] = field.value_to_string(obj)

    def handle_fk_field(self, obj, field):
        related = getattr(obj, field.name)

        if related is not None:
            related = utils.lookup_pattern_from_instance(related)
            #if field.rel.field_name == related._meta.pk.name:
            #    # Related to remote object via primary key
            #    related = related._get_pk_val()
            #@todo consider this case:
            #else:
            #    # Related to remote object via other field
            #    related = getattr(related, field.rel.field_name)
        #self._current[field.name] = smart_unicode(related, strings_only=True)
        self._current[field.name] = related

    def handle_m2m_field(self, obj, field):
        if field.creates_table:
            self._current[field.name] = [utils.lookup_pattern_from_instance(related)
                               for related in getattr(obj, field.name).iterator()]

    def getvalue(self):
        return self.objects

def Deserializer(object_list, **options):
    """
    Deserialize simple Python objects back into Django ORM instances.

    It's expected that you pass the Python objects themselves (instead of a
    stream or a string) to the constructor
    """
    models.get_apps()
    for d in object_list:
        # Look up the model and starting build a dict of data for it.
        Model = _get_model(d["model"])
        uses_dictionary_lookup = False
        data = {}
        m2m_data = {}
        if 'pk' in d:
            data[Model._meta.pk.attname] = Model._meta.pk.to_python(d["pk"])
        else:
            uses_dictionary_lookup = True

        # Handle each field
        for (field_name, field_value) in d["fields"].iteritems():
            if isinstance(field_value, str):
                field_value = smart_unicode(field_value, options.get("encoding", settings.DEFAULT_CHARSET), strings_only=True)

            field = Model._meta.get_field(field_name)

            # Handle M2M relations
            if field.rel and isinstance(field.rel, models.ManyToManyRel):
                m2m_convert = field.rel.to._meta.pk.to_python
                rel_values = []
                for rel_value in field_value:
                    try:
                        rel_values.append(m2m_convert(smart_unicode(rel_value)))
                    except ValidationError:
                        rel_values.append(rel_value)
                m2m_data[field.name] = rel_values

            # Handle FK fields
            elif field.rel and isinstance(field.rel, models.ManyToOneRel):
                if field_value is not None:
                    try:
                        data[field.attname] = field.rel.to._meta.get_field(field.rel.field_name).to_python(field_value)
                    except ValidationError:
                        data[field.attname] = field_value
                else:
                    data[field.attname] = None

            # Handle all other fields
            else:
                data[field.name] = field.to_python(field_value)

        yield utils.DeserializedObject(Model, data, m2m_data)

def _get_model(model_identifier):
    """
    Helper to look up a model from an "app_label.module_name" string.
    """
    try:
        Model = models.get_model(*model_identifier.split("."))
    except TypeError:
        Model = None
    if Model is None:
        raise base.DeserializationError(u"Invalid model identifier: '%s'" % model_identifier)
    return Model
