from django.contrib import admin
from .models import KeywordSearch, NewsArticle, UserProfile
import logging

logger = logging.getLogger(__name__)
admin.site.register(KeywordSearch)
admin.site.register(NewsArticle)



@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin customization for UserProfile model.

    - Displays user, keyword quota, and block status.
    - Handles errors during save and delete operations.
    """
    list_display = ['user', 'keyword_quota', 'is_blocked']

    def save_model(self, request, obj, form, change):
        """
        Saves the user profile, logs errors if any occur.
        """
        try:
            super().save_model(request, obj, form, change)
        except Exception as e:
            logger.error(f"Error saving UserProfile: {e}")
            self.message_user(request, "An error occurred while saving the user profile.", level='error')

    def delete_model(self, request, obj):
        """
        Deletes the user profile, logs errors if any occur.
        """
        try:
            super().delete_model(request, obj)
        except Exception as e:
            logger.error(f"Error deleting UserProfile: {e}")
            self.message_user(request, "An error occurred while deleting the user profile.", level='error')
