# Project: AI_Blackjack - test GPT's ability to play Blackjack
# Author - Stephen Witty switty@level500.com
# Started 7-7-24
# Description - ask GPT to play Blackjack and measure results
# Example used from openai for vision gpt
# To run:
#     tested on ubuntu
#     install OpenAI Python lib (see OpenAI website for instructions)
#     install ImageMagic to gain access to the "convert" command
#     install package feh
#
# V1 7-7-24   Initial development

import random
import time
import os
import sys
import base64
import requests
import subprocess
import re

# OpenAI API Key
api_key = "XXXXXXXXXXXXXXXXXXXXXXXXXXX"

##################### Constants ###########################################################################################
VERSION = 1                                             # Version of code
GAMES = 100                                             # Number of times to run the test
CARD_DIR = "/home/switty/Dev/Blackjack/Cards"           # Picture directory  location fully pathed, do not include / on the end
CARD_TEMP = "/home/switty/Dev/Blackjack/temp"           # Temp folder to create card pictures, do not include / on the end
DELAY = 20                                              # Delay time per test run to display results in seconds
MAX_ERRORS = 6                                          # Max errors when calling GPT before exiting
SEED = -1                                               # Random number seed for deck shuffle, if -1 use system clock
###########################################################################################################################

###################### Running variables
deck = []         # Playing deck with cards inside
deck_pos = 0      # Points to next card to deal off the deck
dealer = []       # Dealer's hand
player = []       # Player's hand
web_api_error = 0 # Track the number of GPT web errors
no_answer = 0     # Track the number of times GPT does not answer the question
player_wins = 0   # Number of times that the player won
dealer_wins = 0   # Number of times that the dealer won
pushes = 0        # Number of ties / pushes

######################### Function to encode the image
def encode_image(image_path):
   with open(image_path, "rb") as image_file:
      return base64.b64encode(image_file.read()).decode('utf-8')

######################### Add suit to card deck
def add_suit(suit):
   for i in range(2,10):
      deck.append(suit + str(i))
   deck.append(suit + "0")  # This is ten
   deck.append(suit + "A")  # Ace
   deck.append(suit + "K")  # King
   deck.append(suit + "Q")  # Queen
   deck.append(suit + "J")  # Jack

######################### Shuffle deck
def shuffle():
#   print("Shuffle deck")
   for i in range(52):
      random_number = random.randint(0,51)
      store =  deck[i]
      deck[i] = deck[random_number]
      deck[random_number] = store

######################### Return next card in the deck
def next_card():
   global deck_pos
   deck_pos = deck_pos + 1 # Move to next card in the deck
   if (deck_pos > 51):
      print("ERROR: Ran past the end of the deck")
      os.sys.exit(1)
   return(deck[deck_pos])

######################## Create board image
def create_board_image(flip_dealer_first_card):
   if (len(CARD_TEMP)<5):
      print("ERROR CARD_TEMP is too short")
      os.sys.exit(1)
   os.system("rm -f " + CARD_TEMP + "/*")
   if not os.path.exists(CARD_TEMP + "/"):
      print("ERROR Card temp folder does not exist")
      os.sys.exit(1)
   if not os.path.isdir(CARD_TEMP + "/"):
      print("ERROR Card temp folder is not a directory")
      os.sys.exit(1)
   if not len(os.listdir(CARD_TEMP + "/")) == 0:
      print("ERROR Delete of files in Card temp directory failed")
      os.sys.exit(1)
   if not os.path.isdir(CARD_DIR + "/"):
      print("ERROR Card Directory does not exist")
      os.sys.exit(1)

   dealer_length=len(dealer)
   player_length=len(player)
   if (dealer_length <= player_length):
      length=player_length
   else:
      length=dealer_length

   # Form player row
   os.system("convert "+CARD_DIR+"/"+player[0]+".jpg "+CARD_DIR+"/"+player[1]+".jpg +append "+CARD_TEMP+"/player.jpg")
   for i in range (2,length):
      if (i < len(player)):
         os.system("convert "+CARD_TEMP+"/player.jpg "+CARD_DIR+"/"+player[i]+".jpg +append "+CARD_TEMP+"/player.jpg")
      else:
         os.system("convert "+CARD_TEMP+"/player.jpg "+CARD_DIR+"/EMPTY.jpg +append "+CARD_TEMP+"/player.jpg")

   # Form dealer row
   if (flip_dealer_first_card == True):
      os.system("convert "+CARD_DIR+"/"+dealer[0]+".jpg "+CARD_DIR+"/"+dealer[1]+".jpg +append "+CARD_TEMP+"/dealer.jpg")
   else:
      os.system("convert "+CARD_DIR+"/BACK.jpg "+CARD_DIR+"/"+dealer[1]+".jpg +append "+CARD_TEMP+"/dealer.jpg")
   for i in range (2,length):
      if (i < len(dealer)):
         os.system("convert "+CARD_TEMP+"/dealer.jpg "+CARD_DIR+"/"+dealer[i]+".jpg +append "+CARD_TEMP+"/dealer.jpg")
      else:
         os.system("convert "+CARD_TEMP+"/dealer.jpg "+CARD_DIR+"/EMPTY.jpg +append "+CARD_TEMP+"/dealer.jpg")

   # Form middle blank row
   os.system("convert "+CARD_DIR+"/EMPTY.jpg "+CARD_DIR+"/EMPTY.jpg +append "+CARD_TEMP+"/middle.jpg")
   for i in range (2,length):
      os.system("convert "+CARD_TEMP+"/middle.jpg "+CARD_DIR+"/EMPTY.jpg +append "+CARD_TEMP+"/middle.jpg")

   # Add three rows together
   os.system("convert "+CARD_TEMP+"/dealer.jpg "+CARD_TEMP+"/middle.jpg -append "+CARD_TEMP+"/board.jpg")
   os.system("convert "+CARD_TEMP+"/board.jpg "+CARD_TEMP+"/player.jpg -append "+CARD_TEMP+"/board.jpg")

   os.system("convert "+CARD_TEMP+"/board.jpg -resize 1024x768 "+CARD_TEMP+"/board.jpg")

