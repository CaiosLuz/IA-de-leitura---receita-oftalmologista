# Leitor de Receitas Oftalmológicas

Este projeto utiliza **FastAPI** e **Tesseract OCR** para **ler receitas de oftalmologistas a partir de imagens** e extrair automaticamente os valores de **grau esférico, cilíndrico e eixo** de cada olho (direito e esquerdo).

---

## 🚀 Tecnologias Utilizadas

- 🐍 **Python 3.10+**
- ⚡ **FastAPI** — Framework rápido e moderno para criação de APIs
- 🔍 **Tesseract OCR** — Reconhecimento óptico de caracteres
- 🧠 **OpenCV** — Processamento de imagens
- 🔣 **NumPy** — Manipulação numérica
- 🌐 **CORS Middleware** — Integração com frontend

---

## 📦 Instalação das Dependências

Antes de iniciar, certifique-se de ter o **Python** instalado.  
Em seguida, instale as dependências executando no terminal:

```bash
pip install fastapi uvicorn opencv-python pytesseract numpy
pip install python-multipart
````

## 🧰 Configuração do Tesseract OCR

O projeto precisa do **executável do Tesseract OCR** instalado no computador.

### 🔗 Download:
Baixe a versão recomendada para Windows ou utilize o executavel que está disponível no repositório
👉 [https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)

### ⚙️ Caminhos padrão utilizados no código:
```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"
````
---

## ▶️ Como Executar o Projeto

1. Abra o terminal na pasta do projeto.
2. Execute o comando abaixo para iniciar o servidor:

   ```bash
   uvicorn main:app --reload
