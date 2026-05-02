from itertools import combinations


VALOR_A_NUMERO = {
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "10": 10,
    "J": 11,
    "Q": 12,
    "K": 13,
    "A": 14,
}

NOMBRE_CATEGORIAS = {
    8: "Escalera de color",
    7: "Poker",
    6: "Full",
    5: "Color",
    4: "Escalera",
    3: "Trio",
    2: "Doble pareja",
    1: "Pareja",
    0: "Carta alta",
}


def evaluar_mejor_mano(cartas: list[str]) -> dict:
    """
    Evalua la mejor mano posible a partir de 7 cartas de Texas Hold'em.

    Devuelve un diccionario con:
    - `rango`: tupla comparable para desempates
    - `nombre`: descripcion legible de la categoria
    - `cartas`: combinacion ganadora de 5 cartas
    """

    if len(cartas) < 5:
        raise ValueError("Se necesitan al menos cinco cartas para evaluar una mano.")

    mejor_resultado = None
    for combinacion in combinations(cartas, 5):
        resultado = _evaluar_cinco_cartas(list(combinacion))
        if mejor_resultado is None or resultado["rango"] > mejor_resultado["rango"]:
            mejor_resultado = resultado

    return mejor_resultado


def comparar_manos(cartas_por_jugador: dict) -> list[dict]:
    """
    Evalua varias manos y devuelve los mejores resultados empatados o ganadores.
    """

    resultados = []
    for participacion, cartas in cartas_por_jugador.items():
        evaluacion = evaluar_mejor_mano(cartas)
        resultados.append(
            {
                "participacion": participacion,
                "rango": evaluacion["rango"],
                "nombre": evaluacion["nombre"],
                "cartas": evaluacion["cartas"],
            }
        )

    mejor_rango = max(resultado["rango"] for resultado in resultados)
    return [
        resultado
        for resultado in resultados
        if resultado["rango"] == mejor_rango
    ]


def _evaluar_cinco_cartas(cartas: list[str]) -> dict:
    cartas_parseadas = sorted((_parsear_carta(carta) for carta in cartas), reverse=True)
    valores = sorted((valor for valor, _ in cartas_parseadas), reverse=True)
    palos = [palo for _, palo in cartas_parseadas]
    conteos = _obtener_conteos_ordenados(valores)

    es_color = len(set(palos)) == 1
    valor_escalera = _detectar_escalera(valores)

    if es_color and valor_escalera is not None:
        rango = (8, valor_escalera)
        return _resultado(rango, cartas)

    if conteos[0][1] == 4:
        valor_poker = conteos[0][0]
        kicker = max(valor for valor in valores if valor != valor_poker)
        rango = (7, valor_poker, kicker)
        return _resultado(rango, cartas)

    if conteos[0][1] == 3 and conteos[1][1] == 2:
        rango = (6, conteos[0][0], conteos[1][0])
        return _resultado(rango, cartas)

    if es_color:
        rango = (5, *valores)
        return _resultado(rango, cartas)

    if valor_escalera is not None:
        rango = (4, valor_escalera)
        return _resultado(rango, cartas)

    if conteos[0][1] == 3:
        valor_trio = conteos[0][0]
        kickers = sorted((valor for valor in valores if valor != valor_trio), reverse=True)
        rango = (3, valor_trio, *kickers)
        return _resultado(rango, cartas)

    parejas = [valor for valor, cantidad in conteos if cantidad == 2]
    if len(parejas) == 2:
        pareja_alta, pareja_baja = sorted(parejas, reverse=True)
        kicker = max(valor for valor in valores if valor not in parejas)
        rango = (2, pareja_alta, pareja_baja, kicker)
        return _resultado(rango, cartas)

    if len(parejas) == 1:
        pareja = parejas[0]
        kickers = sorted((valor for valor in valores if valor != pareja), reverse=True)
        rango = (1, pareja, *kickers)
        return _resultado(rango, cartas)

    rango = (0, *valores)
    return _resultado(rango, cartas)


def _resultado(rango: tuple, cartas: list[str]) -> dict:
    return {
        "rango": rango,
        "nombre": NOMBRE_CATEGORIAS[rango[0]],
        "cartas": list(cartas),
    }


def _parsear_carta(carta: str) -> tuple[int, str]:
    palo = carta[-1]
    valor = carta[:-1]
    return VALOR_A_NUMERO[valor], palo


def _obtener_conteos_ordenados(valores: list[int]) -> list[tuple[int, int]]:
    conteos = {}
    for valor in valores:
        conteos[valor] = conteos.get(valor, 0) + 1
    return sorted(conteos.items(), key=lambda item: (item[1], item[0]), reverse=True)


def _detectar_escalera(valores: list[int]) -> int | None:
    valores_unicos = sorted(set(valores), reverse=True)
    if valores_unicos == [14, 5, 4, 3, 2]:
        return 5

    if len(valores_unicos) != 5:
        return None

    if valores_unicos[0] - valores_unicos[4] == 4:
        return valores_unicos[0]

    return None
