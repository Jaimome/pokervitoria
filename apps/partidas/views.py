from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from apps.nucleo.views import contar_usuarios_conectados
from apps.partidas.forms import FormularioCrearPartida, FormularioPartidaPrivada
from apps.partidas.models import (
    EstadoParticipacion,
    ParticipacionPartida,
    PartidaPoker,
    SolicitudPartidaPublica,
    TipoAccion,
    formatear_codigo_carta,
)
from apps.partidas.servicios import (
    SEGUNDOS_TURNO,
    abandonar_partida,
    cancelar_busqueda_publica,
    crear_partida_privada,
    ejecutar_accion,
    generar_codigo_privado_unico,
    iniciar_mano_inicial,
    iniciar_o_consultar_busqueda_publica,
    normalizar_codigo_privado,
    obtener_puntuacion_orientativa,
    unir_usuario_a_partida,
)
from apps.partidas.tiempo_real import notificar_cambio_partida


class VistaListaPartidas(LoginRequiredMixin, ListView):
    """Listado auxiliar de partidas disponibles."""

    model = PartidaPoker
    template_name = "partidas/lista.html"
    context_object_name = "partidas"

    def get_queryset(self):
        return PartidaPoker.objects.order_by("-creada_en")


class VistaCrearPartida(LoginRequiredMixin, CreateView):
    """Vista auxiliar para crear partidas manualmente."""

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


class VistaPartidaPrivada(LoginRequiredMixin, TemplateView):
    """Pantalla para crear o entrar en una partida privada por código."""

    template_name = "partidas/privada.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["formulario"] = kwargs.get(
            "formulario",
            FormularioPartidaPrivada(
                initial={"codigo_creacion": generar_codigo_privado_unico()}
            ),
        )
        return context

    def post(self, request, *args, **kwargs):
        datos_formulario = request.POST.copy()
        if not datos_formulario.get("codigo_creacion"):
            datos_formulario["codigo_creacion"] = generar_codigo_privado_unico()
        formulario = FormularioPartidaPrivada(datos_formulario)
        accion = request.POST.get("accion")
        if accion == "crear":
            codigo = formulario.data.get("codigo_creacion", "")
            try:
                partida = crear_partida_privada(request.user, codigo)
            except ValueError as error:
                formulario.is_valid()
                formulario.add_error("codigo_creacion", str(error))
                return self.render_to_response(
                    self.get_context_data(formulario=formulario)
                )
            try:
                unir_usuario_a_partida(partida, request.user)
            except ValueError as error:
                partida.delete()
                formulario.is_valid()
                formulario.add_error("codigo_creacion", str(error))
                return self.render_to_response(
                    self.get_context_data(formulario=formulario)
                )
            notificar_cambio_partida(partida.pk, "partida_privada_creada")
            messages.success(request, "Partida privada creada correctamente.")
            return redirect("partidas:detalle", pk=partida.pk)

        if accion == "entrar":
            codigo = normalizar_codigo_privado(formulario.data.get("codigo_entrada", ""))
            try:
                partida = PartidaPoker.objects.get(es_privada=True, codigo_privado=codigo)
            except PartidaPoker.DoesNotExist:
                formulario.is_valid()
                formulario.add_error("codigo_entrada", "No existe ninguna partida privada con ese código.")
                return self.render_to_response(
                    self.get_context_data(formulario=formulario)
                )

            participacion_existente = partida.participaciones.filter(usuario=request.user).first()
            if participacion_existente and participacion_existente.estado != EstadoParticipacion.SALIO:
                return redirect("partidas:detalle", pk=partida.pk)
            try:
                unir_usuario_a_partida(partida, request.user, participacion_existente)
            except ValueError as error:
                formulario.is_valid()
                formulario.add_error("codigo_entrada", str(error))
                return self.render_to_response(
                    self.get_context_data(formulario=formulario)
                )
            notificar_cambio_partida(partida.pk, "jugador_unido")
            messages.success(request, "Te has unido a la partida privada.")
            return redirect("partidas:detalle", pk=partida.pk)

        return self.render_to_response(self.get_context_data(formulario=formulario))


