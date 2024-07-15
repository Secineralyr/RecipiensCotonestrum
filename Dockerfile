FROM python:3.11.9-bookworm

ENV TZ=Asia/Tokyo

RUN apt update -y && apt upgrade -y && apt autoremove -y

RUN apt install -y python3-venv

# RUN apt install -y wget

# RUN DEBIAN_FRONTEND=noninteractive apt install -y build-essential libbz2-dev libdb-dev \
#     libreadline-dev libffi-dev libgdbm-dev liblzma-dev \
#     libncursesw5-dev libsqlite3-dev libssl-dev \
#     zlib1g-dev uuid-dev tk-dev

# RUN mkdir /root/python
# WORKDIR /root/python
# RUN wget https://www.python.org/ftp/python/3.11.0/Python-3.11.0.tar.xz && tar xJf Python-3.11.0.tar.xz && cd Python-3.11.0 && ./configure && make && make install

RUN mkdir /root/main
WORKDIR /root/main
ADD src/*.py /root/main
ADD .env /root/main
ADD requirements.txt /root/main

RUN mkdir venv && python3 -m venv venv && chmod +x venv/bin/activate
RUN venv/bin/activate && python3 -m pip install -U pip && python3 -m pip install -r requirements.txt && rm requirements.txt

CMD cd /root/main && venv/bin/activate && python3 main.py
