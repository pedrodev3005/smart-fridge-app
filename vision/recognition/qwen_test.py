import cv2

from transformers import (
    Qwen2_5_VLForConditionalGeneration,
    AutoProcessor,
)

from qwen_vl_utils import process_vision_info


MODELO = "Qwen/Qwen2.5-VL-3B-Instruct"
CAMERA_INDEX = 0

CAMINHO_FRAME = "vision/images/qwen_frame.jpg"


print("Carregando Qwen2.5-VL...")

modelo = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    MODELO,
    torch_dtype="auto",
    device_map="auto",
)

processor = AutoProcessor.from_pretrained(
    MODELO
)


def reconhecer_imagem(caminho_imagem):

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "image": caminho_imagem,
                },
                {
                    "type": "text",
                    "text": (
                        "Analise cuidadosamente o principal produto ou alimento da imagem. "
                        "Leia todo o texto visível no rótulo antes de responder. "

                        "Diferencie claramente MARCA de PRODUTO. "
                        "Produto é o tipo do alimento ou bebida, por exemplo: "
                        "'suco de uva', 'leite integral', 'iogurte de morango'. "
                        "Marca é o fabricante ou nome comercial, por exemplo: "
                        "'Quinta do Morgado', 'Nestlé', 'Piracanjuba'. "

                        "Não use o nome da marca como nome do produto. "
                        "Se houver texto como 'SUCO DE UVA', use isso para identificar o produto. "

                        "Para categoria, escolha apenas entre: "
                        "Bebidas, Laticínios, Carnes, Frutas, Verduras e legumes, "
                        "Frios, Doces e sobremesas, Molhos e condimentos, "
                        "Alimentos preparados, Outros. "

                        "Se não tiver certeza sobre alguma informação, escreva 'incerto'. "

                        "Responda exatamente neste formato:\n"
                        "Produto: ...\n"
                        "Marca: ...\n"
                        "Categoria: ...\n"
                        "Texto visível no rótulo: ...\n"
                        "Confiança: alta, média ou baixa"
                    )
                },
            ],
        }
    ]

    texto = processor.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    image_inputs, video_inputs = process_vision_info(
        messages
    )

    inputs = processor(
        text=[texto],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    )

    inputs = inputs.to(
        modelo.device
    )

    generated_ids = modelo.generate(
        **inputs,
        max_new_tokens=64,
    )

    generated_ids_trimmed = [
        output_ids[len(input_ids):]
        for input_ids, output_ids
        in zip(
            inputs.input_ids,
            generated_ids,
        )
    ]

    resultado = processor.batch_decode(
        generated_ids_trimmed,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
    )

    return resultado[0]


def main():

    camera = cv2.VideoCapture(
        CAMERA_INDEX
    )

    if not camera.isOpened():
        print(
            "Erro: não foi possível "
            "abrir a câmera."
        )
        return

    print()
    print("Câmera iniciada.")
    print()
    print("E = reconhecer imagem atual")
    print("Q = sair")
    print()

    ultimo_resultado = (
        "Pressione E para reconhecer"
    )

    while True:

        sucesso, frame = camera.read()

        if not sucesso:
            print(
                "Erro ao capturar frame."
            )
            break

        frame_exibicao = frame.copy()

        cv2.putText(
            frame_exibicao,
            ultimo_resultado[:70],
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )

        cv2.imshow(
            "Qwen Vision - Webcam",
            frame_exibicao
        )

        tecla = cv2.waitKey(1) & 0xFF

        if tecla == ord("e"):

            print()
            print("Capturando imagem...")

            cv2.imwrite(
                CAMINHO_FRAME,
                frame
            )

            print(
                "Qwen analisando..."
            )

            try:

                resultado = reconhecer_imagem(
                    CAMINHO_FRAME
                )

                ultimo_resultado = resultado

                print()
                print("Resultado:")
                print(resultado)
                print()

            except Exception as erro:

                print()
                print(
                    "Erro durante "
                    "o reconhecimento:"
                )

                print(erro)

                ultimo_resultado = (
                    "Erro no reconhecimento"
                )

        elif tecla == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()