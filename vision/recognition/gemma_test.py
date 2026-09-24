import cv2
import subprocess
import tempfile
import time
import os

ARQUIVO_MODELO = "gemma-3n-E2B-it-int4.litertlm"


HF_TOKEN = os.environ.get("HF_TOKEN")

MODELO_REPO = "google/gemma-3n-E2B-it-litert-lm"


PROMPT = """
Analise a imagem e identifique separadamente todos os produtos visíveis.

Para identificar cada produto, considere o conjunto completo de informações da imagem:
- texto visível no rótulo;
- aparência da embalagem;
- cor e aparência do conteúdo;
- imagens, frutas, símbolos ou elementos gráficos do rótulo;
- formato do recipiente;
- contexto visual geral do produto.

Não dependa apenas da leitura do texto.
Combine as informações visuais e textuais para chegar à identificação mais provável.

O campo Produto deve representar o alimento completo identificado,
incluindo tipo e sabor quando puderem ser determinados com segurança.

Exemplos de raciocínio:
- embalagem de suco + líquido alaranjado + referência visual/textual a laranja
  → Suco de Laranja;
- embalagem de leite + indicação integral
  → Leite Integral.

Não invente detalhes que não tenham suporte na imagem.
Se houver conflito entre o texto e os elementos visuais, considere o conjunto
das evidências e reduza a confiança quando necessário.

Não inclua volume, porcentagem ou frases promocionais no nome do produto.

Responda exatamente assim:

Quantidade de produtos: ...

Produto 1:
Produto: ...
Marca: ...
Categoria: ...
Confiança: alta, media ou baixa

Produto 2:
Produto: ...
Marca: ...
Categoria: ...
Confiança: alta, media ou baixa

Continue a numeração quando necessário.
"""


def reconhecer_produto(frame):

    with tempfile.NamedTemporaryFile(
        suffix=".jpg",
        delete=False
    ) as arquivo:

        caminho_imagem = arquivo.name

    cv2.imwrite(
        caminho_imagem,
        frame
    )

    comando = [
        "litert-lm",
        "run",
        "--from-huggingface-repo",
        MODELO_REPO,
        ARQUIVO_MODELO,
        "--vision-backend",
        "gpu",
        "--attachment",
        caminho_imagem,
        "--prompt",
        PROMPT,
    ]

    if HF_TOKEN:
        comando.extend([
            "--huggingface-token",
            HF_TOKEN
        ])

    inicio = time.perf_counter()

    try:

        processo = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            timeout=300,
        )

        tempo = (
            time.perf_counter()
            - inicio
        )

        if processo.returncode != 0:

            resultado = (
                "ERRO:\n"
                + processo.stderr
            )

        else:

            resultado = (
                processo.stdout.strip()
            )

    except subprocess.TimeoutExpired:

        tempo = (
            time.perf_counter()
            - inicio
        )

        resultado = (
            "Tempo limite excedido."
        )

    finally:

        if os.path.exists(
            caminho_imagem
        ):
            os.remove(
                caminho_imagem
            )

    return resultado, tempo


camera = cv2.VideoCapture(0)

if not camera.isOpened():

    print(
        "Erro ao abrir a camera."
    )

    exit()


ultimo_tempo = 0


print()
print("Gemma 3n + LiteRT-LM")
print()
print("E = analisar produto")
print("Q = sair")
print()


while True:

    ret, frame = camera.read()

    if not ret:
        break

    cv2.putText(
        frame,
        "E = analisar | Q = sair",
        (20, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
    )

    if ultimo_tempo > 0:

        cv2.putText(
            frame,
            f"Ultima analise: {ultimo_tempo:.1f}s",
            (20, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )

    cv2.imshow(
        "Gemma LiteRT Camera",
        frame
    )

    tecla = (
        cv2.waitKey(1)
        & 0xFF
    )

    if tecla == ord("e"):

        frame_capturado = (
            frame.copy()
        )

        print()
        print(
            "Imagem capturada."
        )

        print(
            "Gemma analisando..."
        )

        resultado, tempo = (
            reconhecer_produto(
                frame_capturado
            )
        )

        ultimo_tempo = tempo

        print()
        print("Resultado:")
        print(resultado)

        print()
        print(
            f"Tempo total: "
            f"{tempo:.2f} segundos"
        )

        print(
            "-------------------------"
        )

    elif tecla == ord("q"):
        break


camera.release()

cv2.destroyAllWindows()