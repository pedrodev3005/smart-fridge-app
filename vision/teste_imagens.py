import cv2
import os
import re
import subprocess
import time
import unicodedata

from difflib import SequenceMatcher


HF_TOKEN = os.environ.get("HF_TOKEN")

MODELO_REPO = "google/gemma-3n-E2B-it-litert-lm"
ARQUIVO_MODELO = "gemma-3n-E2B-it-int4.litertlm"

PASTA_IMAGENS = "vision/images"

CAMINHO_ANTES = os.path.join(
    PASTA_IMAGENS,
    "estado1.png"
)

CAMINHO_DEPOIS = os.path.join(
    PASTA_IMAGENS,
    "estado2.png"
)


PROMPT = """
Analise esta imagem de uma região de uma prateleira de geladeira.

Primeiro determine se existe algum produto ou alimento visível nesta região.

Se NÃO houver produto ou alimento, responda exatamente:

Presenca: nao
Produto: Nenhum
Marca: Nenhuma
Categoria: Nenhuma
Confianca: alta

Se houver produto ou alimento, identifique-o considerando o conjunto completo
de informações da imagem:

- texto visível no rótulo;
- aparência da embalagem;
- cor e aparência do conteúdo;
- imagens e elementos gráficos;
- formato do recipiente;
- contexto visual geral.

Não dependa apenas da leitura do texto.

O campo Produto deve representar o alimento completo identificado,
incluindo tipo e sabor quando puderem ser determinados com segurança.

Não inclua volume, porcentagem ou frases promocionais no nome do produto.

Se existir um produto, responda exatamente:

Presenca: sim
Produto: ...
Marca: ...
Categoria: ...
Confianca: alta, media ou baixa
"""


