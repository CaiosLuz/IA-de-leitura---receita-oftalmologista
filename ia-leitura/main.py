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

# ====================================
# CONFIG TESSERACT
# ====================================

tesseract_bin = shutil.which(
    "tesseract"
)

if tesseract_bin:

    pytesseract.pytesseract.tesseract_cmd = \
        tesseract_bin

else:

    pytesseract.pytesseract.tesseract_cmd = \
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# ====================================
# OCR
# ====================================

def executar_ocr(img):

    gray = cv2.cvtColor(
        img,
        cv2.COLOR_BGR2GRAY
    )

    gray = cv2.resize(

        gray,

        None,

        fx=3,

        fy=3,

        interpolation=
        cv2.INTER_CUBIC

    )

    gray = cv2.GaussianBlur(

        gray,

        (3,3),

        0

    )

    gray = cv2.adaptiveThreshold(

        gray,

        255,

        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,

        cv2.THRESH_BINARY,

        31,

        10

    )

    texto = pytesseract.image_to_string(

        gray,

        config=
        r'--oem 3 --psm 11 -l por'

    )

    return texto


# ====================================
# NORMALIZA NUMEROS
# ====================================

def converter_numero(valor):

    valor = valor.replace(
        "(",
        "-"
    )

    valor = valor.replace(
        "[",
        "-"
    )

    valor = valor.replace(
        "=",
        "-"
    )

    valor = valor.replace(
        "/",
        "7"
    )

    if "." not in valor:

        limpo = valor.replace(
            "-",
            ""
        )

        if len(limpo)==4:

            valor = "-" + \
                    limpo[0] + \
                    "." + \
                    limpo[1:]

    try:

        return float(
            valor
        )

    except:

        return None


# ====================================
# EXTRAI DADOS
# ====================================

def extrair_bloco(texto):

    nums = re.findall(

        r"[-=\[\(]?\d+\.\d+|[-=\[\(]?\d+",

        texto

    )

    floats=[]
    ints=[]

    for n in nums:

        valor = converter_numero(
            n
        )

        if valor is None:

            continue

        if abs(valor) < 40:

            floats.append(
                valor
            )

        elif 0 <= valor <= 180:

            ints.append(
                int(valor)
            )

    if (

        len(floats)>=2

        and

        len(ints)>=1

    ):

        return {

            "esferico":
            floats[0],

            "cilindrico":
            floats[1],

            "eixo":
            ints[0]

        }

    return None


# ====================================
# ROOT
# ====================================

@app.get("/")

def root():

    return {

        "status":
        "online"

    }


# ====================================
# ENDPOINT
# ====================================

@app.post("/analisar")

async def analisar(

        file: UploadFile = File(...)

):

    try:

        image_bytes = \
            await file.read()

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
                "imagem invalida"

            }

        texto = executar_ocr(
            img
        )

        texto = texto.upper()

        texto = texto.replace(
            ",",
            "."
        )

        print(texto)

        linhas=[

            l.strip()

            for l in
            texto.splitlines()

            if l.strip()

        ]

        dados={}

        # =====================
        # MODELO COMPLEXO
        # =====================

        for i,linha in enumerate(
                linhas
        ):

            if "OD" in linha:

                bloco=" ".join(

                    linhas[
                    i:i+10
                    ]

                )

                r = extrair_bloco(
                    bloco
                )

                if r:

                    dados["OD"]=r


            if "OE" in linha:

                bloco=" ".join(

                    linhas[
                    i:i+10
                    ]

                )

                r = extrair_bloco(
                    bloco
                )

                if r:

                    dados["OE"]=r


        # =====================
        # MODELO SIMPLES
        # =====================

        if "OD" not in dados:

            numeros = re.findall(

                r"[-=]?\d+\.\d+|\d{1,3}",

                texto

            )

            convertidos=[]

            for n in numeros:

                valor = converter_numero(
                    n
                )

                if valor is not None:

                    convertidos.append(
                        valor
                    )

            if len(convertidos)>=6:

                dados["OD"]={

                    "esferico":
                    convertidos[0],

                    "cilindrico":
                    convertidos[1],

                    "eixo":
                    int(
                        convertidos[2]
                    )

                }

                dados["OE"]={

                    "esferico":
                    convertidos[3],

                    "cilindrico":
                    convertidos[4],

                    "eixo":
                    int(
                        convertidos[5]
                    )

                }

        print(
            "RESULTADO",
            dados
        )

        if (

            "OD" not in dados

            or

            "OE" not in dados

        ):

            return {

                "erro":
                "nao interpretado"

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