FROM python:3.10
ADD main.py .
ADD key.py .
RUN pip install pytelegrambotapi requests flask time
CMD ["python", "./main.py"]