#################### Calculate hand value
def hand_value(hand):
   value = 0
   value2 = 0
   ace = False
   for i in range(0,len(hand)):
      check = hand[i][-1]
      if (check=="K" or check=="Q" or check=="J" or check=="0"):
         value = value + 10
      elif (check=="A"):
         value = value + 1
         ace = True
      else:
         value = value + int(check)

   # See if it helps to make the Ace an 11
   value2 = value
   if (ace == True):
      value2 = value - 1 + 11

   if (value2 <= 21):
      return value2
   else:
      return value

################# Display Board
def display_board():
   process = subprocess.Popen(["feh",CARD_TEMP+"/board.jpg"],stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
   return process

########### Display final board of game - display, wait then close 
def display_final_board():
   create_board_image(True)
   process = display_board()

   dealer_value = hand_value(dealer)
   player_value = hand_value(player)

   display_hand_values()
#   input("Press enter to continue\n")
   time.sleep(DELAY)
   process.terminate()

############### Display the hands and values of each
def display_hand_values():
   dealer_value_tmp = hand_value(dealer)
   player_value_tmp = hand_value(player)

   print()
   print(dealer, end="")
   print(" Dealer Value: " + str(dealer_value_tmp))
   print(player, end="")
   print(" Player Value: " + str(player_value_tmp))

####################### Does GPT want another card?
def gpt_card():
   global web_api_error
   global no_answer
   attempts=0

   while(attempts < MAX_ERRORS):
      time.sleep(1)
      attempts =  attempts + 1
      # Getting the base64 string
      base64_image = encode_image(CARD_TEMP+"/board.jpg")
      headers = {
         "Content-Type": "application/json",
         "Authorization": f"Bearer {api_key}"
      }

      # Construct GPT API json, this is from GPT example code
      payload = {
         "model": "gpt-4o",
         "messages": [
            {
               "role": "user",
               "content": [
                  {
                     "type": "text",
                     "text": "You are an expert blackjack player.  You are playing blackjack.  The game has already started.  In the supplied image, the top cards are the house dealers and the bottom cards are yours.  Your goal is to win the game by making the best decision.  Do you want to be dealt another card?   Provide back the answer as YES or NO between {}.  For example if the answer is YES then reply back with {YES}.  Also lists the cards in your hand and the dealer's hand"
                  },
                  {
                     "type": "image_url",
                     "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                  }
               }
            ]
         }
      ],
      "max_tokens": 300
      }

      output = {}
      try:
         response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=90)
         output = response.json()
      except Exception as e:
         print("ERROR - Exception on openai web call.")
         print(e)
         web_api_error = web_api_error + 1
         continue

      if (response.status_code != 200  or "error" in output):
         print("ERROR - Received return error from openai web api.  Status code = " + str(response.status_code))
         web_api_error = web_api_error + 1
         if ("error" in output):
            print(output["error"]["message"])
         continue

      if ("choices" not in output):
         print("ERROR - Choices is not in output from GPT")
         web_api_error = web_api_error + 1
         continue

      message = output["choices"][0]["message"]["content"]

#   message = "{no}"  # debug line if needed

   ################### Extract GPT answer from {} ###################################
   # Making several checks to make sure we are getting the answer in the right format
      cnt = 0
      cnt2 = 0
      pos = 0
      for char in message:
         if (char == "{"):
            cnt = cnt + 1
            start = pos
         if (char == "}"):
            cnt2 = cnt2 + 1
            end = pos
         pos = pos + 1

      if (cnt == 0 or cnt2 == 0):
         print("ERROR:  No brackets or incomplete")
         no_answer = no_answer + 1
         continue

      if (cnt > 1 or cnt2 > 1):
         print("ERROR:  Too many brackets in output from GPT")
         no_answer = no_answer + 1
         continue

      if (end < start):
         print("ERROR: Brackets are reversed in output from GPT")
         no_answer = no_answer + 1
         continue

      if ( (end - start) != 3 and (end - start) != 4):
         print("ERROR: Answer is the wrong size (Either 2 or 3 characters)")
         no_answer = no_answer + 1
         continue

      # Parse out the answer in between {}
      answer = ""
      match = re.search(r'\{(.*?)\}',message)
      answer = match.group(1)
      answer = answer.upper()

