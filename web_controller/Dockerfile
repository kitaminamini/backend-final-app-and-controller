FROM python:3.7-alpine

# Python packages
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
# EXPOSE 8000
CMD ["python", "main.py"]