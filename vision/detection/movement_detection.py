import cv2


LIMIAR_MOVIMENTACAO = 0.70


def extrair_regiao(
    imagem,
    x,
    y,
    largura,
    altura
):
    return imagem[
        y:y + altura,
        x:x + largura
    ]


def comparar_regioes(
    regiao_antes,
    regiao_depois
):
    if (
        regiao_antes is None
        or regiao_depois is None
        or regiao_antes.size == 0
        or regiao_depois.size == 0
    ):
        return 0

    tamanho = (150, 150)

    antes = cv2.resize(
        regiao_antes,
        tamanho
    )

    depois = cv2.resize(
        regiao_depois,
        tamanho
    )

    antes = cv2.cvtColor(
        antes,
        cv2.COLOR_BGR2HSV
    )

    depois = cv2.cvtColor(
        depois,
        cv2.COLOR_BGR2HSV
    )

    hist_antes = cv2.calcHist(
        [antes],
        [0, 1],
        None,
        [50, 60],
        [0, 180, 0, 256]
    )

    hist_depois = cv2.calcHist(
        [depois],
        [0, 1],
        None,
        [50, 60],
        [0, 180, 0, 256]
    )

    cv2.normalize(
        hist_antes,
        hist_antes,
        0,
        1,
        cv2.NORM_MINMAX
    )

    cv2.normalize(
        hist_depois,
        hist_depois,
        0,
        1,
        cv2.NORM_MINMAX
    )

    similaridade = cv2.compareHist(
        hist_antes,
        hist_depois,
        cv2.HISTCMP_CORREL
    )

    return similaridade


def detectar_movimentacoes(
    imagem_antes,
    imagem_depois,
    regioes
):
    candidatos = []

    # Testa todas as combinações possíveis
    for i in range(len(regioes)):
        regiao_origem = regioes[i]

        recorte_antes = extrair_regiao(
            imagem_antes,
            regiao_origem["x"],
            regiao_origem["y"],
            regiao_origem["largura"],
            regiao_origem["altura"]
        )

        for j in range(len(regioes)):
            if i == j:
                continue

            regiao_destino = regioes[j]

            recorte_depois = extrair_regiao(
                imagem_depois,
                regiao_destino["x"],
                regiao_destino["y"],
                regiao_destino["largura"],
                regiao_destino["altura"]
            )

            similaridade = comparar_regioes(
                recorte_antes,
                recorte_depois
            )

            candidatos.append(
                {
                    "origem": i,
                    "destino": j,
                    "similaridade": similaridade
                }
            )

    # Ordena do mais parecido para o menos parecido
    candidatos.sort(
        key=lambda item: item["similaridade"],
        reverse=True
    )


    movimentacoes = []

    # Uma região que já participou de uma movimentação
    # não pode ser reutilizada nem como origem nem como destino.
    regioes_usadas = set()

    for candidato in candidatos:
        origem = candidato["origem"]
        destino = candidato["destino"]
        similaridade = candidato["similaridade"]

        if similaridade < LIMIAR_MOVIMENTACAO:
            continue

        # Se qualquer uma das duas regiões já foi utilizada,
        # descartamos esta associação.
        if origem in regioes_usadas:
            continue

        if destino in regioes_usadas:
            continue

        movimentacoes.append(
            candidato
        )

        # As duas regiões passam a estar ocupadas
        # por esta movimentação.
        regioes_usadas.add(origem)
        regioes_usadas.add(destino)

    return (
        movimentacoes,
        regioes_usadas
    )