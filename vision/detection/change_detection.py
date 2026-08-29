import cv2


def comparar_imagens(caminho_antes, caminho_depois):
    antes = cv2.imread(caminho_antes)
    depois = cv2.imread(caminho_depois)

    if antes is None or depois is None:
        print("Erro ao carregar uma das imagens.")
        return

    # Garante que as duas imagens tenham o mesmo tamanho
    depois = cv2.resize(
        depois,
        (antes.shape[1], antes.shape[0])
    )

    # Converte as imagens para escala de cinza
    antes_cinza = cv2.cvtColor(antes, cv2.COLOR_BGR2GRAY)
    depois_cinza = cv2.cvtColor(depois, cv2.COLOR_BGR2GRAY)

    # Suaviza pequenos ruídos da imagem
    antes_cinza = cv2.GaussianBlur(antes_cinza, (5, 5), 0)
    depois_cinza = cv2.GaussianBlur(depois_cinza, (5, 5), 0)

    # Calcula a diferença entre as duas imagens
    diferenca = cv2.absdiff(antes_cinza, depois_cinza)

    # Transforma as diferenças relevantes em regiões brancas
    _, mascara = cv2.threshold(
        diferenca,
        30,
        255,
        cv2.THRESH_BINARY
    )

    # Junta pequenas regiões próximas
    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (5, 5)
    )

    mascara = cv2.dilate(
        mascara,
        kernel,
        iterations=2
    )

    # Calcula percentual total de mudança
    pixels_alterados = cv2.countNonZero(mascara)
    pixels_totais = mascara.shape[0] * mascara.shape[1]

    percentual = (pixels_alterados / pixels_totais) * 100

    print(f"Alteração total da imagem: {percentual:.2f}%")

    # Procura regiões diferentes
    contornos, _ = cv2.findContours(
        mascara,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    imagem_resultado = depois.copy()

    regioes_detectadas = 0

    for contorno in contornos:
        area = cv2.contourArea(contorno)

        # Ignora alterações muito pequenas
        if area < 1000:
            continue

        x, y, largura, altura = cv2.boundingRect(contorno)

        cv2.rectangle(
            imagem_resultado,
            (x, y),
            (x + largura, y + altura),
            (0, 255, 0),
            2
        )

        regioes_detectadas += 1

        print(
            f"Região {regioes_detectadas}: "
            f"x={x}, y={y}, "
            f"largura={largura}, altura={altura}, "
            f"área={area:.0f}"
        )

    if regioes_detectadas > 0:
        print(
            f"\n{regioes_detectadas} região(ões) "
            "com mudança significativa detectada(s)."
        )
    else:
        print("\nNenhuma região significativa detectada.")

    cv2.imshow("Antes", antes)
    cv2.imshow("Depois", depois)
    cv2.imshow("Mascara de diferenca", mascara)
    cv2.imshow("Regioes alteradas", imagem_resultado)

    print("\nPressione Q em uma das janelas para sair.")

    while True:
        tecla = cv2.waitKey(0) & 0xFF

        if tecla == ord("q"):
            break

    cv2.destroyAllWindows()


comparar_imagens(
    "vision/images/antes.jpg",
    "vision/images/depois.jpg"
)