#      print(message)

      # Check and see if the answer is YES or NO
      if (answer != "YES" and answer != "NO"):
         print("ERROR, The answer is not YES or NO")
         no_answer = no_answer + 1
         continue

      if (answer == "YES"):
         return True
      else:
         return False
################ End Extract GPT answer #######

###################### Start of Main program 
print("AI Blackjack....")
print("Version: " + str(VERSION))
print("Card directory: " + str(CARD_DIR))
print("Temp directory: " + str(CARD_TEMP))
print("Games to play: " + str(GAMES))
print("Delay between games: " + str(DELAY))
print("GPT max errors: " + str(MAX_ERRORS))
print("Random seed: " + str(SEED))

print("Creating card deck")

# Set up the card deck
add_suit("D")  # Diamonds
add_suit("S")  # Spades
add_suit("H")  # Hearts
add_suit("C")  # Clubs
print("Size of card deck: ",len(deck))

# Setup random number seed for shuffle operation
# Use system time if constant is -1
if (SEED == -1):
   seed = int(time.time()) # Use Unix epoch
else:
   seed = SEED;
print("Seed for random shuffle: " + str(seed))
random.seed(seed)

count=0
while(count < GAMES):
   count = count + 1
   os.system("clear")
   print("***** Starting a new game.  Game number: " + str(count))
   print()
   shuffle()
   deck_pos = 0
   dealer = []
   player = []
   # Dealer and player gets two cards to start
   dealer.append(next_card())
   player.append(next_card())
   dealer.append(next_card())
   player.append(next_card())

   dealer_value = hand_value(dealer)
   player_value = hand_value(player)

#   display_hand_values()

   # Check if player got a blackjack
   if (player_value == 21):
      print("Player has Blackjack")

      # Check and see if dealer is also a blackjack
      if (dealer_value == 21):
         print(">>>>>>>>>> Dealer Blackjack, PUSH")
         pushes = pushes + 1
      else:
         print(">>>>>>>>>> Player Wins")
         player_wins = player_wins + 1

      display_final_board()
      continue

   get_card = True
   # Stay in this loop until player gets all cards wanted or goes bust
   while(player_value < 21 and get_card == True):
      create_board_image(False)
      process = display_board()
 #     input("Press enter\n")

      print("GPT is thinking.....")
      get_card = gpt_card()
      if (get_card == True):
         print("Player HITS")
         player.append(next_card())
         process.terminate()

         dealer_value = hand_value(dealer)
         player_value = hand_value(player)

#         display_hand_values()

      else:
         print("Player STANDS")
         process.terminate()

   # Check and see if player went bust
   if (player_value > 21):
      print("Player went bust")
      print(">>>>>>>> Dealer Wins")
      display_final_board()
      dealer_wins = dealer_wins + 1
      continue

   # Dealers turn - keep getting cards until total is at least 17
   while(dealer_value < 17):
      dealer.append(next_card())
      dealer_value = hand_value(dealer)

   # Check if Dealer went bust
   if (dealer_value > 21):
      print("Dealer went bust")
      print(">>>>>>> Player Wins")
      display_final_board()
      player_wins = player_wins + 1
      continue

   # Check if Dealer has blackjack
   if (dealer_value == 21 and len(dealer) == 2):
      print("Dealer has Blackjack")
      print(">>>>>>> Dealer Wins")
      display_final_board()
      dealer_wins = dealer_wins + 1
      continue

   # Check for tie / PUSH
   if (dealer_value == player_value):
      print(">>>>>>> PUSH, no winner")
      display_final_board()
      pushes = pushes + 1
      continue

   # Check for Player win
   if (dealer_value <  player_value):
      print(">>>>>> Player Wins")
      display_final_board()
      player_wins = player_wins + 1
      continue

   # Check for Dealer win
   if (dealer_value > player_value):
      print(">>>>>> Dealer Wins")
      display_final_board()
      dealer_wins = dealer_wins + 1
      continue

   # Should never make it to this bottom of loop, missed a condition somewhere
   print("ERROR:  Should not make it to bottom of loop!!!!!")
   display_final_board()
   os.sys.exit(1)

os.system("clear")
print("\n\n********* Summary **************")
print("Number of games: " + str(GAMES))
print("Player wins: " + str(player_wins))
print("Dealer wins: " + str(dealer_wins))
print("Pushes: " + str(pushes))
print("GPT no answer: " + str(no_answer))
print("GPT web api error: " + str(no_answer))
print("***********************\n\n\n")
