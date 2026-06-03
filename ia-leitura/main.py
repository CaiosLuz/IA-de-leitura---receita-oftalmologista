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

# -----------------------------
# CONFIG TESSERACT
# -----------------------------

tesseract_bin = shutil.which("tesseract")

if tesseract_bin:

    pytesseract.pytesseract.tesseract_cmd = tesseract_bin

else:

    pytesseract.pytesseract.tesseract_cmd = \
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    os.environ["TESSDATA_PREFIX"] = \
        r"C:\Program Files\Tesseract-OCR\tessdata"


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

        # -----------------------------
        # REDUZ IMAGENS GIGANTES
        # -----------------------------

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

                ),

                interpolation=
                    cv2.INTER_AREA

            )

        # -----------------------------
        # PRE PROCESSAMENTO
        # -----------------------------

        gray = cv2.cvtColor(

            img,

            cv2.COLOR_BGR2GRAY

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
            r'--oem 3 --psm 11 -l por'

        texto = pytesseract.image_to_string(

            gray,

            config=custom_config

        )

        texto = texto.replace(",", ".")
        texto = texto.replace("--", "-")
        texto = texto.replace("- ", "-")
        texto = texto.replace("’", "'")

        texto = re.sub(

            r'(?<=\d)/(?=\d)',

            '.',

            texto

        )

        texto_upper = texto.upper()

        print(
            "\n========== OCR =========="
        )

        print(texto)

        dados = {}

        # -----------------------------
        # PROCURA OD / OE
        # -----------------------------

        linhas = [

            l.strip()

            for l in texto_upper.splitlines()

            if l.strip()

        ]

        for i, linha in enumerate(linhas):

            if linha in ["OD", "OE"]:

                olho = linha

                candidatos = []

                for prox in linhas[
                    i+1:i+20
                ]:

                    encontrados = re.findall(

                        r"-?\d+\.\d+|-?\d+",

                        prox

                    )

                    candidatos.extend(
                        encontrados
                    )

                decimais = []

                inteiros = []

                for n in candidatos:

                    if "." in n:

                        try:

                            decimais.append(
                                float(n)
                            )

                        except:

                            pass

                    else:

                        try:

                            inteiro = int(n)

                            if 0 <= inteiro <= 180:

                                inteiros.append(
                                    inteiro
                                )

                        except:

                            pass

                if (

                    len(decimais) >= 2

                    and

                    len(inteiros) >= 1

                ):

                    dados[olho] = {

                        "esferico":

                            decimais[0],

                        "cilindrico":

                            decimais[1],

                        "eixo":

                            inteiros[0]

                    }

        print(
            "Resultado:",
            dados
        )

        # -----------------------------
        # SE NÃO ENCONTROU
        # -----------------------------

        if len(dados) == 0:

            return {

                "erro":

                    "Não foi possível interpretar a receita"

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

    port = int(

        os.environ.get(
            "PORT",
            8000
        )

    )

    uvicorn.run(

        app,

        host="0.0.0.0",

        port=port

    )