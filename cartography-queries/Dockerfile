FROM python:3.7-slim

RUN addgroup --gid 11111 app
RUN adduser --shell /bin/false --uid 11111 --ingroup app app


WORKDIR /app/
COPY * .

RUN pip3 install -r requirements.txt
RUN chmod +x query_manager.py
RUN chmod +x query_builder.py
RUN chown -R app:app /app
USER app

# ENTRYPOINT ["/app/query_manager.py"]
# ENTRYPOINT ["/app/query_builder.py"]
