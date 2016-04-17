#!/usr/bin/env python3

from libvurpobot import *
import time
import sys
import subprocess
import grequests
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
    subprocess.Popen(["opusdec", "received.ogg", "received.wav"]).wait()
    subprocess.Popen(["mplayer", "received.wav"]).wait()
  
  def handleVoice(self, update):
    self.voiceFile = self.bot.getFile(file_id=update.message.voice.file_id)

class HacklabHandler(CommandHandler):
  def __init__(self, access):
    self.command = "/hacklab"
    self.accessControl = access
  
  def handleCommand(self, update):
    self.bot.sendChatAction(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
    apiServer="localhost"
    hacklabRequests = [
        grequests.get(url="http://{}/pi_api/temp/".format(apiServer), params={"a":"getTemp"}),              # 0: temperature
        grequests.get(url="http://{}/pi_api/humidity/".format(apiServer), params={"a":"getHumidity"}),      # 1: humidity
        grequests.get(url="http://{}/pi_api/gpio/".format(apiServer), params={"a":"readPin", "pin":"1"}),   # 2: electronics
        grequests.get(url="http://{}/pi_api/gpio/".format(apiServer), params={"a":"readPin", "pin":"0"}),   # 3: mechanics
        grequests.get(url="http://{}/pi_api/pir/".format(apiServer), params={"a":"getStatus"})]             # 4: PIR
    hacklabResponses = grequests.map(hacklabRequests)
    if None in hacklabResponses:
        raise ConnectionError("A request for the /hacklab command failed!")

    temperature = json.loads(hacklabResponses[0].text)['data']
    humidity = json.loads(hacklabResponses[1].text)['data']
    electronicsLight = json.loads(hacklabResponses[2].text)['data'] == "0"
    mechanicsLight = json.loads(hacklabResponses[3].text)['data'] == "0"
    pirStatus = json.loads(hacklabResponses[4].text)['time']

    if not electronicsLight and not mechanicsLight:
      lightStatus = "Lights are off. Hacklab is probably empty."
    elif electronicsLight != mechanicsLight:
      lightStatus = "Lights are on in the {} room.".format(("electronics" if electronicsLight else "mechanics"))
    else:
      lightStatus = "Lights are on in both rooms!"

    responseMessage = "{} Last movement at {}. Temperature is {:.1f}\u00b0C. Humidity is {}%".format(lightStatus, pirStatus, temperature, humidity)
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
  announceHandler = AnnounceHandler([-3450879])
  processor.registerCommandHandler(announceHandler)
  processor.registerVoiceHandler(announceHandler)
  processor.registerCommandHandler(HacklabHandler([]))
  #processor.registerCommandHandler(HumidityHandler([]))
  while True:
    try:
      processor.main()
    except KeyboardInterrupt:
      print("Caught KeyboardInterrupt")
      sys.exit(0)

