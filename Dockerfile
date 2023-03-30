FROM ubuntu:jammy

# Set the locale
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y locales

RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    update-locale LANG=en_US.UTF-8

ENV LANG en_US.UTF-8

WORKDIR /app
ADD *.py /app/
ADD *.txt /app/
RUN apt-get -y install poppler-utils && \
    apt-get -y install python3 python3-pip && \
    DEBIAN_FRONTEND=noninteractive apt-get -y install ruby ruby-dev gem
ADD requirements.txt .
RUN  pip install --upgrade pip && \
     pip install -r requirements.txt && \
     gem install anystyle nokogiri serrano remote_syslog_logger

# for https://github.com/viig99/SymSpellCppPy:
#  RUN  apt-get -y install git cmake wget && \
#    wget -O resources/frequency_dictionary_de-100k.txt https://raw.githubusercontent.com/wolfgarbe/SymSpell/master/SymSpell.FrequencyDictionary/de-100k.txt && \
#    pip install --upgrade SymSpellCppPy

#RUN chmod 0777 app/tmp && chmod 0777 app/Dataset && chmod 00777 app/Models && chmod 0777 app/cgi-bin/*
ENTRYPOINT ["python3", "/app/run-main.py"]
