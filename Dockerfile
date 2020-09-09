FROM python:3.7-slim as BUILDER

RUN apt-get -y update
RUN apt install -y -qq python3-pip
RUN apt install -y -qq -f openjdk-11-jdk-headless; exit 0

RUN apt-get -y update

ENV JAVA_HOME="/usr/lib/jvm/java-11-openjdk-amd64"
ENV PATH="${JAVA_HOME}/bin:${PATH}"

COPY * /home/

RUN pip3 install -r /home/requirements.txt

CMD ["python3", "/home/bioformat_extractor.py"]