class VistaBuscarPartida(LoginRequiredMixin, TemplateView):
    """Pantalla de espera y emparejamiento publico simple."""

    template_name = "partidas/buscar.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        partida = iniciar_o_consultar_busqueda_publica(request.user)
        if partida is not None:
            messages.success(request, "Se ha encontrado una partida pública.")
            return redirect("partidas:detalle", pk=partida.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["usuarios_conectados"] = contar_usuarios_conectados()
        context["busqueda_activa"] = SolicitudPartidaPublica.objects.filter(
            usuario=self.request.user
        ).exists()
        return context


class VistaEstadoBusquedaPartida(LoginRequiredMixin, View):
    """Devuelve el estado de la búsqueda pública sin recargar la pantalla."""

    def get(self, request, *args, **kwargs):
        partida = iniciar_o_consultar_busqueda_publica(request.user)
        if partida is not None:
            return JsonResponse(
                {
                    "partida_encontrada": True,
                    "url": reverse("partidas:detalle", kwargs={"pk": partida.pk}),
                }
            )

        return JsonResponse(
            {
                "partida_encontrada": False,
                "usuarios_conectados": contar_usuarios_conectados(),
            }
        )


class VistaCancelarBusquedaPartida(LoginRequiredMixin, View):
    """Cancela la búsqueda pública actual del usuario."""

    def post(self, request, *args, **kwargs):
        cancelar_busqueda_publica(request.user)
        messages.info(request, "Búsqueda pública cancelada.")
        return redirect("nucleo:inicio")


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
        context["participantes_visibles"] = list(
            self.object.participaciones.exclude(usuario=self.request.user).select_related("usuario")
        )

        cartas_privadas = []
        puntuacion_orientativa = None
        if mano_actual and participacion_actual:
            cartas_privadas = list(
                mano_actual.cartas_privadas.filter(participacion=participacion_actual)
            )
            cartas_para_puntuacion = [
                carta.codigo for carta in cartas_privadas
            ] + mano_actual.cartas_comunitarias_visibles()
            puntuacion_orientativa = obtener_puntuacion_orientativa(cartas_para_puntuacion)

        context["cartas_privadas"] = cartas_privadas
        context["puntuacion_orientativa"] = puntuacion_orientativa
        if puntuacion_orientativa is not None:
            context["color_puntuacion_orientativa"] = (
                f"hsl({(puntuacion_orientativa - 1) * 13}, 72%, 42%)"
            )
        else:
            context["color_puntuacion_orientativa"] = None
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
        context["objetivo_minimo_subida"] = (
            mano_actual.apuesta_actual_ronda + mano_actual.incremento_minimo_subida
            if mano_actual
            else 0
        )
        context["objetivo_maximo_subida"] = (
            participacion_actual.apuesta_en_ronda + participacion_actual.fichas
            if participacion_actual
            else 0
        )
        context["cartas_comunitarias"] = (
            [
                formatear_codigo_carta(carta)
                for carta in mano_actual.cartas_comunitarias_visibles()
            ]
            if mano_actual
            else []
        )
        context["puede_subir"] = bool(
            participacion_actual
            and mano_actual
            and (participacion_actual.apuesta_en_ronda + participacion_actual.fichas)
            >= (mano_actual.apuesta_actual_ronda + mano_actual.incremento_minimo_subida)
        )
        context["acciones_recientes"] = (
            mano_actual.acciones.select_related("participacion__usuario") if mano_actual else []
        )
        context["ganadores_mano"] = (
            mano_actual.ganadores.select_related("usuario") if mano_actual else []
        )
        context["segundos_turno"] = SEGUNDOS_TURNO
        if mano_actual and mano_actual.turno_actual_desde:
            context["turno_expira_en"] = mano_actual.turno_actual_desde + timedelta(
                seconds=SEGUNDOS_TURNO
            )
        else:
            context["turno_expira_en"] = None
        context["nombre_turno_actual"] = (
            mano_actual.turno_actual.usuario.username
            if mano_actual and mano_actual.turno_actual
            else None
        )
        return context


class VistaUnirsePartida(LoginRequiredMixin, View):
    """Anade al usuario actual a una partida si hay un asiento disponible."""

    def post(self, request, *args, **kwargs):
        partida = PartidaPoker.objects.get(pk=kwargs["pk"])

        participacion_existente = partida.participaciones.filter(usuario=request.user).first()
        if participacion_existente and participacion_existente.estado != EstadoParticipacion.SALIO:
            messages.info(request, "Ya formas parte de esta partida.")
            return redirect("partidas:detalle", pk=partida.pk)

        try:
            unir_usuario_a_partida(partida, request.user, participacion_existente)
        except (IntegrityError, ValueError) as error:
            messages.error(request, str(error))
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
        messages.success(
            request,
            "La partida se ha iniciado y ya se han repartido las cartas privadas.",
        )
        return redirect("partidas:detalle", pk=partida.pk)


class VistaAccionPartida(LoginRequiredMixin, View):
    """Procesa una accion del jugador actual sobre la mano activa."""

    def post(self, request, *args, **kwargs):
        try:
            partida = PartidaPoker.objects.get(pk=kwargs["pk"])
        except PartidaPoker.DoesNotExist as error:
            raise Http404("La partida indicada no existe.") from error

        mano = partida.manos.order_by("-creada_en").first()
        participacion = partida.participaciones.filter(usuario=request.user).first()
        tipo_accion = request.POST.get("tipo_accion", "")

        if mano is None or participacion is None:
            messages.error(request, "No se puede procesar la acción solicitada.")
            return redirect("partidas:detalle", pk=partida.pk)

        if tipo_accion not in {
            TipoAccion.PASAR,
            TipoAccion.IGUALAR,
            TipoAccion.SUBIR,
            TipoAccion.RETIRARSE,
        }:
            messages.error(request, "La acción indicada no es válida.")
            return redirect("partidas:detalle", pk=partida.pk)

        objetivo_subida = None
        if tipo_accion == TipoAccion.SUBIR:
            objetivo_subida_texto = request.POST.get("objetivo_subida", "").strip()
            try:
                objetivo_subida = int(objetivo_subida_texto)
            except ValueError:
                messages.error(
                    request,
                    "Debes indicar una cantidad numérica válida para subir.",
                )
                return redirect("partidas:detalle", pk=partida.pk)

        try:
            ejecutar_accion(
                mano,
                participacion,
                tipo_accion,
                objetivo_subida=objetivo_subida,
            )
        except ValueError as error:
            messages.error(request, str(error))
            return redirect("partidas:detalle", pk=partida.pk)

        notificar_cambio_partida(partida.pk, "accion_registrada")
        return redirect("partidas:detalle", pk=partida.pk)


class VistaAbandonarPartida(LoginRequiredMixin, View):
    """Permite salir de una partida sin perder las fichas no comprometidas."""

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
        return redirect("nucleo:inicio")
