import datetime
from django.test import TestCase
from smart_serializers import get_unique_fields, construct_lookup_pattern
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

    def test_lookup_pattern_generation(self):
        self.assertEqual(construct_lookup_pattern(OnlyPkModel.objects.get(pk=1)), 1)
        self.assertEqual(construct_lookup_pattern(SlugModel.objects.get(pk=1)), 1)
        self.assertEqual(construct_lookup_pattern(UniqueSlugModel.objects.get(pk=1)),
                         {'slug': 'bar'})

class SerializerTest(TestCase):

    def setUp(self):
        author = Author.objects.create(name="Joe")
        author_profile = AuthorProfile.objects.create(author=author, date_of_birth=datetime.date(2009, 1, 1))
        category1 = Category.objects.create(name="Foo", slug="foo")
        category2 = Category.objects.create(name="Bar", slug="bar")
        article = Article.objects.create(author=author, headline="LHC destroys Earth", pub_date=datetime.date(2009, 1, 1))
        article.categories.add(category1)
        article.categories.add(category2)

    def xtestFoo(self):
        author_field = get_field_by_name(Article, 'author')

        #@todo: dry up this boilerplate:
        serializer = Serializer()
        serializer.start_object(None)
        serializer.handle_fk_field(Article.objects.get(pk=1), author_field)

        serialized_author = serializer._current[author_field.name]
        self.assertEqual(serialized_author, {
            'name': 'Joe',
        })
        #self.assertEqual(Serializer().serialize(Article.objects.all()), 'foo')
