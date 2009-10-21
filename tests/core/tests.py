import datetime
from django.test import TestCase
from smart_serializers import get_unique_fields, lookup_pattern_from_instance
from smart_serializers.python import Serializer, Deserializer
from core.models import Article, Author, AuthorProfile, Category, Publication, Site
from core.models import *


def get_field_by_name(model, field_name):
    return [field for field in model._meta.fields if field.name == field_name][0]


class FieldInspectionTest(TestCase):

    def test_unique_field_collection(self):
        self.assertEqual(get_unique_fields(OnlyPkModel), ('pk',))
        self.assertEqual(get_unique_fields(SlugModel), ('pk',))
        self.assertEqual(get_unique_fields(UniqueSlugModel), ('slug',))
        self.assertEqual(get_unique_fields(UniqueIntModel), ('val',))
        self.assertEqual(get_unique_fields(TwoUniqueIntsModel), ('val1', 'val2'))
        self.assertEqual(get_unique_fields(UniqueTogetherModel), ('val1', 'val2'))
        self.assertEqual(get_unique_fields(UniqueTogetherAndUniqueModel), ('val1', 'val2', 'val3'))

        #self.assertEqual(get_unique_fields(TwoUniqueTogetherSetsModel), ('val1', 'val2', 'val3'))
        #@todo test parent-inherited pk's
        #@todo test multiple unique_together sets

class LookupPatternGenerationTest(TestCase):

    def setUp(self):
        OnlyPkModel.objects.create()
        SlugModel.objects.create(slug='foo')
        UniqueSlugModel.objects.create(slug='bar')
        UniqueIntModel.objects.create(val=1)
        TwoUniqueIntsModel.objects.create(val1=1, val2=2)
        UniqueTogetherModel.objects.create(val1=1, val2=2)
        UniqueTogetherAndUniqueModel.objects.create(val1=1, val2=2, val3=3)

    def test_lookup_pattern_generation(self):
        self.assertEqual(lookup_pattern_from_instance(OnlyPkModel.objects.get(pk=1)), 1)
        self.assertEqual(lookup_pattern_from_instance(SlugModel.objects.get(pk=1)), 1)
        self.assertEqual(lookup_pattern_from_instance(UniqueSlugModel.objects.get(pk=1)),
                         {'slug': 'bar'})
        self.assertEqual(lookup_pattern_from_instance(UniqueIntModel.objects.get(pk=1)),
                         {'val': 1})
        self.assertEqual(lookup_pattern_from_instance(TwoUniqueIntsModel.objects.get(pk=1)),
                         {'val1': 1, 'val2': 2})
        self.assertEqual(lookup_pattern_from_instance(UniqueTogetherModel.objects.get(pk=1)),
                         {'val1': 1, 'val2': 2})
        self.assertEqual(lookup_pattern_from_instance(UniqueTogetherAndUniqueModel.objects.get(pk=1)),
                         {'val1': 1, 'val2': 2, 'val3': 3})

class SerializerTest(TestCase):

    def setUp(self):
        author = Author.objects.create(name="Joe")
        author_profile = AuthorProfile.objects.create(author=author, date_of_birth=datetime.date(2009, 1, 1))
        category1 = Category.objects.create(name="Foo", slug="foo")
        category2 = Category.objects.create(name="Bar", slug="bar")
        article = Article.objects.create(author=author, headline="LHC destroys Earth", pub_date=datetime.date(2009, 1, 1))
        article.categories.add(category1)
        article.categories.add(category2)

    def test_category_serialization(self):
        self.assertEqual(Serializer().serialize(Category.objects.all()), [
            {'model': u'core.category', 'fields': {'name': u'Bar', 'slug': u'bar'}},
            {'model': u'core.category', 'fields': {'name': u'Foo', 'slug': u'foo'}}
        ])

    def test_full_article_serialization(self):
        self.assertEqual(Serializer().serialize(Article.objects.all()), [
            {
                'pk': 1,
                'model': u'core.article',
                'fields': {'headline': u'LHC destroys Earth',
                           'pub_date': datetime.datetime(2009, 1, 1, 0, 0),
                           'author': {'name': u'Joe'},
                           'categories': [
                                {'slug': u'bar'},
                                {'slug': u'foo'},
                            ],
                          }}
            ])
