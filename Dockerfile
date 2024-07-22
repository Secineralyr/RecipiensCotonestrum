FROM python:3.11.9-bookworm

ENV TZ=Asia/Tokyo

RUN apt update -y && apt upgrade -y && apt autoremove -y

RUN apt install -y python3-venv


RUN mkdir /root/main
WORKDIR /root/main

RUN mkdir venv && python3 -m venv venv && chmod +x venv/bin/activate

COPY requirements.txt /root/main
RUN venv/bin/activate && python3 -m pip install -U pip && python3 -m pip install -r requirements.txt && rm requirements.txt

COPY src /root/main
COPY .env /root/main

CMD cd /root/main && venv/bin/activate && python3 main.py
