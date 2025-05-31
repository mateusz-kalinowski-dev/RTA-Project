FROM python:3.12-slim

WORKDIR /analyzer

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "analyzer.py"] 