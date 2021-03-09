FROM python:latest
COPY . /app
RUN pip install -r /app/requirements.txt
#EXPOSE 8765
CMD python /app/server.py