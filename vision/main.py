import cv2
import time
import os
import numpy as np

from detection.movement_detection import (
    detectar_movimentacoes
)


CAMERA_INDEX = 0
PASTA_IMAGENS = "vision/images"

CAMINHO_REFERENCIA = os.path.join(
    PASTA_IMAGENS,
    "referencia.jpg"
)

CAMINHO_ATUAL = os.path.join(
    PASTA_IMAGENS,
    "atual.jpg"
)


def detectar_mudancas(imagem_antes, imagem_depois):
    antes_cinza = cv2.cvtColor(
        imagem_antes,
        cv2.COLOR_BGR2GRAY
    )

    depois_cinza = cv2.cvtColor(
        imagem_depois,
        cv2.COLOR_BGR2GRAY
    )

    antes_cinza = cv2.GaussianBlur(
        antes_cinza,
        (5, 5),
        0
    )

    depois_cinza = cv2.GaussianBlur(
        depois_cinza,
        (5, 5),
        0
    )

    diferenca = cv2.absdiff(
        antes_cinza,
        depois_cinza
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

    # Remove pequenos ruídos
    mascara = cv2.morphologyEx(
        mascara,
        cv2.MORPH_OPEN,
        kernel,
        iterations=2
    )

    # Junta regiões próximas
    mascara = cv2.morphologyEx(
        mascara,
        cv2.MORPH_CLOSE,
        kernel,
        iterations=2
    )

    contornos, _ = cv2.findContours(
        mascara,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    resultado = imagem_depois.copy()

    regioes = []
    regioes_detectadas = 0

    altura_imagem, largura_imagem = imagem_depois.shape[:2]

    area_imagem = (
        altura_imagem
        * largura_imagem
    )

    area_minima = 1000

    # Regiões maiores que 20% da imagem
    # são consideradas suspeitas
    area_maxima = area_imagem * 0.20

    for contorno in contornos:
        area = cv2.contourArea(
            contorno
        )

        if area < area_minima:
            continue

        if area > area_maxima:
            print(
                f"Região ignorada: área muito grande "
                f"({area:.0f} pixels). "
                "Possível alteração de iluminação."
            )
            continue

        x, y, largura, altura = cv2.boundingRect(
            contorno
        )

        regioes.append(
            {
                "x": x,
                "y": y,
                "largura": largura,
                "altura": altura,
                "area": area
            }
        )

        cv2.rectangle(
            resultado,
            (x, y),
            (
                x + largura,
                y + altura
            ),
            (0, 255, 0),
            2
        )

        regioes_detectadas += 1

        print(
            f"Região {regioes_detectadas}: "
            f"x={x}, "
            f"y={y}, "
            f"largura={largura}, "
            f"altura={altura}, "
            f"área={area:.0f}"
        )

    pixels_alterados = cv2.countNonZero(
        mascara
    )

    pixels_totais = (
        mascara.shape[0]
        * mascara.shape[1]
    )

    percentual = (
        pixels_alterados
        / pixels_totais
    ) * 100

    print(
        f"Alteração total: "
        f"{percentual:.2f}%"
    )

    return (
        mascara,
        resultado,
        regioes
    )


def capturar_frame_estavel(
    camera,
    quantidade=5
):
    frames = []

    for _ in range(quantidade):
        ret, frame = camera.read()

        if not ret:
            continue

        frames.append(
            frame.astype(
                np.float32
            )
        )

        time.sleep(0.05)

    if not frames:
        print(
            "Erro ao capturar frames."
        )

        return None

    media = np.mean(
        frames,
        axis=0
    )

    return media.astype(
        np.uint8
    )


def main():
    os.makedirs(
        PASTA_IMAGENS,
        exist_ok=True
    )

    camera = cv2.VideoCapture(
        CAMERA_INDEX
    )

    if not camera.isOpened():
        print(
            "Erro: não foi possível "
            "abrir a câmera."
        )

        return

    print(
        "Câmera iniciada."
    )

    print()

    print(
        "Capturando estado inicial..."
    )

    # Dá tempo para a câmera estabilizar
    time.sleep(2)

    referencia = capturar_frame_estavel(
        camera
    )

    if referencia is None:
        camera.release()
        return

    cv2.imwrite(
        CAMINHO_REFERENCIA,
        referencia
    )

    print(
        "Estado inicial salvo."
    )

    print()

    print(
        "O = porta abriu"
    )

    print(
        "F = porta fechou"
    )

    print(
        "Q = sair"
    )

    print()

    porta_aberta = False

    while True:
        ret, frame = camera.read()

        if not ret:
            print(
                "Erro ao capturar imagem."
            )

            break

        cv2.imshow(
            "Smart Fridge - Camera",
            frame
        )

        tecla = cv2.waitKey(1) & 0xFF

        if tecla == ord("o"):
            if porta_aberta:
                print(
                    "A porta já está aberta."
                )

                continue

            porta_aberta = True

            print()

            print(
                "Porta ABERTA."
            )

            print(
                "Faça a alteração na cena."
            )

        elif tecla == ord("f"):
            if not porta_aberta:
                print(
                    "A porta já está fechada."
                )

                continue

            porta_aberta = False

            print()

            print(
                "Porta FECHADA."
            )

            print(
                "Aguardando estabilização..."
            )

            time.sleep(2)

            imagem_atual = capturar_frame_estavel(
                camera
            )

            if imagem_atual is None:
                continue

            cv2.imwrite(
                CAMINHO_ATUAL,
                imagem_atual
            )

            print(
                "Nova imagem capturada."
            )

            print()

            print(
                "Comparando com estado anterior..."
            )

            (
                mascara,
                resultado,
                regioes
            ) = detectar_mudancas(
                referencia,
                imagem_atual
            )

            if len(regioes) > 0:
                print(
                    f"{len(regioes)} região(ões) "
                    "alterada(s) detectada(s)."
                )

            else:
                print(
                    "Nenhuma mudança "
                    "significativa detectada."
                )

            # Tenta associar regiões antigas
            # e novas como movimentação
            if len(regioes) >= 2:
                print()

                print(
                    "Analisando movimentações..."
                )

                (
                    movimentacoes,
                ) = detectar_movimentacoes(
                    referencia,
                    imagem_atual,
                    regioes
                )

                if movimentacoes:
                    for numero, movimento in enumerate(
                        movimentacoes,
                        start=1
                    ):
                        origem = movimento[
                            "origem"
                        ]

                        destino = movimento[
                            "destino"
                        ]

                        similaridade = movimento[
                            "similaridade"
                        ]

                        print()

                        print(
                            f"Movimentação {numero} detectada:"
                        )

                        print(
                            f"  Região de origem: "
                            f"{origem + 1}"
                        )

                        print(
                            f"  Região de destino: "
                            f"{destino + 1}"
                        )

                        print(
                            f"  Similaridade: "
                            f"{similaridade:.2f}"
                        )

                else:
                    print(
                        "Nenhuma movimentação "
                        "confirmada."
                    )

            cv2.imshow(
                "Mascara de diferenca",
                mascara
            )

            cv2.imshow(
                "Regioes alteradas",
                resultado
            )

            # A imagem atual se torna
            # a referência do próximo ciclo
            referencia = imagem_atual.copy()

            cv2.imwrite(
                CAMINHO_REFERENCIA,
                referencia
            )

            print()

            print(
                "Novo estado salvo como referência."
            )

            print(
                "Pronto para o próximo ciclo."
            )

        elif tecla == ord("q"):
            break

    camera.release()

    cv2.destroyAllWindows()

    print()

    print(
        "Programa encerrado."
    )


if __name__ == "__main__":
    main()