from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


### --- Keyword Search Tracking --- ###

class KeywordSearch(models.Model):
    """
    Tracks user keyword searches.

    Fields:
        user (ForeignKey): The user who searched.
        keyword (CharField): The keyword searched.
        searched_at (DateTimeField): Timestamp of search.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    keyword = models.CharField(max_length=255)
    searched_at = models.DateTimeField(auto_now_add=True)
    last_refreshed = models.DateTimeField(null=True, blank=True)



    def __str__(self):
        return f"{self.user.username} - {self.keyword}"


### --- News Articles Fetched from News API --- ###

class NewsArticle(models.Model):
    """
    Stores articles fetched for a keyword search.

    Fields:
        keyword_search (ForeignKey): Related search instance.
        title (CharField): Article title.
        description (TextField): Optional article summary.
        url (URLField): Link to the full article.
        published_at (DateTimeField): When it was published.
        source_name (CharField): News source (e.g., BBC, CNN).
        language (CharField): Language of the article.
    """
    keyword_search = models.ForeignKey(
        KeywordSearch,
        on_delete=models.CASCADE,
        related_name='articles'
    )
    title = models.CharField(max_length=500)
    description = models.TextField(null=True, blank=True)
    url = models.URLField()
    published_at = models.DateTimeField()
    source_name = models.CharField(max_length=200)
    language = models.CharField(max_length=10)

    def __str__(self):
        return self.title


### --- Extended User Profile Model --- ###

class UserProfile(models.Model):
    """
    Extends the default User model to store additional info.

    Fields:
        user (OneToOneField): Link to Django's built-in User.
        keyword_quota (int): Number of keywords user can search.
        is_blocked (bool): Whether user is blocked from searching.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    keyword_quota = models.PositiveIntegerField(default=10)
    is_blocked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} Profile"


### --- Signal: Create or Update UserProfile on User Creation --- ###

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Signal to create or update UserProfile whenever a User is saved.
    """
    if created:
        UserProfile.objects.create(user=instance)
    else:
        instance.userprofile.save()
