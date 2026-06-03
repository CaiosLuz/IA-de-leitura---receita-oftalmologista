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

    allow_headers=["*"]

)

# ==================================
# ROOT
# ==================================

@app.api_route(
    "/",
    methods=["GET","HEAD"]
)
def root():

    return {

        "status":"online"

    }


# ==================================
# CONFIG TESSERACT
# ==================================

tesseract_bin = shutil.which(
    "tesseract"
)

if tesseract_bin:

    pytesseract.pytesseract.tesseract_cmd = \
        tesseract_bin

else:

    pytesseract.pytesseract.tesseract_cmd = \
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# ==================================
# OCR
# ==================================

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

    texto = pytesseract.image_to_string(

        gray,

        config=
            r'--oem 3 --psm 6 -l por'

    )

    return texto


# ==================================
# NORMALIZA TEXTO OCR
# ==================================

def normalizar(texto):

    texto = texto.upper()

    texto = texto.replace(
        ",",
        "."
    )

    texto = texto.replace(
        "(",
        "-"
    )

    texto = texto.replace(
        "[",
        "-"
    )

    texto = texto.replace(
        "=",
        "-"
    )

    texto = texto.replace(
        "|",
        " "
    )

    texto = texto.replace(
        "O D",
        "OD"
    )

    texto = texto.replace(
        "O E",
        "OE"
    )

    return texto


# ==================================
# CONVERTER NUMERO
# ==================================

def converter_numero(v):

    v=v.strip()

    try:

        return float(v)

    except:

        pass

    apenas = re.sub(

        r"[^0-9]",

        "",

        v

    )

    if len(apenas)==4:

        return -(

            int(apenas)

            /100

        )

    if len(apenas)==3:

        return float(
            apenas
        )

    return None


# ==================================
# PARSER RECEITA COMPLEXA
# ==================================

def parser_complexo(texto):

    dados={}

    od = re.search(

        r"OD.*?(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s+(\d{1,3})",

        texto,

        re.S

    )

    oe = re.search(

        r"OE.*?(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s+(\d{1,3})",

        texto,

        re.S

    )

    if od:

        dados["OD"]={

            "esferico":

            converter_numero(
                od.group(1)
            ),

            "cilindrico":

            converter_numero(
                od.group(2)
            ),

            "eixo":

            int(
                od.group(3)
            )

        }

    if oe:

        dados["OE"]={

            "esferico":

            converter_numero(
                oe.group(1)
            ),

            "cilindrico":

            converter_numero(
                oe.group(2)
            ),

            "eixo":

            int(
                oe.group(3)
            )

        }

    return dados


# ==================================
# PARSER RECEITA SIMPLES
# ==================================

def parser_simples(texto):

    dados={}

    od = re.search(

        r"OLHO DIREITO.*?(-?\d+\.\d+).*?(-?\d+\.\d+).*?(\d{1,3})",

        texto,

        re.S

    )

    oe = re.search(

        r"OLHO ESQUERDO.*?(-?\d+\.\d+).*?(-?\d+\.\d+).*?(\d{1,3})",

        texto,

        re.S

    )

    if od:

        dados["OD"]={

            "esferico":
            float(
                od.group(1)
            ),

            "cilindrico":
            float(
                od.group(2)
            ),

            "eixo":
            int(
                od.group(3)
            )

        }

    if oe:

        dados["OE"]={

            "esferico":
            float(
                oe.group(1)
            ),

            "cilindrico":
            float(
                oe.group(2)
            ),

            "eixo":
            int(
                oe.group(3)
            )

        }

    return dados


# ==================================
# ENDPOINT
# ==================================

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

        texto = normalizar(
            texto
        )

        print(
            "\n===== OCR ====="
        )

        print(
            texto
        )

        dados = parser_complexo(
            texto
        )

        if (

            "OD" not in dados

            or

            "OE" not in dados

        ):

            dados = parser_simples(
                texto
            )

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