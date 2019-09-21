FROM gorialis/discord.py

WORKDIR /app

COPY setup.py ./
RUN pip install -r setup.py

COPY . .

CMD ["python", "bot.py"]
