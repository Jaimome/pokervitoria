from django import template


register = template.Library()


@register.filter
def corregir_mojibake(valor):
    """Repara mensajes UTF-8 que lleguen mal decodificados a la plantilla."""

    if not isinstance(valor, str):
        return valor

    if not any(ord(caracter) > 127 for caracter in valor):
        return valor

    try:
        return valor.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return valor
