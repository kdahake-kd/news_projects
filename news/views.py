from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib import messages
from .models import KeywordSearch, NewsArticle, UserProfile
from .forms import KeywordSearchForm
from datetime import timedelta
import requests
import logging

logger = logging.getLogger(__name__)
NEWS_API_KEY = settings.NEWS_API_KEY

@login_required
def search_news(request):
    """
    Handles keyword-based news search for the logged-in user.

    Main Features:
    - Validates and enforces user-specific keyword quota limits.
    - Shows confirmation screen if keyword was searched recently.
    - Calls News API and saves results if new search or forced refresh.
    - Displays quota usage and prevents repeated submissions.

    Args:
        request (HttpRequest): Django request object.

    Returns:
        HttpResponse: Rendered form, confirmation page, or search history.
    """
    try:
        remaining_quota = None

        # 1. Profile, quota, and block check
        if not (request.user.is_superuser or request.user.is_staff):
            try:
                profile = request.user.userprofile
            except UserProfile.DoesNotExist:
                messages.error(request, "Your user profile was not found.")
                return redirect('search_history')

            if profile.is_blocked:
                messages.error(request, "You are currently blocked from searching.")
                return redirect('search_history')

            search_count = KeywordSearch.objects.filter(user=request.user).count()
            if search_count >= profile.keyword_quota:
                messages.error(request, f"Keyword quota reached ({profile.keyword_quota}).")
                return redirect('search_history')

            remaining_quota = profile.keyword_quota - search_count

        if request.method == 'POST':
            form = KeywordSearchForm(request.POST)
            if form.is_valid():
                keyword = form.cleaned_data['keyword'].strip()
                force_refresh = request.GET.get("force_refresh") == "1"

                #  2. Check recent search (within 15 minutes)
                recent = KeywordSearch.objects.filter(
                    user=request.user,
                    keyword__iexact=keyword,
                    searched_at__gte=timezone.now() - timedelta(minutes=15)
                ).first()

                if recent and not force_refresh:
                    articles = NewsArticle.objects.filter(keyword_search=recent)
                    return render(request, 'news/confirm_refresh.html', {
                        'keyword': keyword,
                        'recent_search_time': recent.searched_at,
                        'articles': articles,
                        'form': form,
                        'remaining_quota': remaining_quota
                    })

                #  3. Call News API
                try:
                    url = f"https://newsapi.org/v2/everything?q={keyword}&apiKey={NEWS_API_KEY}"
                    response = requests.get(url)
                    data = response.json()
                except requests.exceptions.RequestException as e:
                    logger.error(f"News API request failed: {e}")
                    messages.error(request, "News API request failed. Please try again later.")
                    return render(request, 'news/search.html', {'form': form, 'remaining_quota': remaining_quota})

                if data.get("status") != "ok":
                    logger.error(f"News API error: {data}")
                    messages.error(request, "News API returned an error.")
                    return render(request, 'news/search.html', {'form': form, 'remaining_quota': remaining_quota})

                #  4. Save KeywordSearch safely (prevent IntegrityError)
                search, created = KeywordSearch.objects.get_or_create(
                    user=request.user,
                    keyword__iexact=keyword,
                    defaults={'keyword': keyword, 'searched_at': timezone.now()}
                )
                if not created:
                    # Update the timestamp and clear previous articles
                    search.searched_at = timezone.now()
                    search.save()
                    NewsArticle.objects.filter(keyword_search=search).delete()

                #  5. Save articles
                for article in data.get('articles', []):
                    try:
                        NewsArticle.objects.create(
                            keyword_search=search,
                            title=article.get('title', ''),
                            description=article.get('description', ''),
                            url=article.get('url', ''),
                            published_at=article.get('publishedAt'),
                            source_name=article.get('source', {}).get('name', 'Unknown'),
                            language=article.get('language', 'en')
                        )
                    except Exception as e:
                        logger.warning(f"Failed to save article: {e}")

                messages.success(request, "News articles fetched successfully.")
                return redirect('search_history')
        else:
            form = KeywordSearchForm()

        return render(request, 'news/search.html', {
            'form': form,
            'remaining_quota': remaining_quota,
        })

    except Exception as e:
        logger.error(f"Unhandled exception in search_news: {e}")
        messages.error(request, "An unexpected error occurred.")
        return redirect('search_history')


