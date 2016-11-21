#!/usr/bin/env python

# ReadNFC
# Thomas Baer

import httplib
import json
import logging.handlers
import re
import time

import RPi.GPIO as GPIO
import nxppy
from paho.mqtt.publish import single

LOG_FILENAME = "/var/log/nfc.log"
LOG_LEVEL = logging.INFO

SERVER = 'timr.solongo.office'
URI = '/api/cardreader?id='
GREEN = 47
RED = 35
PIEP = 26
ON = GPIO.HIGH
OFF = GPIO.LOW

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=3)
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def on_connect(client, userdata, flags, rc):
    logger.info("Connected with result code " + str(rc))


def blinkled(led, duration, piep):
    GPIO.output(led, ON)
    if piep:
        GPIO.output(PIEP, ON)
    time.sleep(duration)
    GPIO.output(led, OFF)
    if piep:
        GPIO.output(PIEP, OFF)


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(GREEN, GPIO.OUT)
GPIO.setup(RED, GPIO.OUT)
GPIO.setup(PIEP, GPIO.OUT)
GPIO.output(RED, OFF)
GPIO.output(GREEN, OFF)
GPIO.output(PIEP, OFF)

logger.info("NFC Start")
mifare = nxppy.Mifare()
uid1 = ''
while True:
    blinkled(RED, 0.1, False)
    time.sleep(1)
    try:
        uid1 = mifare.select()
        print(uid1)
        if uid1 is not None:
            logger.info("Chip read:" + uid1)
            single('/nfc/read', payload=json.dumps(dict(uid=uid1)), qos=0, retain=False, hostname="192.168.88.13",
                   port=1883, client_id="solongo.nfcreader", keepalive=60)
            conn = httplib.HTTPConnection(SERVER, 80, timeout=5)
            conn.request("GET", URI + uid1)
            r = conn.getresponse()
            if r.status == 200:
                ret = r.getheader('X-Return')
                print(ret)
                if re.match('\d', ret) is not None:
                    for i in range(0, int(ret)):
                        blinkled(GREEN, 0.1, True)
                        time.sleep(0.2)
                else:
                    for i in range(0, 6):
                        blinkled(RED, 0.02, True)
                        time.sleep(0.05)
    except Exception:
        logger.error("Fehler.")