def detectarMudanca(imagemAntes, imagemDepois):

    cinzaAntes = cv2.cvtColor(
        imagemAntes,
        cv2.COLOR_BGR2GRAY
    )

    cinzaDepois = cv2.cvtColor(
        imagemDepois,
        cv2.COLOR_BGR2GRAY
    )

    cinzaAntes = cv2.GaussianBlur(
        cinzaAntes,
        (5, 5),
        0
    )

    cinzaDepois = cv2.GaussianBlur(
        cinzaDepois,
        (5, 5),
        0
    )

    diferenca = cv2.absdiff(
        cinzaAntes,
        cinzaDepois
    )

    _, mascara = cv2.threshold(
        diferenca,
        35,
        255,
        cv2.THRESH_BINARY
    )

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (5, 5)
    )

    mascara = cv2.morphologyEx(
        mascara,
        cv2.MORPH_CLOSE,
        kernel
    )

    mascara = cv2.dilate(
        mascara,
        kernel,
        iterations=2
    )

    contornos, _ = cv2.findContours(
        mascara,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    contornosValidos = []

    altura, largura = imagemDepois.shape[:2]
    areaImagem = altura * largura

    for contorno in contornos:

        area = cv2.contourArea(contorno)

        if area < 1000:
            continue

        if area > areaImagem * 0.50:
            continue

        contornosValidos.append(contorno)

    return contornosValidos, mascara


def caixasSeSobrepoem(caixa1, caixa2, distancia=30):

    x1, y1, x2, y2 = caixa1
    a1, b1, a2, b2 = caixa2

    separadasHorizontalmente = (
        x2 + distancia < a1
        or
        a2 + distancia < x1
    )

    separadasVerticalmente = (
        y2 + distancia < b1
        or
        b2 + distancia < y1
    )

    if (
        separadasHorizontalmente
        or
        separadasVerticalmente
    ):
        return False

    return True


def unirDuasCaixas(caixa1, caixa2):

    x1, y1, x2, y2 = caixa1
    a1, b1, a2, b2 = caixa2

    return (
        min(x1, a1),
        min(y1, b1),
        max(x2, a2),
        max(y2, b2)
    )


def fundirCaixas(contornos):

    caixas = []

    for contorno in contornos:

        x, y, w, h = cv2.boundingRect(
            contorno
        )

        caixas.append(
            (
                x,
                y,
                x + w,
                y + h
            )
        )

    mudou = True

    while mudou:

        mudou = False
        novasCaixas = []

        usadas = [False] * len(caixas)

        for i in range(len(caixas)):

            if usadas[i]:
                continue

            caixaAtual = caixas[i]

            for j in range(
                i + 1,
                len(caixas)
            ):

                if usadas[j]:
                    continue

                if caixasSeSobrepoem(
                    caixaAtual,
                    caixas[j]
                ):

                    caixaAtual = unirDuasCaixas(
                        caixaAtual,
                        caixas[j]
                    )

                    usadas[j] = True
                    mudou = True

            usadas[i] = True

            novasCaixas.append(
                caixaAtual
            )

        caixas = novasCaixas

    return caixas


def criarRecortesPorCaixa(
    imagemAntes,
    imagemDepois,
    caixas
):

    altura, largura = imagemDepois.shape[:2]

    regioes = []

    margem = 40

    for i, caixa in enumerate(caixas):

        x1, y1, x2, y2 = caixa

        xMin = max(
            0,
            x1 - margem
        )

        yMin = max(
            0,
            y1 - margem
        )

        xMax = min(
            largura,
            x2 + margem
        )

        yMax = min(
            altura,
            y2 + margem
        )

        recorteAntes = imagemAntes[
            yMin:yMax,
            xMin:xMax
        ]

        recorteDepois = imagemDepois[
            yMin:yMax,
            xMin:xMax
        ]

        regioes.append({
            "numero": i + 1,
            "antes": recorteAntes,
            "depois": recorteDepois,
            "x": xMin,
            "y": yMin,
            "xMax": xMax,
            "yMax": yMax
        })

    return regioes


def analisarGemma(caminhoImagem):

    comando = [
        "litert-lm",
        "run",
        "--from-huggingface-repo",
        MODELO_REPO,
        ARQUIVO_MODELO,
        "--vision-backend",
        "gpu",
        "--attachment",
        caminhoImagem,
        "--prompt",
        PROMPT
    ]

    if HF_TOKEN:

        comando.extend([
            "--huggingface-token",
            HF_TOKEN
        ])

    resultado = subprocess.run(
        comando,
        capture_output=True,
        text=True
    )

    return resultado.stdout


def pegarCampo(texto, campo):

    for linha in texto.splitlines():

        if linha.lower().startswith(
            campo.lower() + ":"
        ):

            return linha.split(
                ":",
                1
            )[1].strip()

    return ""


def interpretarResposta(texto):

    presenca = pegarCampo(
        texto,
        "Presenca"
    ).lower()

    produto = pegarCampo(
        texto,
        "Produto"
    )

    marca = pegarCampo(
        texto,
        "Marca"
    )

    categoria = pegarCampo(
        texto,
        "Categoria"
    )

    confianca = pegarCampo(
        texto,
        "Confianca"
    )

    if not confianca:
        confianca = "não informada"

    return {
        "presenca": presenca,
        "produto": produto,
        "marca": marca,
        "categoria": categoria,
        "confianca": confianca
    }


def normalizar(texto):

    texto = texto.lower().strip()

    texto = unicodedata.normalize(
        "NFD",
        texto
    )

    texto = "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )

    texto = re.sub(
        r"[^a-z0-9 ]",
        " ",
        texto
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.strip()


def similaridade(texto1, texto2):

    texto1 = normalizar(texto1)
    texto2 = normalizar(texto2)

    if not texto1 or not texto2:
        return 0

    return SequenceMatcher(
        None,
        texto1,
        texto2
    ).ratio()


def mesmoProduto(produto1, produto2):

    nome1 = normalizar(
        produto1["produto"]
    )

    nome2 = normalizar(
        produto2["produto"]
    )

    marca1 = normalizar(
        produto1["marca"]
    )

    marca2 = normalizar(
        produto2["marca"]
    )

    marcasInvalidas = [
        "",
        "nenhuma",
        "nenhum",
        "nao identificada",
        "nao identificado"
    ]

    marcaConhecida1 = (
        marca1 not in marcasInvalidas
    )

    marcaConhecida2 = (
        marca2 not in marcasInvalidas
    )

    similaridadeProduto = similaridade(
        nome1,
        nome2
    )

    similaridadeMarca = similaridade(
        marca1,
        marca2
    )

    if marcaConhecida1 and marcaConhecida2:

        if (
            similaridadeMarca >= 0.75
            and
            similaridadeProduto >= 0.60
        ):
            return True

        return False

    if similaridadeProduto >= 0.85:
        return True

    return False


def decidirMudancaLocal(
    antes,
    depois
):

    temAntes = (
        normalizar(
            antes["presenca"]
        ) == "sim"
    )

    temDepois = (
        normalizar(
            depois["presenca"]
        ) == "sim"
    )

    if not temAntes and temDepois:
        return "Entrada"

    if temAntes and not temDepois:
        return "Retirada"

    if not temAntes and not temDepois:
        return "Nenhuma mudança relevante"

    if mesmoProduto(
        antes,
        depois
    ):
        return "Movimento local"

    return "Substituição"


def criarEventosProvisorios(resultadosRegioes):

    entradas = []
    retiradas = []
    substituicoes = []
    movimentosLocais = []

    for resultado in resultadosRegioes:

        tipo = resultado["tipo"]
        numero = resultado["regiao"]

        antes = resultado["antes"]
        depois = resultado["depois"]

        if tipo == "Entrada":

            entradas.append({
                "regiao": numero,
                "produto": depois,
                "origem": "entrada"
            })

        elif tipo == "Retirada":

            retiradas.append({
                "regiao": numero,
                "produto": antes,
                "origem": "retirada"
            })

        elif tipo == "Substituição":

            substituicao = {
                "regiao": numero,
                "antes": antes,
                "depois": depois,
                "usouAntesMovimento": False,
                "usouDepoisMovimento": False
            }

            substituicoes.append(
                substituicao
            )

            retiradas.append({
                "regiao": numero,
                "produto": antes,
                "origem": "substituicao",
                "substituicao": substituicao
            })

            entradas.append({
                "regiao": numero,
                "produto": depois,
                "origem": "substituicao",
                "substituicao": substituicao
            })

        elif tipo == "Movimento local":

            movimentosLocais.append({
                "regiao": numero,
                "produto": depois
            })

    return (
        entradas,
        retiradas,
        substituicoes,
        movimentosLocais
    )


def consolidarEventos(resultadosRegioes):

    (
        entradas,
        retiradas,
        substituicoes,
        movimentosLocais
    ) = criarEventosProvisorios(
        resultadosRegioes
    )

    movimentos = []

    entradasUsadas = set()
    retiradasUsadas = set()

    for i, retirada in enumerate(retiradas):

        melhorEntrada = None
        melhorIndice = None
        melhorPontuacao = 0

        for j, entrada in enumerate(entradas):

            if j in entradasUsadas:
                continue

            if (
                retirada["regiao"]
                ==
                entrada["regiao"]
            ):
                continue

            if mesmoProduto(
                retirada["produto"],
                entrada["produto"]
            ):

                pontuacao = similaridade(
                    retirada["produto"]["produto"],
                    entrada["produto"]["produto"]
                )

                if pontuacao > melhorPontuacao:

                    melhorPontuacao = pontuacao
                    melhorEntrada = entrada
                    melhorIndice = j

        if melhorEntrada is not None:

            retiradasUsadas.add(i)
            entradasUsadas.add(melhorIndice)

            if retirada["origem"] == "substituicao":

                retirada[
                    "substituicao"
                ][
                    "usouAntesMovimento"
                ] = True

            if melhorEntrada["origem"] == "substituicao":

                melhorEntrada[
                    "substituicao"
                ][
                    "usouDepoisMovimento"
                ] = True

            movimentos.append({
                "produto": melhorEntrada["produto"],
                "regiaoAntes": retirada["regiao"],
                "regiaoDepois": melhorEntrada["regiao"]
            })

    eventosFinais = []

    for movimento in movimentos:

        eventosFinais.append({
            "tipo": "Movimento",
            "produto": movimento["produto"],
            "regiaoAntes": movimento["regiaoAntes"],
            "regiaoDepois": movimento["regiaoDepois"]
        })

    for movimento in movimentosLocais:

        eventosFinais.append({
            "tipo": "Movimento",
            "produto": movimento["produto"],
            "regiaoAntes": movimento["regiao"],
            "regiaoDepois": movimento["regiao"]
        })

    for i, entrada in enumerate(entradas):

        if i in entradasUsadas:
            continue

        if entrada["origem"] == "substituicao":
            continue

        eventosFinais.append({
            "tipo": "Entrada",
            "produto": entrada["produto"],
            "regiao": entrada["regiao"]
        })

    for i, retirada in enumerate(retiradas):

        if i in retiradasUsadas:
            continue

        if retirada["origem"] == "substituicao":
            continue

        eventosFinais.append({
            "tipo": "Retirada",
            "produto": retirada["produto"],
            "regiao": retirada["regiao"]
        })

    for substituicao in substituicoes:

        usouAntes = substituicao[
            "usouAntesMovimento"
        ]

        usouDepois = substituicao[
            "usouDepoisMovimento"
        ]

        if not usouAntes and not usouDepois:

            eventosFinais.append({
                "tipo": "Substituição",
                "antes": substituicao["antes"],
                "depois": substituicao["depois"],
                "regiao": substituicao["regiao"]
            })

    return eventosFinais


def mostrarProduto(produto):

    print(
        f"Produto: {produto['produto']}"
    )

    print(
        f"Marca: {produto['marca']}"
    )

    print(
        f"Categoria: {produto['categoria']}"
    )

    print(
        f"Confiança: {produto['confianca']}"
    )


# =========================================================
# PROGRAMA PRINCIPAL
# =========================================================


imagemAntes = cv2.imread(
    CAMINHO_ANTES
)

imagemDepois = cv2.imread(
    CAMINHO_DEPOIS
)


if imagemAntes is None:

    print(
        f"Erro: não foi possível abrir "
        f"{CAMINHO_ANTES}"
    )

    exit()


if imagemDepois is None:

    print(
        f"Erro: não foi possível abrir "
        f"{CAMINHO_DEPOIS}"
    )

    exit()


if imagemAntes.shape != imagemDepois.shape:

    print(
        "Erro: as duas imagens precisam "
        "ter o mesmo tamanho."
    )

    exit()


print("Comparando imagens...")


contornos, mascara = detectarMudanca(
    imagemAntes,
    imagemDepois
)


print(
    f"Contornos alterados encontrados: "
    f"{len(contornos)}"
)


if len(contornos) == 0:

    print(
        "Nenhuma mudança relevante encontrada."
    )

    exit()


caixasFundidas = fundirCaixas(
    contornos
)


print(
    f"Regiões finais após fusão: "
    f"{len(caixasFundidas)}"
)


regioes = criarRecortesPorCaixa(
    imagemAntes,
    imagemDepois,
    caixasFundidas
)


visualizacao = imagemDepois.copy()


for regiao in regioes:

    cv2.rectangle(
        visualizacao,
        (
            regiao["x"],
            regiao["y"]
        ),
        (
            regiao["xMax"],
            regiao["yMax"]
        ),
        (0, 255, 0),
        2
    )


cv2.imshow(
    "Mascara de mudancas",
    mascara
)

cv2.imshow(
    "Mudancas detectadas",
    visualizacao
)


resultadosRegioes = []

tempoTotalIA = 0


for regiao in regioes:

    numero = regiao["numero"]

    caminhoAntes = os.path.join(
        PASTA_IMAGENS,
        f"regiao_{numero}_antes.png"
    )

    caminhoDepois = os.path.join(
        PASTA_IMAGENS,
        f"regiao_{numero}_depois.png"
    )

    cv2.imwrite(
        caminhoAntes,
        regiao["antes"]
    )

    cv2.imwrite(
        caminhoDepois,
        regiao["depois"]
    )

    cv2.imshow(
        f"Regiao {numero} - ANTES",
        regiao["antes"]
    )

    cv2.imshow(
        f"Regiao {numero} - DEPOIS",
        regiao["depois"]
    )


    print("\n=========================")
    print(f"REGIÃO {numero}")
    print("=========================")


    print("\nGemma analisando ANTES...")

    inicioAntes = time.time()

    respostaAntesTexto = analisarGemma(
        caminhoAntes
    )

    fimAntes = time.time()

    tempoAntes = (
        fimAntes - inicioAntes
    )


    print("\nResultado ANTES:")

    print(
        respostaAntesTexto
    )


    respostaAntes = interpretarResposta(
        respostaAntesTexto
    )


    print("\nGemma analisando DEPOIS...")

    inicioDepois = time.time()

    respostaDepoisTexto = analisarGemma(
        caminhoDepois
    )

    fimDepois = time.time()

    tempoDepois = (
        fimDepois - inicioDepois
    )


    print("\nResultado DEPOIS:")

    print(
        respostaDepoisTexto
    )


    respostaDepois = interpretarResposta(
        respostaDepoisTexto
    )


    tipoMudanca = decidirMudancaLocal(
        respostaAntes,
        respostaDepois
    )


    tempoRegiao = (
        tempoAntes
        +
        tempoDepois
    )


    tempoTotalIA += tempoRegiao


    resultadosRegioes.append({
        "regiao": numero,
        "tipo": tipoMudanca,
        "antes": respostaAntes,
        "depois": respostaDepois,
        "tempoAntes": tempoAntes,
        "tempoDepois": tempoDepois
    })


print("\n")
print("=========================")
print("ANÁLISE DAS REGIÕES")
print("=========================")


for resultado in resultadosRegioes:

    print(
        f"\nRegião {resultado['regiao']}: "
        f"{resultado['tipo']}"
    )


eventosFinais = consolidarEventos(
    resultadosRegioes
)


print("\n")
print("=========================")
print("RESULTADO FINAL")
print("=========================")


if len(eventosFinais) == 0:

    print(
        "Nenhuma mudança relevante encontrada."
    )


for i, evento in enumerate(
    eventosFinais,
    start=1
):

    print(
        f"\nEvento {i}:"
    )

    print(
        f"Tipo de mudança: "
        f"{evento['tipo']}"
    )


    if evento["tipo"] == "Entrada":

        mostrarProduto(
            evento["produto"]
        )


    elif evento["tipo"] == "Retirada":

        mostrarProduto(
            evento["produto"]
        )


    elif evento["tipo"] == "Movimento":

        mostrarProduto(
            evento["produto"]
        )

        print(
            f"Região inicial: "
            f"{evento['regiaoAntes']}"
        )

        print(
            f"Região final: "
            f"{evento['regiaoDepois']}"
        )


    elif evento["tipo"] == "Substituição":

        print(
            "Produto retirado:"
        )

        mostrarProduto(
            evento["antes"]
        )

        print(
            "\nProduto adicionado:"
        )

        mostrarProduto(
            evento["depois"]
        )


print(
    f"\nTempo total da IA: "
    f"{tempoTotalIA:.2f} segundos"
)


print(
    "\nPressione qualquer tecla "
    "nas imagens para finalizar."
)


cv2.waitKey(0)

cv2.destroyAllWindows()