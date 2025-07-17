from django import forms

class KeywordSearchForm(forms.Form):
    """
        Form to capture a search keyword from the user.

        Fields:
            keyword (CharField): The keyword to search news for.
        """
    keyword = forms.CharField(label='Enter Keyword', max_length=255)
