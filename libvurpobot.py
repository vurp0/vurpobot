#!/usr/bin/env python3

import telegram
import sys
import traceback

def getChatName(update):
  updateDict = update.to_dict()
  print(updateDict)
  if updateDict['message']['chat']['type'] == "group":
    return updateDict['message']['chat']['title']
  elif updateDict['message']['chat']['type'] == "private":
    return "{0}{1}{2}".format(updateDict['message']['chat']['first_name'], (" " if (len(updateDict['message']['chat']['last_name']) > 0) else ""), updateDict['message']['chat']['last_name'])
  return ""

class CommandProcessor:
  def __init__(self, bot):
    print("Init CommandProcessor")
    self.ownerID = 49506617
    self.bot = bot
    self.lastUpdateID = None
    self.commandMap = []
    self.voiceHandlers = []
    try:
      self.lastUpdateID = self.bot.getUpdates()[-1].update_id
    except IndexError:
      self.lastUpdateID = None

  def main(self):
    try:
      for update in self.bot.getUpdates(offset=self.lastUpdateID, timeout=10):
        self.processUpdate(update)
    except KeyboardInterrupt:
      raise
    except:
      self.reportMainloopError()

  def processUpdate(self, update):
    try:
      print(update)
      for handler in self.commandMap:
        if update.message.text.startswith("{} ".format(handler.command)) or update.message.text == handler.command:
          if handler.accessControl == [] or update.message.chat_id in handler.accessControl:
            handler.handleCommand(update)
          else:
            print("chat_id {0} not in handler.accessControl {1}, denying".format(update.message.chat_id, handler.accessControl))
      for handler in self.voiceHandlers:
        if update.message.voice:
          if handler.accessControl == [] or update.message.chat_id in handler.accessControl:
            handler.handleVoice(update)
          else:
            print("denied voiceHandler")
        
    except:
      self.reportCommandError(update)
    finally:
      self.lastUpdateID = update.update_id+1

  def reportMainloopError(self):
    print("Caught exception in mainloop! Reporting to bot owner")
    err = traceback.format_exc()
    print(err)
    try:
      self.bot.sendMessage(chat_id=self.ownerID, text='*Error in mainloop*:\n```\n{1}```'.format(err), parse_mode=telegram.ParseMode.MARKDOWN)
    except:
      print("Caught exception while reporting exception!")
      #print(err)
      print(traceback.format_exc())

  def reportCommandError(self, update):
    print("Caught exception while handling command! Reporting to bot owner")
    err = traceback.format_exc()
    print(err)
    try:
      self.bot.sendMessage(chat_id=self.ownerID, text='*Error in chat "{0}"*:\n```\n{1}```'.format(getChatName(update), err), parse_mode=telegram.ParseMode.MARKDOWN)
      self.bot.sendMessage(chat_id=update.message.chat_id, text='An error occurred! Reported.', reply_to_message_id=update.message.message_id)
    except:
      print("Caught exception while reporting exception!")
      #print(err)
      print(traceback.format_exc())

  def registerCommandHandler(self, handler):
    handler.setBot(self.bot)
    self.commandMap.append(handler)

  def registerVoiceHandler(self, handler):
    handler.setBot(self.bot)
    self.voiceHandlers.append(handler)

class CommandHandler:
  def __init__(self, access):
    self.command = "/command"
    self.accessControl = []
  
  def setBot(self, bot):
    self.bot = bot

  def handleCommand(self, update):
    self.bot.sendMessage(chat_id=update.message.chat_id, text="Default CommandHandler reply")

class VoiceHandler:
  def __init__(self, access):
    self.accessControl = access
  
  def setBot(self, bot):
    self.bot = bot

  def handleVoice(self, update):
    self.bot.sendMessage(chat_id=update.message.chat_id, text="Default VoiceHandler reply")

if __name__ == "__main__":
  processor = CommandProcessor(telegram.Bot(token="TOKEN"))
  processor.registerCommandHandler(CommandHandler())
  while True:
    try:
      processor.main()
    except KeyboardInterrupt:
      print("Caught KeyboardInterrupt")
      sys.exit(0)
