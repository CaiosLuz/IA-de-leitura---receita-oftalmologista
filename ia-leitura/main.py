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

# --------------------------------
# CONFIG TESSERACT
# --------------------------------

tesseract_bin = shutil.which("tesseract")

if tesseract_bin:

    pytesseract.pytesseract.tesseract_cmd = tesseract_bin

else:

    pytesseract.pytesseract.tesseract_cmd = \
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    os.environ["TESSDATA_PREFIX"] = \
        r"C:\Program Files\Tesseract-OCR\tessdata"


# --------------------------------
# EXTRAÇÃO AUXILIAR
# --------------------------------

def extrair_bloco(bloco):

    nums = re.findall(
        r"-?\d+\.\d+|-?\d+",
        bloco
    )

    floats = []
    ints = []

    for n in nums:

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


# --------------------------------
# ENDPOINT
# --------------------------------

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
                "erro":"Imagem inválida"
            }

        # --------------------------
        # resize
        # --------------------------

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

        # --------------------------
        # preprocessamento
        # --------------------------

        gray = cv2.cvtColor(
            img,
            cv2.COLOR_BGR2GRAY
        )

        gray = cv2.GaussianBlur(
            gray,
            (3,3),
            0
        )

        gray = cv2.resize(

            gray,

            None,

            fx=2,

            fy=2,

            interpolation=
            cv2.INTER_CUBIC

        )

        gray = cv2.threshold(

            gray,

            0,

            255,

            cv2.THRESH_BINARY
            |
            cv2.THRESH_OTSU

        )[1]

        custom_config = \
            r'--oem 3 --psm 4 -l por'

        texto = pytesseract.image_to_string(

            gray,

            config=
            custom_config

        )

        texto_upper = \
            texto.upper().replace(",", ".")

        print("\n========== OCR ==========")

        print(texto_upper)

        dados = {}

        linhas = [

            l.strip()

            for l in texto_upper.splitlines()

            if l.strip()

        ]

        # ===================================
        # MODELO LONGE / OD / OE
        # ===================================

        for i, linha in enumerate(linhas):

            if "OD" in linha:

                bloco = " ".join(
                    linhas[i:i+3]
                )

                resultado = extrair_bloco(
                    bloco
                )

                if resultado:

                    dados["OD"] = resultado


            if "OE" in linha:

                bloco = " ".join(
                    linhas[i:i+3]
                )

                resultado = extrair_bloco(
                    bloco
                )

                if resultado:

                    dados["OE"] = resultado


        # ===================================
        # MODELO OLHO DIREITO
        # ===================================

        if (

            "OLHO DIREITO"
            in texto_upper

            and

            "OLHO ESQUERDO"
            in texto_upper

        ):

            od_match = re.search(

                r"OLHO DIREITO(.*?)"
                r"(-?\d+\.\d+)\s+"
                r"(-?\d+\.\d+)\s+"
                r"(\d{1,3})",

                texto_upper,

                re.S

            )

            oe_match = re.search(

                r"OLHO ESQUERDO(.*?)"
                r"(-?\d+\.\d+)\s+"
                r"(-?\d+\.\d+)\s+"
                r"(\d{1,3})",

                texto_upper,

                re.S

            )

            if od_match:

                dados["OD"] = {

                    "esferico":
                    float(
                        od_match.group(2)
                    ),

                    "cilindrico":
                    float(
                        od_match.group(3)
                    ),

                    "eixo":
                    int(
                        od_match.group(4)
                    )

                }


            if oe_match:

                dados["OE"] = {

                    "esferico":
                    float(
                        oe_match.group(2)
                    ),

                    "cilindrico":
                    float(
                        oe_match.group(3)
                    ),

                    "eixo":
                    int(
                        oe_match.group(4)
                    )

                }


        print(
            "Resultado:",
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

            "erro":str(e)

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