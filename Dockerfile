FROM python:3.11-alpine
LABEL authors="vaibhavjha"

WORKDIR /app
COPY ./requirements.txt /app
RUN pip install -r requirements.txt
COPY . .
ENV LANGCHAIN_TRACING_V2=true
ENV LANGCHAIN_PROJECT=gm_askhr_june_2024
EXPOSE 8000
CMD ["python3", "__main__.py"]

