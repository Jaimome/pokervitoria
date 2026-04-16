from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView

from apps.partidas.forms import FormularioCrearPartida
from apps.partidas.models import (
    EstadoParticipacion,
    ManoPoker,
    ParticipacionPartida,
    PartidaPoker,
    TipoAccion,
)
from apps.partidas.servicios import abandonar_partida, ejecutar_accion, iniciar_mano_inicial
from apps.partidas.tiempo_real import notificar_cambio_partida


class VistaListaPartidas(LoginRequiredMixin, ListView):
    """Muestra las partidas disponibles para el usuario autenticado."""

    model = PartidaPoker
    template_name = "partidas/lista.html"
    context_object_name = "partidas"


class VistaCrearPartida(LoginRequiredMixin, CreateView):
    """Permite crear una nueva partida desde el navegador."""

    model = PartidaPoker
    form_class = FormularioCrearPartida
    template_name = "partidas/crear.html"

    def form_valid(self, form):
        form.instance.creador = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "La partida se ha creado correctamente.")
        return response

    def get_success_url(self):
        return reverse_lazy("partidas:detalle", kwargs={"pk": self.object.pk})


class VistaDetallePartida(LoginRequiredMixin, DetailView):
    """Muestra la informacion principal de una partida concreta."""

    model = PartidaPoker
    template_name = "partidas/detalle.html"
    context_object_name = "partida"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        participacion_actual = self.object.participaciones.exclude(
            estado=EstadoParticipacion.SALIO
        ).filter(usuario=self.request.user).first()
        mano_actual = self.object.manos.order_by("-creada_en").first()

        context["participacion_actual"] = participacion_actual
        context["ya_unido"] = participacion_actual is not None
        context["asiento_libre"] = self.object.obtener_primer_asiento_libre()
        context["puede_iniciarse"] = self.object.puede_iniciarse()
        context["mano_actual"] = mano_actual
        if mano_actual and participacion_actual:
            context["cartas_privadas"] = mano_actual.cartas_privadas.filter(
                participacion=participacion_actual
            )
        else:
            context["cartas_privadas"] = []

        context["es_mi_turno"] = bool(
            mano_actual
            and participacion_actual
            and mano_actual.turno_actual_id == participacion_actual.id
        )
        context["apuesta_por_igualar"] = (
            max(0, mano_actual.apuesta_actual_ronda - participacion_actual.apuesta_en_ronda)
            if mano_actual and participacion_actual
            else 0
        )
        context["cartas_comunitarias"] = mano_actual.cartas_comunitarias_visibles() if mano_actual else []
        context["acciones_recientes"] = mano_actual.acciones.select_related(
            "participacion__usuario"
        ) if mano_actual else []
        return context


class VistaUnirsePartida(LoginRequiredMixin, View):
    """Anade al usuario actual a una partida si hay un asiento disponible."""

    def post(self, request, *args, **kwargs):
        partida = PartidaPoker.objects.get(pk=kwargs["pk"])

        participacion_existente = partida.participaciones.filter(usuario=request.user).first()
        if participacion_existente and participacion_existente.estado != EstadoParticipacion.SALIO:
            messages.info(request, "Ya formas parte de esta partida.")
            return redirect("partidas:detalle", pk=partida.pk)

        asiento_libre = partida.obtener_primer_asiento_libre()
        if asiento_libre is None:
            messages.error(request, "La partida ya esta completa.")
            return redirect("partidas:detalle", pk=partida.pk)

        try:
            if participacion_existente and participacion_existente.estado == EstadoParticipacion.SALIO:
                participacion_existente.numero_asiento = asiento_libre
                participacion_existente.estado = EstadoParticipacion.UNIDO
                participacion_existente.activa_en_mano = False
                participacion_existente.salio_en = None
                participacion_existente.save(
                    update_fields=["numero_asiento", "estado", "activa_en_mano", "salio_en"]
                )
            else:
                ParticipacionPartida.objects.create(
                    partida=partida,
                    usuario=request.user,
                    numero_asiento=asiento_libre,
                    estado=EstadoParticipacion.UNIDO,
                )
        except IntegrityError:
            messages.error(request, "No se ha podido unir el usuario a la partida.")
            return redirect("partidas:detalle", pk=partida.pk)

        notificar_cambio_partida(partida.pk, "jugador_unido")
        messages.success(request, "Te has unido a la partida correctamente.")
        return redirect("partidas:detalle", pk=partida.pk)


class VistaIniciarPartida(LoginRequiredMixin, View):
    """Inicia una mano de prueba y reparte cartas privadas a los jugadores."""

    def post(self, request, *args, **kwargs):
        try:
            partida = PartidaPoker.objects.get(pk=kwargs["pk"])
        except PartidaPoker.DoesNotExist as error:
            raise Http404("La partida indicada no existe.") from error

        try:
            iniciar_mano_inicial(partida)
        except ValueError as error:
            messages.error(request, str(error))
            return redirect("partidas:detalle", pk=partida.pk)

        notificar_cambio_partida(partida.pk, "partida_iniciada")
        messages.success(request, "La partida se ha iniciado y ya se han repartido las cartas privadas.")
        return redirect("partidas:detalle", pk=partida.pk)


class VistaAccionPartida(LoginRequiredMixin, View):
    """Procesa una accion minima del jugador actual sobre la mano activa."""

    def post(self, request, *args, **kwargs):
        try:
            partida = PartidaPoker.objects.get(pk=kwargs["pk"])
        except PartidaPoker.DoesNotExist as error:
            raise Http404("La partida indicada no existe.") from error

        mano = partida.manos.order_by("-creada_en").first()
        participacion = partida.participaciones.filter(usuario=request.user).first()
        tipo_accion = request.POST.get("tipo_accion", "")

        if mano is None or participacion is None:
            messages.error(request, "No se puede procesar la accion solicitada.")
            return redirect("partidas:detalle", pk=partida.pk)

        if tipo_accion not in {TipoAccion.PASAR, TipoAccion.IGUALAR, TipoAccion.RETIRARSE}:
            messages.error(request, "La accion indicada no es valida.")
            return redirect("partidas:detalle", pk=partida.pk)

        try:
            ejecutar_accion(mano, participacion, tipo_accion)
        except ValueError as error:
            messages.error(request, str(error))
            return redirect("partidas:detalle", pk=partida.pk)

        notificar_cambio_partida(partida.pk, "accion_registrada")
        messages.success(request, f"Accion registrada: {tipo_accion}.")
        return redirect("partidas:detalle", pk=partida.pk)


class VistaAbandonarPartida(LoginRequiredMixin, View):
    """Permite salir de una partida para no bloquear sesiones de prueba."""

    def post(self, request, *args, **kwargs):
        try:
            partida = PartidaPoker.objects.get(pk=kwargs["pk"])
        except PartidaPoker.DoesNotExist as error:
            raise Http404("La partida indicada no existe.") from error

        participacion = partida.participaciones.filter(usuario=request.user).first()
        if participacion is None:
            messages.error(request, "No formas parte de esta partida.")
            return redirect("partidas:detalle", pk=partida.pk)

        abandonar_partida(partida, participacion)
        notificar_cambio_partida(partida.pk, "jugador_salio")
        messages.success(request, "Has salido de la partida correctamente.")
        return redirect("partidas:lista")
