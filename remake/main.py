# -*- coding: ascii -*-
# by mrfriot
# systemctl start postgresql.service

import telebot
import logging
import os

ADMINID = []

bot = telebot.TeleBot(os.environ["token"])

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        filename="bot.log",
        encoding="ascii",
        filemode="a",
        format="{asctime} | {levelname} | {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M"
    )
    logging.info("Bot started.")
    for admin in ADMINID:
        bot.send_message(admin, "Bot started.")
    bot.infinity_polling()
