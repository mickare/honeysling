FROM python:3.7

ADD honeysling.py requirements.txt /opt/honeysling/

RUN pip install -r /opt/honeysling/requirements.txt && \
	chmod +x /opt/honeysling/honeysling.py

EXPOSE 22

WORKDIR /opt/honeysling/
CMD /opt/honeysling/honeysling.py