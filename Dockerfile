FROM python:3.11-slim

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia os arquivos e instala as libs do Python
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

# Porta que o Render geralmente espera (10000 ou 80)
EXPOSE 80

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]