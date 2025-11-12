from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

import pytesseract
import cv2
import numpy as np
import re 
import os 

app = FastAPI()

# CORS – libera acesso pro Angular
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Leitura da imagem

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

os.environ["TESSDATA_PREFIX"] = r'C:\Program Files\Tesseract-OCR\tessdata'

@app.post("/analisar")
async def analisar_receita(file: UploadFile = File(...)):

    image_bytes = await file.read()
    npimg = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    # Pré-processamento

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    custom_config = r'--oem 3 --psm 6 -l por'

    # Executa OCR

    texto = pytesseract.image_to_string(gray, config=custom_config)

    texto = texto.replace("’", "'")
    texto = texto.replace(",", ".")
    texto = texto.replace("- ", "-")
    texto = texto.replace("--", "-")
    texto = texto.replace("0./", "0.")
    texto = re.sub(r'(?<=\d)/(?=\d)', '.', texto)

    padrao = re.compile(
        r"OLHO\s+(DIREITO|ESQUERDO).*?(-?\d+[.,']?\d*)[^\d-]+(-?\d+[.,']?\d*)[^\d]+(\d{2,3})",
        re.DOTALL
    )

    dados = {}
    for match in padrao.findall(texto):
        lado, esf, cil, eixo = match
        lado = 'OD' if lado == 'DIREITO' else 'OE'
        dados[lado] = {
            "esferico": float(esf.replace(',', '.').replace("'", "")),
            "cilindrico": float(cil.replace(',', '.').replace("'", "")),
            "eixo": int(eixo)
        }

    print("\n", dados)

    return {
        "resultado": dados
    }