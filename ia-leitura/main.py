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
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"


# -----------------------------
# FUNÇÃO AUXILIAR
# -----------------------------
def extrair_valores(bloco_texto):
    numeros = re.findall(r"-?\d+\.\d+|-?\d+", bloco_texto)

    esf = None
    cil = None
    eixo = None

    floats = []
    ints = []

    for n in numeros:
        try:
            if "." in n:
                floats.append(float(n))
            else:
                i = int(n)
                if 0 <= i <= 180:
                    ints.append(i)
        except:
            pass

    if len(floats) >= 2:
        esf = floats[0]
        cil = floats[1]

    if len(ints) >= 1:
        eixo = ints[0]

    if esf is not None and cil is not None and eixo is not None:
        return {
            "esferico": esf,
            "cilindrico": cil,
            "eixo": eixo
        }

    return None


# -----------------------------
# ENDPOINT
# -----------------------------
@app.post("/analisar")
async def analisar_receita(file: UploadFile = File(...)):

    try:
        image_bytes = await file.read()

        npimg = np.frombuffer(image_bytes, np.uint8)

        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

        if img is None:
            return {"erro": "Imagem inválida"}

        # -----------------------------
        # REDIMENSIONAMENTO
        # -----------------------------
        altura, largura = img.shape[:2]

        if largura > 1000:
            escala = 1000 / largura
            img = cv2.resize(
                img,
                (1000, int(altura * escala)),
                interpolation=cv2.INTER_AREA
            )

        # -----------------------------
        # PREPROCESSAMENTO
        # -----------------------------
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        gray = cv2.threshold(
            gray,
            0,
            255,
            cv2.THRESH_BINARY | cv2.THRESH_OTSU
        )[1]

        custom_config = r'--oem 3 --psm 6 -l por'

        texto = pytesseract.image_to_string(gray, config=custom_config)

        texto_upper = texto.upper()
        texto_upper = texto_upper.replace(",", ".")

        print("\n========== OCR ==========")
        print(texto_upper)

        # -----------------------------
        # RESULTADO FINAL
        # -----------------------------
        dados = {}

        # =====================================================
        # 1) CASO 1: FORMATO COM "LONGE"
        # =====================================================
        linhas = [
            l.strip()
            for l in texto_upper.splitlines()
            if l.strip()
        ]

        indice_longe = next(
            (i for i, l in enumerate(linhas) if "LONGE" in l),
            None
        )

        if indice_longe is not None:

            numeros = []
            for linha in linhas[indice_longe:]:
                encontrados = re.findall(r"-?\d+\.\d+|-?\d+", linha)
                numeros.extend(encontrados)

            decimais = []
            inteiros = []

            for n in numeros:
                try:
                    if "." in n:
                        decimais.append(float(n))
                    else:
                        i = int(n)
                        if 0 <= i <= 180:
                            inteiros.append(i)
                except:
                    pass

            if len(decimais) >= 4 and len(inteiros) >= 2:
                dados["OD"] = {
                    "esferico": decimais[0],
                    "cilindrico": decimais[1],
                    "eixo": inteiros[0]
                }

                dados["OE"] = {
                    "esferico": decimais[2],
                    "cilindrico": decimais[3],
                    "eixo": inteiros[1]
                }

        # =====================================================
        # 2) CASO 2: FORMATO COM OLHO DIREITO / ESQUERDO
        # =====================================================
        if "OLHO DIREITO" in texto_upper and "OLHO ESQUERDO" in texto_upper:

            od_match = re.search(
                r"OLHO DIREITO(.*?)(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(\d{1,3})",
                texto_upper,
                re.S
            )

            oe_match = re.search(
                r"OLHO ESQUERDO(.*?)(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(\d{1,3})",
                texto_upper,
                re.S
            )

            if od_match:
                dados["OD"] = {
                    "esferico": float(od_match.group(2)),
                    "cilindrico": float(od_match.group(3)),
                    "eixo": int(od_match.group(4))
                }

            if oe_match:
                dados["OE"] = {
                    "esferico": float(oe_match.group(2)),
                    "cilindrico": float(oe_match.group(3)),
                    "eixo": int(oe_match.group(4))
                }

        print("Resultado:", dados)

        # -----------------------------
        # RETORNO
        # -----------------------------
        if not dados:
            return {
                "erro": "Não foi possível interpretar a receita"
            }

        return dados

    except Exception as e:
        print(e)
        return {"erro": str(e)}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port
    )