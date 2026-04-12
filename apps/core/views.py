from django.views.generic import TemplateView


class HomeView(TemplateView):
    """Basic landing page used as a health check for the first milestone."""

    template_name = "pages/home.html"

# Create your views here.
