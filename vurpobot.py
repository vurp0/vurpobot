#!/usr/bin/env python

import telegram
import subprocess
import re
import requests,json
import traceback
import sys


"""
Changelog:
version 1: /vurpobot command
version 2: /fortune command and sed-style text replacement
version 3: /hacklab status command
version 4: error handling
"""

VERSION = "4"

print("Connecting to Telegram...")
bot = telegram.Bot(token="TOKEN")
print("Connected.")

LAST_UPDATE_ID = None
receivedUpdates = []


try:
  LAST_UPDATE_ID = bot.getUpdates()[-1].update_id
except IndexError:
  LAST_UPDATE_ID = None

def getChatName(update):
  updateDict = update.to_dict()
  print updateDict
  if updateDict['message']['chat']['type'] == "group":
    return updateDict['message']['chat']['title']
  elif updateDict['message']['chat']['type'] == "private":
    return "{0}{1}{2}".format(updateDict['message']['chat']['first_name'], (" " if (len(updateDict['message']['chat']['last_name']) > 0) else ""), updateDict['message']['chat']['last_name'])
  return ""

print("Starting main loop")
while True:
  try:
    for update in bot.getUpdates(offset=LAST_UPDATE_ID, timeout=10):
      #print update
      lastUpdate = update
      chat_id = update.message.chat_id
      message = update.message.text.encode('utf-8')
      if message == "/vurpobot":
	print("Sending intro message")
	bot.sendMessage(chat_id=chat_id, text="I am but a simple bot, tending to my scripts. v{}".format(VERSION))

      elif message == "/fortune":
	fortune = subprocess.check_output("fortune")
	print("Sending fortune message: {0}".format(fortune))
	bot.sendMessage(chat_id=chat_id, text=fortune)
      elif message == "/hacklab":
	tempRequest = requests.get(url="http://localhost/pi_api/temp/", params={"a":"getTemp"})
	temperature = json.loads(tempRequest.text)['data']
	electronicsRequest = requests.get(url="http://localhost/pi_api/gpio/", params={"a":"readPin", "pin":"1"})
	electronicsLight = json.loads(electronicsRequest.text)['data'] == "0"
	mechanicsRequest = requests.get(url="http://localhost/pi_api/gpio/", params={"a":"readPin", "pin":"0"})
	mechanicsLight = json.loads(mechanicsRequest.text)['data'] == "0"
	if not electronicsLight and not mechanicsLight:
	  lightStatus = "Lights are off. Hacklab is probably empty."
	elif electronicsLight != mechanicsLight:
	  lightStatus = "Lights are on in the {} room.".format(("electronics" if electronicsLight else "mechanics"))
	else:
	  lightStatus = "Lights are on in both rooms!"
	
	responseMessage = u"{} Temperature is {:.2f}\u00b0C".format(lightStatus, temperature)
	bot.sendMessage(chat_id=chat_id, text=responseMessage)

      elif re.search("^s/.+/.+/$", message) != None:
	match = re.search("^s/(.+)/(.+)/$", message)
	fixUpdate = None
	for tempUpdate in reversed(receivedUpdates):
	  if (tempUpdate.message.text.encode('utf-8')[0] != "/") and (tempUpdate.message.chat_id == chat_id):
	    fixUpdate = tempUpdate
	    break
	if fixUpdate != None:
	  print("Sending sed correction message")
	  fixedMessage = fixUpdate.message.text.encode('utf-8').replace(match.groups()[0], "*{}*".format(match.groups()[1]))
	  bot.sendMessage(chat_id=chat_id, text="{}".format(fixedMessage), parse_mode=telegram.ParseMode.MARKDOWN)

      else:
	receivedUpdates.append(update)
	print update
        #print receivedUpdates
     
      LAST_UPDATE_ID = update.update_id+1
  except KeyboardInterrupt:
    print("Caught KeyboardInterrupt, exiting")
    sys.exit(0)
  except:
    err = traceback.format_exc()
    print("Caught exception, reporting\n***\n{}***".format(err))  
    try:
      bot.sendMessage(chat_id=49506617, text="*Error in chat \"{0}\":*\n```\n{1}\n```".format(getChatName(lastUpdate), err), parse_mode=telegram.ParseMode.MARKDOWN) #Hardcoded chat id
      bot.sendMessage(chat_id=chat_id, text="Error processing command! Reported to vurpo.")
    except:
      print("Couldn't report exception")
      print(traceback.format_exc())
  finally:
    LAST_UPDATE_ID = update.update_id+1
