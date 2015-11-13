#!/usr/bin/env python3

from libvurpobot import *
import time
import sys
import subprocess
import requests
import json

def isInt(string):
  try:
    int(string)
    return True
  except:
    return False

class CameraHandler(CommandHandler):
  def __init__(self, access):
    self.command = "/camera"
    self.accessControl = access

  def handleCommand(self, update):
    argument = update.message.text.replace("{} ".format(self.command), "")
    if not isInt(argument):
      self.bot.sendMessage(chat_id=update.message.chat_id, text="Usage:\n/camera <camera number>")
    elif int(argument) not in range(2):
      self.bot.sendMessage(chat_id=update.message.chat_id, text="No such camera")
    else:
      self.bot.sendChatAction(chat_id=update.message.chat_id, action=telegram.ChatAction.UPLOAD_PHOTO)
      subprocess.Popen(["ffmpeg", "-y", "-f", "video4linux2", "-s", "640x480", "-i", "/dev/video{}".format(argument), "-ss", "0:0:2", "-frames", "1", "latest.jpg"]).wait()
      pic = open("latest.jpg", "rb")
      self.bot.sendPhoto(chat_id=update.message.chat_id, photo=pic)
      pic.close()

class VurpobotHandler(CommandHandler):
  def __init__(self, access):
    self.command = "/vurpobot"
    self.accessControl = access
  
  def handleCommand(self, update):
    self.bot.sendChatAction(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
    time.sleep(4)
    self.bot.sendMessage(chat_id=update.message.chat_id, text="JavaScript fuel can't melt Python beams")

class SpeakHandler(CommandHandler):
  def __init__(self, access):
    self.command = "/speak"
    self.accessControl = access
  
  def handleCommand(self, update):
    argument = update.message.text.replace("{} ".format(self.command), "")
    if argument == "" or argument == self.command:
      self.bot.sendMessage(chat_id=update.message.chat_id, text="Usage:\n/speak <text>")
    else:
      self.bot.sendChatAction(chat_id=update.message.chat_id, action=telegram.ChatAction.RECORD_AUDIO)
      subprocess.Popen(["./speak_to_opus.sh", argument]).wait()
      speak = open("output.ogg", "rb")
      self.bot.sendVoice(chat_id=update.message.chat_id, voice=speak)
      speak.close()

class FailHandler(CommandHandler):
  def __init__(self, access):
    self.command = "/fail"
    self.accessControl = access

  def handleCommand(self, update):
    raise(Exception("Can't run the /fail command without raising an exception"))

class AnnounceHandler(CommandHandler,VoiceHandler):
  def __init__(self, access):
    self.command = "/announce"
    self.accessControl = access

  def handleCommand(self, update):
    #argument = update.message.text.replace("{} ".format(self.command), "")
    #self.bot.sendMessage(chat_id=update.message.chat_id, text="WIP")
    self.voiceFile.download("received.ogg")
    subprocess.Popen(["mplayer", "received.ogg"]).wait()
  
  def handleVoice(self, update):
    self.voiceFile = self.bot.getFile(file_id=update.message.voice.file_id)

class HacklabHandler(CommandHandler):
  def __init__(self, access):
    self.command = "/hacklab"
    self.accessControl = access
  
  def handleCommand(self, update):
    apiServer="localhost"
    tempRequest = requests.get(url="http://{}/pi_api/temp/".format(apiServer), params={"a":"getTemp"})
    temperature = json.loads(tempRequest.text)['data']
    humRequest = requests.get(url="http://{}/pi_api/humidity/".format(apiServer), params={"a":"getHumidity"})
    humidity = json.loads(humRequest.text)['data']
    electronicsRequest = requests.get(url="http://{}/pi_api/gpio/".format(apiServer), params={"a":"readPin", "pin":"1"})
    electronicsLight = json.loads(electronicsRequest.text)['data'] == "0"
    mechanicsRequest = requests.get(url="http://{}/pi_api/gpio/".format(apiServer), params={"a":"readPin", "pin":"0"})
    mechanicsLight = json.loads(mechanicsRequest.text)['data'] == "0"
    if not electronicsLight and not mechanicsLight:
      lightStatus = "Lights are off. Hacklab is probably empty."
    elif electronicsLight != mechanicsLight:
      lightStatus = "Lights are on in the {} room.".format(("electronics" if electronicsLight else "mechanics"))
    else:
      lightStatus = "Lights are on in both rooms!"

    responseMessage = "{} Temperature is {:.1f}\u00b0C. Humidity is {}".format(lightStatus, temperature, humidity)
    self.bot.sendMessage(chat_id=update.message.chat_id, text=responseMessage)

class HumidityHandler(CommandHandler):
  def __init__(self, access):
    self.command = "/humidity"
    self.accessControl = access
  
  def handleCommand(self, update):
    apiServer="localhost"
    humRequest = requests.get(url="http://{}/pi_api/humidity/".format(apiServer), params={"a":"getHumidity"})
    humidity = json.loads(humRequest.text)['data']
    self.bot.sendMessage(chat_id=update.message.chat_id, text="Humidity is {}%".format(humidity))

if __name__ == "__main__":
  config = open("config.txt", "r")
  processor = CommandProcessor(telegram.Bot(token=config.read().rstrip()))
  config.close()
  processor.registerCommandHandler(VurpobotHandler([]))
  processor.registerCommandHandler(HacklabHandler([]))
  processor.registerCommandHandler(CameraHandler([]))
  processor.registerCommandHandler(SpeakHandler([]))
  while True:
    try:
      processor.main()
    except KeyboardInterrupt:
      print("Caught KeyboardInterrupt")
      sys.exit(0)

