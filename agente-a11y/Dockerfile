FROM mcr.microsoft.com/playwright/python:v1.46.0-jammy

WORKDIR /app

# Instalar requerimientos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY . .

# Exponer el puerto del servidor web
EXPOSE 8000

# Iniciar el agente en modo servidor
CMD ["python", "-m", "a11y_agent", "serve", "--host", "0.0.0.0", "--port", "8000"]
