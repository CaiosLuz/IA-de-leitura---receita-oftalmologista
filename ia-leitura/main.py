from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

import pytesseract
import cv2
import numpy as np
import re
import shutil
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================
# CONFIG TESSERACT
# =====================================

tesseract_bin = shutil.which("tesseract")

if tesseract_bin:

    pytesseract.pytesseract.tesseract_cmd = tesseract_bin

else:

    pytesseract.pytesseract.tesseract_cmd = \
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    os.environ["TESSDATA_PREFIX"] = \
        r"C:\Program Files\Tesseract-OCR\tessdata"


# =====================================
# AUXILIAR EXTRAÇÃO
# =====================================

def extrair_bloco(texto):

    numeros = re.findall(
        r"-?\d+\.\d+|-?\d+",
        texto
    )

    floats = []
    ints = []

    for n in numeros:

        try:

            if "." in n:

                valor = float(n)

                if abs(valor) < 40:

                    floats.append(valor)

            else:

                valor = int(n)

                if 0 <= valor <= 180:

                    ints.append(valor)

        except:
            pass

    if len(floats) >= 2 and len(ints) >= 1:

        return {

            "esferico": floats[0],

            "cilindrico": floats[1],

            "eixo": ints[0]

        }

    return None


# =====================================
# OCR
# =====================================

def executar_ocr(img):

    gray = cv2.cvtColor(
        img,
        cv2.COLOR_BGR2GRAY
    )

    gray = cv2.resize(

        gray,

        None,

        fx=2,

        fy=2,

        interpolation=
        cv2.INTER_CUBIC

    )

    gray = cv2.GaussianBlur(

        gray,

        (3,3),

        0

    )

    gray = cv2.equalizeHist(
        gray
    )

    gray = cv2.adaptiveThreshold(

        gray,

        255,

        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,

        cv2.THRESH_BINARY,

        31,

        10

    )

    config = \
        r'--oem 3 --psm 6 -l por'

    texto = pytesseract.image_to_string(

        gray,

        config=config

    )

    return texto


# =====================================
# ENDPOINT
# =====================================

@app.post("/analisar")
async def analisar_receita(
        file: UploadFile = File(...)
):

    try:

        image_bytes = await file.read()

        npimg = np.frombuffer(
            image_bytes,
            np.uint8
        )

        img = cv2.imdecode(
            npimg,
            cv2.IMREAD_COLOR
        )

        if img is None:

            return {

                "erro":
                "Imagem inválida"

            }

        altura, largura = img.shape[:2]

        if largura > 1000:

            escala = 1000 / largura

            img = cv2.resize(

                img,

                (

                    1000,

                    int(
                        altura *
                        escala
                    )

                )

            )

        texto = executar_ocr(
            img
        )

        texto_upper = \
            texto.upper().replace(
                ",",
                "."
            )

        print("\n========== OCR ==========")

        print(
            texto_upper
        )

        linhas = [

            l.strip()

            for l in
            texto_upper.splitlines()

            if l.strip()

        ]

        dados = {}

        # =====================================
        # MODELO LONGE / OD / OE
        # =====================================

        for i, linha in enumerate(
                linhas
        ):

            if "OD" in linha:

                bloco = " ".join(

                    linhas[
                    i:i+4
                    ]

                )

                resultado = \
                    extrair_bloco(
                        bloco
                    )

                if resultado:

                    dados[
                        "OD"
                    ] = resultado


            if "OE" in linha:

                bloco = " ".join(

                    linhas[
                    i:i+4
                    ]

                )

                resultado = \
                    extrair_bloco(
                        bloco
                    )

                if resultado:

                    dados[
                        "OE"
                    ] = resultado


        # =====================================
        # MODELO OLHO DIREITO / ESQUERDO
        # =====================================

        if (

            "OLHO DIREITO"
            in texto_upper

            and

            "OLHO ESQUERDO"
            in texto_upper

        ):

            od = re.search(

                r"OLHO DIREITO(.*?)"
                r"(-?\d+\.\d+)\s+"
                r"(-?\d+\.\d+)\s+"
                r"(\d{1,3})",

                texto_upper,

                re.S

            )

            oe = re.search(

                r"OLHO ESQUERDO(.*?)"
                r"(-?\d+\.\d+)\s+"
                r"(-?\d+\.\d+)\s+"
                r"(\d{1,3})",

                texto_upper,

                re.S

            )

            if od:

                dados["OD"] = {

                    "esferico":
                    float(
                        od.group(2)
                    ),

                    "cilindrico":
                    float(
                        od.group(3)
                    ),

                    "eixo":
                    int(
                        od.group(4)
                    )

                }

            if oe:

                dados["OE"] = {

                    "esferico":
                    float(
                        oe.group(2)
                    ),

                    "cilindrico":
                    float(
                        oe.group(3)
                    ),

                    "eixo":
                    int(
                        oe.group(4)
                    )

                }

        print(
            "\nResultado:",
            dados
        )

        if (

            "OD" not in dados

            or

            "OE" not in dados

        ):

            return {

                "erro":
                "Não foi possível interpretar"

            }

        return dados

    except Exception as e:

        print(e)

        return {

            "erro":
            str(e)

        }


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(

        app,

        host="0.0.0.0",

        port=int(

            os.environ.get(

                "PORT",

                8000

            )

        )

    )