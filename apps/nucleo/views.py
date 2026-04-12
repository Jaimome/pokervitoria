from django.views.generic import TemplateView


class VistaInicio(TemplateView):
    """Pagina inicial minima para comprobar que el proyecto arranca."""

    template_name = "pages/inicio.html"
