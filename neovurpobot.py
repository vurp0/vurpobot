#!/usr/bin/env python3

from libvurpobot import *
import sys
import subprocess

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

if __name__ == "__main__":
  config = open("config.txt", "r")
  processor = CommandProcessor(telegram.Bot(token=config.read().rstrip()))
  config.close()
  #processor.registerCommandHandler(CameraHandler([49506617]))
  processor.registerCommandHandler(VurpobotHandler([]))
  #processor.registerCommandHandler(SpeakHandler([]))
  processor.registerCommandHandler(FailHandler([]))
  announceHandler = AnnounceHandler([])
  processor.registerCommandHandler(announceHandler)
  processor.registerVoiceHandler(announceHandler)
  while True:
    try:
      processor.main()
    except KeyboardInterrupt:
      print("Caught KeyboardInterrupt")
      sys.exit(0)

