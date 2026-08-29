import cv2

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("Erro: não foi possível abrir a câmera.")
    exit()

print("A = capturar ANTES")
print("D = capturar DEPOIS")
print("Q = sair")

while True:
    ret, frame = camera.read()

    if not ret:
        print("Erro ao capturar imagem.")
        break

    cv2.imshow("Smart Fridge - Camera", frame)

    tecla = cv2.waitKey(1) & 0xFF

    if tecla == ord("a"):
        cv2.imwrite("vision/images/antes.jpg", frame)
        print("Imagem ANTES capturada!")

    elif tecla == ord("d"):
        cv2.imwrite("vision/images/depois.jpg", frame)
        print("Imagem DEPOIS capturada!")

    elif tecla == ord("q"):
        break       

camera.release()
cv2.destroyAllWindows()