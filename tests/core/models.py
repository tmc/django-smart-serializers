from django.db import models


class OnlyPkModel(models.Model):
    id = models.AutoField(primary_key=True)

class SlugModel(models.Model):
    slug = models.SlugField()

class UniqueSlugModel(models.Model):
    slug = models.SlugField(unique=True)

class UniqueIntModel(models.Model):
    val = models.IntegerField(unique=True)

class TwoUniqueIntsModel(models.Model):
    val1 = models.IntegerField(unique=True)
    val2 = models.IntegerField(unique=True)

class UniqueTogetherModel(models.Model):
    val1 = models.IntegerField()
    val2 = models.IntegerField()

    class Meta:
        unique_together = ('val1', 'val2')

class UniqueTogetherAndUniqueModel(models.Model):
    val1 = models.IntegerField(unique=True)
    val2 = models.IntegerField()
    val3 = models.IntegerField()

    class Meta:
        unique_together = ('val2', 'val3')










###################################################################


class Category(models.Model):
    name = models.CharField(max_length=20)
    slug = models.SlugField(unique=True)

    class Meta:
       ordering = ('name',)

    def __unicode__(self):
        return self.name

class Author(models.Model):
    name = models.CharField(max_length=20, unique=True)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return self.name

class Article(models.Model):
    headline = models.CharField(max_length=50)
    categories = models.ManyToManyField(Category)

    class Meta:
       ordering = ('id',)

    def __unicode__(self):
        return self.headline

class AuthorProfile(models.Model):
    author = models.OneToOneField(Author, primary_key=True)
    date_of_birth = models.DateField()

    def __unicode__(self):
        return u"Profile of %s" % self.author

class Publication(models.Model):
    article = models.ForeignKey(Article)
    site = models.ForeignKey('Site')

    class Meta:
        ordering = ('id',)
        unique_together = ('article', 'site')

    def __unicode__(self):
        return '%s on %s' % (self.article, self.site)

class Site(models.Model):
    name = models.CharField(max_length=20)
    articles = models.ManyToManyField(Article, through=Publication)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return self.name
