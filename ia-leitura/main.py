from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pytesseract
import cv2
import numpy as np
import re 
import shutil
import os 

app = FastAPI()

# CORS – Libera acesso para o Android e outras origens
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURAÇÃO DINÂMICA DO TESSERACT ---
# Procura o executável no sistema (necessário para Linux/Render/Docker)
tesseract_bin = shutil.which("tesseract")

if tesseract_bin:
    # Se encontrou no sistema (Linux), usa o caminho detectado
    pytesseract.pytesseract.tesseract_cmd = tesseract_bin
else:
    # Caso contrário, usa o caminho padrão do Windows (Local)
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    # No Windows, também precisamos do TESSDATA_PREFIX
    os.environ["TESSDATA_PREFIX"] = r'C:\Program Files\Tesseract-OCR\tessdata'

@app.post("/analisar")
async def analisar_receita(file: UploadFile = File(...)):

    # Converte o arquivo recebido para formato que o OpenCV entenda
    image_bytes = await file.read()
    npimg = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    if img is None:
        return {"erro": "Não foi possível processar a imagem enviada."}

    # --- PRÉ-PROCESSAMENTO ---
    # Converte para tons de cinza e aplica binarização (ajuda muito o OCR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    # Configuração: OEM 3 (padrão), PSM 6 (bloco único de texto), Idioma Português
    custom_config = r'--oem 3 --psm 6 -l por'

    # --- EXECUTA OCR ---
    texto = pytesseract.image_to_string(gray, config=custom_config)

    # Limpeza de caracteres comuns que o OCR confunde
    texto = texto.replace("’", "'")
    texto = texto.replace(",", ".")
    texto = texto.replace("- ", "-")
    texto = texto.replace("--", "-")
    texto = texto.replace("0./", "0.")
    texto = re.sub(r'(?<=\d)/(?=\d)', '.', texto)

    # Expressão regular para capturar Olho Direito/Esquerdo e os graus
    padrao = re.compile(
        r"OLHO\s+(DIREITO|ESQUERDO).*?(-?\d+[.,']?\d*)[^\d-]+(-?\d+[.,']?\d*)[^\d]+(\d{2,3})",
        re.DOTALL
    )

    dados = {}
    for match in padrao.findall(texto):
        lado_br, esf, cil, eixo = match
        lado_id = 'OD' if lado_br == 'DIREITO' else 'OE'
        
        try:
            dados[lado_id] = {
                "esferico": float(esf.replace(',', '.').replace("'", "")),
                "cilindrico": float(cil.replace(',', '.').replace("'", "")),
                "eixo": int(eixo)
            }
        except ValueError:
            continue # Pula caso algum valor não seja conversível

    # Log para acompanhamento no servidor
    print(f"Resultado da análise: {dados}")

    return dados

if __name__ == "__main__":
    import uvicorn
    # Usa a porta do ambiente (Render) ou a 8000 (Local)
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)