@login_required
def search_history(request):
    """
    Displays the authenticated user's search history along with filtering capabilities.

    Features:
    - Retrieves all previously searched keywords by the user.
    - Filters associated articles by optional parameters: publication date, source name, and language.
    - Groups filtered articles under their respective keyword searches.
    - Prepares distinct lists of sources and languages for use in the UI filter dropdowns.
    - Includes a "Refresh Results" button that fetches **new articles** from the News API for each previously searched keyword.
      This ensures the user can update their history with the **latest news data** without re-searching manually.

    Refresh Button Functionality:
    --------------------------------------
    1. On clicking the "Refresh Results" button in the history page:
       - The frontend makes a GET request to the `refresh_results` view.
       - That view retrieves the user's previously searched keywords.
       - It re-queries the News API using the same keywords.
       - Only **new articles** (based on unique URLs not already saved) are saved in the database.
    2. After refreshing, the user is redirected back to the same history page.
       - They will now see **latest news articles** grouped under their past search keywords.
       - Filtering options (date/source/language) remain functional on the updated results.

    Args:
        request (HttpRequest): The request object containing session and optional filter query parameters.

    Returns:
        HttpResponse: Renders the 'news/history.html' template with search history and applied filters.

    Notes:
        - User must be authenticated to access this view.
        - If an error occurs during processing, logs the error and redirects to the search page.
    """
    try:
        searches = KeywordSearch.objects.filter(user=request.user).order_by('-searched_at')

        selected_date = request.GET.get('date')
        selected_source = request.GET.get('source')
        selected_language = request.GET.get('language')

        filtered_searches = []
        for search in searches:
            articles = NewsArticle.objects.filter(keyword_search=search)

            if selected_date:
                articles = articles.filter(published_at__date=selected_date)
            if selected_source:
                articles = articles.filter(source_name__icontains=selected_source)
            if selected_language:
                articles = articles.filter(language=selected_language)

            if articles.exists():
                search.filtered_articles = articles
                filtered_searches.append(search)

        sources = NewsArticle.objects.filter(keyword_search__user=request.user).values_list('source_name', flat=True).distinct()
        languages = NewsArticle.objects.filter(keyword_search__user=request.user).values_list('language', flat=True).distinct()

        return render(request, 'news/history.html', {
            'searches': filtered_searches,
            'filters': {
                'date': selected_date,
                'source': selected_source,
                'language': selected_language,
            },
            'sources': sources,
            'languages': languages,
            'keyword_searches': searches,
        })

    except Exception as e:
        logger.error(f"Error in search_history: {e}")
        messages.error(request, "Failed to load search history.")
        return redirect('search_news')





from django.utils import timezone
from datetime import timedelta

