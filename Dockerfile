FROM python:3.8

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip3 install -r requirements.txt
COPY . .

RUN python3 ./manage.py initial_setup
RUN python3 ./manage.py load_test_data
COPY storage2-dev-localhost.pem /etc/ssl/certs/storage2-dev-localhost.pem

ENV DEBUG=True

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
