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

tesseract_bin = shutil.which("tesseract")

if tesseract_bin:
    pytesseract.pytesseract.tesseract_cmd = tesseract_bin
else:
    pytesseract.pytesseract.tesseract_cmd = \
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"

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
        interpolation=cv2.INTER_CUBIC
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

    config = r'--oem 3 --psm 11 -l por'

    return pytesseract.image_to_string(
        gray,
        config=config
    )


def normalizar_numero(valor):

    valor = valor.replace("(","-")
    valor = valor.replace("[","-")

    if "." not in valor:

        if valor.startswith("-"):

            n = valor.replace("-","")

            if len(n)==4:

                return float(
                    "-" +
                    n[0] +
                    "." +
                    n[1:]
                )

    try:
        return float(valor)
    except:
        return None


def extrair_bloco(texto):

    texto = texto.replace(",", ".")

    nums = re.findall(
        r"[-\[\(]?\d+\.\d+|[-\[\(]?\d+",
        texto
    )

    floats=[]
    ints=[]

    for n in nums:

        numero = normalizar_numero(
            n
        )

        if numero is None:
            continue

        if abs(numero) < 40:

            floats.append(
                numero
            )

        elif 0 <= numero <= 180:

            ints.append(
                int(numero)
            )

    print("FLOATS",floats)
    print("INTS",ints)

    if len(floats)>=2 and len(ints)>=1:

        return {

            "esferico":
                floats[0],

            "cilindrico":
                floats[1],

            "eixo":
                ints[0]

        }

    return None


@app.post("/analisar")
async def analisar(
        file: UploadFile = File(...)
):

    image_bytes = await file.read()

    npimg = np.frombuffer(
        image_bytes,
        np.uint8
    )

    img = cv2.imdecode(
        npimg,
        cv2.IMREAD_COLOR
    )

    texto = executar_ocr(
        img
    )

    texto = texto.upper()
    texto = texto.replace(",", ".")

    print(texto)

    linhas = [

        l.strip()

        for l in texto.splitlines()

        if l.strip()

    ]

    dados={}

    # MODELO COMPLEXO

    for i,linha in enumerate(
            linhas
    ):

        if "OD" in linha:

            bloco = " ".join(
                linhas[i:i+10]
            )

            print(
                "BLOCO OD:",
                bloco
            )

            resultado = extrair_bloco(
                bloco
            )

            if resultado:

                dados["OD"] = resultado


        if "OE" in linha:

            bloco = " ".join(
                linhas[i:i+10]
            )

            print(
                "BLOCO OE:",
                bloco
            )

            resultado = extrair_bloco(
                bloco
            )

            if resultado:

                dados["OE"] = resultado

    # MODELO SIMPLES

    if (

        "OLHO DIREITO"
        in texto

        and

        "OLHO ESQUERDO"
        in texto

    ):

        od = re.search(

            r"OLHO DIREITO.*?"
            r"(-?\d+\.\d+)\s+"
            r"(-?\d+\.\d+)\s+"
            r"(\d{1,3})",

            texto,

            re.S

        )

        oe = re.search(

            r"OLHO ESQUERDO.*?"
            r"(-?\d+\.\d+)\s+"
            r"(-?\d+\.\d+)\s+"
            r"(\d{1,3})",

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

    print(
        "RESULTADO",
        dados
    )

    if not dados:

        return {

            "erro":
            "Não foi possível interpretar"

        }

    return dados


@app.get("/")
def root():

    return {

        "status":
        "online"

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