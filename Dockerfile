FROM gorialis/discord.py:3.6-alpine-master-extras

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "/usr/local/bin/botintegration"]
