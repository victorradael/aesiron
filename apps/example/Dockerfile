FROM python:3.13-slim

# Define o diretório de trabalho como /app
WORKDIR /app

# Copia o arquivo requirements.txt para o diretório de trabalho
COPY requirements.txt .

RUN pip install -r requirements.txt

# Copia todo o conteúdo do diretório atual para /app no contêiner
COPY ./app /app

EXPOSE 8501

CMD ["streamlit", "run", "app.py"]

