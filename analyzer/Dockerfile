FROM python:3.12-slim

WORKDIR /analyzer

# Install Python dependencies
COPY requirements.txt .
RUN  pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Wait for MongoDB to be ready
CMD ["python", "analyzer.py"] 