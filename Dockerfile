FROM python:3
COPY app.py /app/app.py
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip3 install --no-cache-dir -r requirements.txt
EXPOSE 8080
CMD ["python3", "app.py"]