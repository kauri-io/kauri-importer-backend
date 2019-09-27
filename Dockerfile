FROM ubuntu:latest

WORKDIR /app

COPY . /app

RUN apt-get update -y

RUN apt-get install -y python3 python3-pip python3-dev python-pip python-dev build-essential

RUN pip3 install -U pip

RUN pip3 install -r requirements.txt

# RUN pip install -r requirements.txt

ENV GATEWAY_ENDPOINT "https://api.kauri.io/graphql"

CMD ["python3", "main.py"]