@login_required
def refresh_news(request, keyword_id):
    """
        Refreshes the news articles associated with a specific keyword search for the authenticated user.

        Features:
        - Allows users to fetch new articles for a previously searched keyword.
        - Prevents refresh if the same keyword was refreshed within the last 15 minutes (rate limiting).
        - Only fetches articles newer than the latest one already saved to avoid duplication.
        - Saves new, non-duplicate articles to the database.
        - Updates the 'last_refreshed' timestamp of the keyword search.

        Args:
            request (HttpRequest): The request object containing session and user data.
            keyword_id (int): The ID of the KeywordSearch instance to be refreshed.

        Returns:
            HttpResponseRedirect: Redirects to the search history page with a success or error message.

        Steps:
        1. Prevent users from refreshing the same keyword within 15 minutes to avoid spamming the News API.
        2. Identify the latest published article already stored for this keyword to fetch only newer articles.
        3. Call the News API using the keyword and optional `from` date.
        4. Filter out duplicate articles (based on title and published_at).
        5. Save new articles to the database and update the last refreshed timestamp.
        6. Notify the user whether the refresh was successful or not.

        Notes:
        - Requires user to be logged in.
        - If an exception occurs (e.g., API error, DB error), the function logs it and displays a user-friendly error message.
        """
    try:
        search = get_object_or_404(KeywordSearch, pk=keyword_id, user=request.user)

        #  Step 1: Prevent refresh within 15 minutes
        if search.last_refreshed and timezone.now() - search.last_refreshed < timedelta(minutes=15):
            messages.warning(request, "Please wait 15 minutes before refreshing this keyword again.")
            return redirect('search_history')

        #  Step 2: Get latest published article to avoid duplicates
        latest_article = search.articles.order_by('-published_at').first()
        from_date = latest_article.published_at if latest_article else None

        # Step 3: Call News API
        url = f"https://newsapi.org/v2/everything?q={search.keyword}&from={from_date}&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
        response = requests.get(url)
        data = response.json()

        for article in data.get('articles', []):
            published = article['publishedAt']
            try:
                if not search.articles.filter(title=article['title'], published_at=published).exists():
                    NewsArticle.objects.create(
                        keyword_search=search,
                        title=article['title'],
                        description=article.get('description'),
                        url=article['url'],
                        published_at=published,
                        source_name=article['source']['name'],
                        language=article.get('language', 'en')
                    )
            except Exception as e:
                logger.warning(f"Error saving refreshed article: {e}")

        #  Step 4: Update last refreshed timestamp
        search.last_refreshed = timezone.now()
        search.save()

        messages.success(request, "News refreshed successfully.")
        return redirect('search_history')

    except Exception as e:
        logger.error(f"Error in refresh_news: {e}")
        messages.error(request, "Failed to refresh articles.")
        return redirect('search_history')



def register_view(request):
    """
    Handles user registration through a POST request and renders the registration page.

    If the request method is POST, the view checks for the presence of `username` and `password`.
    If valid and the user doesn't already exist, it creates a new user and logs them in.
    Errors and duplicate registrations are handled gracefully with appropriate user messages.

    Args:
        request (HttpRequest): The incoming request object from the user.

    Returns:
        HttpResponse: Redirects to:
            - Home page (`/`) upon successful registration.
            - Registration page with an error if form validation fails.
            - Login page if the user already exists.
        Or renders the registration form for GET requests.

    Raises:
        None directly, but logs and handles exceptions gracefully.
    """

    try:
        if request.method == "POST":
            username = request.POST.get("username")
            password = request.POST.get("password")

            if not username or not password:
                messages.error(request, "Username and password are required.")
                return redirect("register")

            if User.objects.filter(username=username).exists():
                messages.error(request, "User already exists, please login.")
                return redirect("login")

            user = User.objects.create_user(username=username, password=password)
            login(request, user)
            return redirect("/")
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}", exc_info=True)
        messages.error(request, "An unexpected error occurred during registration.")
        return redirect("register")

    return render(request, "news/register.html")




from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

def custom_login_view(request):
    """
    Handles user login using a custom login view.

    This view authenticates a user based on username and password submitted via POST.
    If credentials are valid, the user is logged in and redirected to the homepage.
    Appropriate error messages are displayed if:
    - Required fields are missing
    - User does not exist
    - Authentication fails

    Args:
        request (HttpRequest): The HTTP request object containing login data.

    Returns:
        HttpResponse:
            - Redirect to homepage ("/") if login is successful.
            - Redirect to "register" if the user does not exist.
            - Redirect back to "login" with error messages on failure.
            - Renders the login template on GET request.

    Raises:
        None directly. Exceptions are logged and handled with user feedback.
    """
    try:
        if request.method == "POST":
            username = request.POST.get("username")
            password = request.POST.get("password")

            if not username or not password:
                messages.error(request, "Username and password are required.")
                return redirect("login")

            if not User.objects.filter(username=username).exists():
                messages.warning(request, "User does not exist, please register.")
                return redirect("register")

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect("/")
            else:
                messages.error(request, "Invalid credentials")
                return redirect("login")
    except Exception as e:
        logger.error(f"Error during login: {str(e)}", exc_info=True)
        messages.error(request, "An unexpected error occurred during login.")
        return redirect("login")

    return render(request, "news/login.html")
from django.contrib.auth import logout
def user_logout_view(request):
    logout(request)
    return redirect('register')


