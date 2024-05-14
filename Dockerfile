FROM ubuntu:24.04

RUN apt update && apt upgrade -y
RUN echo -e "2\n105" | apt install software-properties-common -y
RUN add-apt-repository ppa:deadsnakes/ppa -y
RUN apt update
RUN apt install python3-pip -y
RUN apt install python3.12-venv -y
RUN apt install curl file -y
RUN rm -f /usr/lib/python3.12/EXTERNALLY-MANAGED

RUN useradd -c 'GraphFS user' -m -d /graphfs -s /bin/bash graphfs
USER graphfs
WORKDIR /graphfs

COPY binstore binstore
COPY etc/config.yml etc/
COPY requirements.txt .

RUN pip3 install -r requirements.txt
RUN echo export PATH=/graphfs/.local/bin:$PATH >> /graphfs/.profile
RUN echo export PYTHONPATH=/graphfs/binstore/src >> /graphfs/.profile

EXPOSE 9000/tcp

CMD ["/bin/bash", "-c", "source /graphfs/.profile && cd binstore && uvicorn main:app --host 0.0.0.0 --port 9000"]
