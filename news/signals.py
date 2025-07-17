"""
Signal to automatically create a UserProfile whenever a new user is registered.

This ensures that every non-staff, non-superuser User has a corresponding UserProfile
created immediately after the User instance is saved.

Functions:
    - create_user_profile: Triggered after a User instance is saved. If the User is newly created
      and not a staff/superuser, a UserProfile is created or retrieved.

"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal handler that creates a UserProfile for each newly registered non-admin user.

    Args:
        sender (Model): The model class (User) that sent the signal.
        instance (User): The actual instance of the user created.
        created (bool): A boolean; True if a new record was created.
        **kwargs: Additional keyword arguments.

    """
    if created and not instance.is_staff and not instance.is_superuser:
        UserProfile.objects.get_or_create(user=instance)
