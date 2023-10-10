import os
import discord
from discord.ext import commands
import asyncio
import random
from keep_alive import keep_alive
import json
import time
from typing import Optional
from discord.ext import tasks
from datetime import datetime, timedelta
#import pytz

from discord import app_commands  #added for slash commands 17/05/23

intents = discord.Intents.all()

bot = commands.Bot(command_prefix='!', intents=intents)


#added on 15/05/2023 17:20
@bot.event
async def on_ready():

  await bot.wait_until_ready()  #added later 01/07/2023
  #await bot.change_presence(activity=discord.Game(name="helping my iitm bs degree peeps"))
  await bot.change_presence(activity=discord.Activity(
    type=discord.ActivityType.watching, name="my IITM BS friends"))
  print(f'{bot.user} is ready to chat!')


@bot.command(name="psr")
async def psr(ctx):
  await ctx.send(f'pong! ||{round(bot.latency*1000)} ms||')


doubt_channel_id = 1119540709050040411


#adding reaction on all messages in introduction-----------
@bot.event
async def on_message(message):
  if message.channel.id == 1092838110452252733:  # Replace with the ID of the target channel
    emojis = ["❤️", "👋", "🤝"]  # Replace with the desired reaction emojis
    for emoji in emojis:
      try:
        await message.add_reaction(emoji)
      except discord.Forbidden:
        print(
          f"I don't have permission to add reactions in '{message.channel.name}' channel."
        )
      except discord.HTTPException:
        print(f"Failed to add reactions to message with ID: {message.id}")
  #adding to create thread for doubts-------
  # Check if the message has attachments and is in the target channel
  if message.channel.id == doubt_channel_id and message.attachments:
    username = message.author.name
    # Create a thread from the message
    thread = await message.create_thread(name=f'{username} doubts')
    await message.add_reaction('✅')
    #print(f'Created thread: {thread.name}')
  await bot.process_commands(message)


# Dictionary to keep track of voice channels and associated text channels
custom_channels = {}


@bot.event
async def on_voice_state_update(member, before, after):
  if member.bot:
    return
  # Check if the member joined the specific voice channel
  if after.channel and after.channel.id == 1132584139950932090:  # Replace SPECIFIC_VOICE_CHANNEL_ID with the desired voice channel ID
    guild = member.guild
    category = guild.get_channel(
      1113776348842967132)  # Replace CATEGORY_ID with the desired category ID

    # Create the custom voice channel
    voice_channel = await category.create_voice_channel(
      f"{member.name}'s Voice Channel")

    # Create the associated text channel
    text_channel = await category.create_text_channel(
      f"{member.name}'s Text Channel")

    # Move the member to the created voice channel
    await member.move_to(voice_channel)

    # Grant necessary permissions
    await voice_channel.set_permissions(member,
                                        connect=True,
                                        manage_channels=True)
    await text_channel.set_permissions(member, manage_channels=True)

    # Store the custom channels in the dictionary
    custom_channels[voice_channel.id] = text_channel.id

    # Send a direct message to the member
    #await member.send("Your custom voice channel and text channel have been created!")

  # Check if the member left a voice channel
  if before.channel and before.channel.id in custom_channels:
    # Get the associated text channel
    text_channel_id = custom_channels[before.channel.id]
    text_channel = bot.get_channel(text_channel_id)

    # Check if all members have left the voice channel
    if len(before.channel.members) == 0:
      # Delete the voice channel and text channel
      await before.channel.delete()
      await text_channel.delete()

      # Remove the custom channels from the dictionary
      del custom_channels[before.channel.id]


#adding command to lock and unlock costum voice channles


# Lock command to hide the text channel and the associated voice channel
@bot.command()
async def lock(ctx):
  voice_channel = ctx.author.voice.channel

  # Check if the voice channel is a custom channel
  if voice_channel.id not in custom_channels:
    await ctx.send("You can only lock custom voice channels.")
    return

  text_channel_id = custom_channels[voice_channel.id]
  text_channel = bot.get_channel(text_channel_id)

  # Hide the text channel by adjusting permissions
  await text_channel.set_permissions(ctx.guild.default_role,
                                     read_messages=False)

  # Lock the voice channel
  await voice_channel.set_permissions(ctx.guild.default_role, connect=False)

  # Allow access to the text channel for voice channel members
  for member in voice_channel.members:
    await text_channel.set_permissions(member, read_messages=True)

  await ctx.send(
    "The voice channel has been locked and the associated text channel has been made visible to voice channel members."
  )


#adding command to hide the voice and associate text channel--------
async def hide_custom_channels(bot, voice_channel):
  """Makes the custom voice channel and associated text channel private for everyone except for the users
    who are already in the voice channel.

    Args:
        bot: The Discord bot.
        voice_channel: The custom voice channel to be made private.
    """
  if voice_channel.id not in custom_channels:
    # The voice channel is not a custom voice channel
    raise ValueError("You can only hide custom voice channels.")

  text_channel_id = custom_channels[voice_channel.id]
  text_channel = bot.get_channel(text_channel_id)

  # Set the voice channel to private for everyone
  overwrites = {
    voice_channel.guild.default_role:
    discord.PermissionOverwrite(view_channel=False)
  }
  await voice_channel.edit(overwrites=overwrites)

  # Set the text channel to private for everyone
  overwrites = {
    text_channel.guild.default_role:
    discord.PermissionOverwrite(read_messages=False)
  }
  await text_channel.edit(overwrites=overwrites)

  # Set the voice channel and text channel to viewable for the users who are already in the voice channel
  for member in voice_channel.members:
    overwrites = {
      member:
      discord.PermissionOverwrite(connect=True),
      voice_channel.guild.default_role:
      discord.PermissionOverwrite(view_channel=False)
    }
    await voice_channel.edit(overwrites=overwrites)

  for member in text_channel.members:
    overwrites = {
      member:
      discord.PermissionOverwrite(read_messages=True),
      text_channel.guild.default_role:
      discord.PermissionOverwrite(read_messages=False)
    }
    await text_channel.edit(overwrites=overwrites)
  # Add a delay to prevent rate limiting
  await asyncio.sleep(1)


@bot.command(name="hide")
async def hide(ctx):
  """Makes the custom voice channel and associated text channel private for the user."""
  voice_channel = ctx.author.voice.channel
  if not voice_channel:
    await ctx.send("You are not in a voice channel.")
    return

  try:
    await hide_custom_channels(bot, voice_channel)
    await ctx.send(
      "Custom voice channel and text channel have been made private.")
  except Exception as e:
    # Log the error and send a message to the channel
    print(e)
    await ctx.send("An error occurred while hiding the custom channels.")


# Public command to make the voice and text channels visible to everyone
async def show_custom_channels(bot, voice_channel):
  if voice_channel.id not in custom_channels:
    # The voice channel is not a custom voice channel
    raise ValueError("this command works only for custom voice channels.")

  text_channel_id = custom_channels[voice_channel.id]
  text_channel = bot.get_channel(text_channel_id)

  # Set the voice channel to public for everyone
  overwrites = {
    voice_channel.guild.default_role:
    discord.PermissionOverwrite(view_channel=True)
  }
  await voice_channel.edit(overwrites=overwrites)

  # Set the text channel to public for everyone
  overwrites = {
    text_channel.guild.default_role:
    discord.PermissionOverwrite(read_messages=True)
  }
  await text_channel.edit(overwrites=overwrites)

  # Add a delay to prevent rate limiting
  await asyncio.sleep(1)


@bot.command(name="public")
async def public(ctx):
  """Makes the custom voice channel and associated text channel public for everyone."""
  voice_channel = ctx.author.voice.channel
  if not voice_channel:
    await ctx.send("You are not in a voice channel.")
    return

  try:
    await show_custom_channels(bot, voice_channel)
    await ctx.send(
      "Custom voice channel and text channel have been made public.")
  except Exception as e:
    # Log the error and send a message to the channel
    print(e)
    await ctx.send("An error occurred while showing the custom channel.")


# Error handling for the lock command
@lock.error
async def lock_error(ctx, error):
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.send(
      "Please join a custom voice channel to use the lock command.")
  else:
    await ctx.send("An error occurred while processing the command.")


#invite comamdn to invite a member in a costum voice channel even it its hidden or locked-------


@bot.command(name="invite")
async def invite(ctx, *, member_name: str):
  """Invites a member to the custom voice channel."""
  voice_channel = ctx.author.voice.channel
  if not voice_channel:
    await ctx.send("You are not in a voice channel.")
    return

  try:
    member = discord.utils.get(ctx.guild.members, name=member_name)
    if not member:
      await ctx.send(f"Member with name '{member_name}' not found.")
      return

    # Send an invitation message to the member's DM
    invite_message = f"Hey {member.mention}, you've been invited to join {voice_channel.mention} voice channel!"
    await member.send(invite_message)

    # Set the appropriate permissions for the invited member in the custom voice channel
    overwrites = {
      member:
      discord.PermissionOverwrite(connect=True),
      voice_channel.guild.default_role:
      discord.PermissionOverwrite(connect=False)
    }
    await voice_channel.edit(overwrites=overwrites)

    await ctx.send(f"{member.mention} has been invited to the voice channel.")

  except Exception as e:
    # Log the error and send a message to the channel
    print(e)
    await ctx.send("An error occurred while inviting the member.")


'''
# Command to schedule disconnect from voice channel ---------------------------
@bot.command()
async def disc(ctx, member: discord.Member = None, time: int = 1):
    # This command takes an optional member and a time (in seconds) as arguments
    # If no member is provided, it uses the author of the message as the member
    # It checks if the member is in a voice channel and if the time is positive
    # It sends a message confirming the command and starts a countdown
    # It moves the member to None (disconnects them) when the time is up
    # It sends another message notifying the result

    if member is None:
      member = ctx.author # Use the author of the message as the member

    if member.voice and time > 0:
      await ctx.send(f"Okay, I will disconnect {member.mention} from {member.voice.channel.name} in {time} minutes.")
      await asyncio.sleep(time * 60) # Multiply time by 60 to convert minutes to seconds
      await member.move_to(None)
      await ctx.send(f"{member.name} has been disconnected from voice chat.")
    else:
      await ctx.send("Invalid arguments. Please provide a valid member and a positive time.")


#adding error handling ----------
@disc.error
async def disconnect_error(ctx, error):
    # This function will be called whenever an error occurs in the disconnect command
    # You can use isinstance to check what kind of error it is
    if isinstance(error, commands.MissingRequiredArgument):
        # This error occurs when the user does not provide a required argument
        await ctx.send("Please specify the time (in minutes) for disconnecting. Usage: !disc  [member] <time>")
    elif isinstance(error, commands.BadArgument):
        # This error occurs when the user provides an invalid argument
        await ctx.send("Please provide a valid member or leave it blank to disconnect yourself.")
    elif isinstance(error, commands.BotMissingPermissions):
        # This error occurs when the bot does not have the required permissions to perform the action
        await ctx.send("I do not have permission to move members in voice channels.")
    else:
        # This is a generic error handler for any other kind of error
        await ctx.send(f"Something went wrong: {error}")

'''


@bot.command()
async def disc(ctx, member: discord.Member = None, time: int = 1):
  # This command takes an optional member and a time (in minutes) as arguments
  # If no member is provided, it uses the author of the message as the member
  # If no time is provided, it defaults to 1 (disconnect immediately)
  # It checks if the member is in a voice channel and if the time is positive
  # It sends a message confirming the command and starts a countdown
  # It moves the member to None (disconnects them) when the time is up
  # It sends another message notifying the result

  if member is None:
    member = ctx.author  # Use the author of the message as the member

  if time <= 0:
    time = 1  # Default to 1 minute (disconnect immediately)

  if member.voice and time > 0:
    await ctx.send(
      f"Okay, I will disconnect {member.mention} from {member.voice.channel.name} in {time} minutes."
    )
    await asyncio.sleep(time * 60
                        )  # Multiply time by 60 to convert minutes to seconds
    await member.move_to(None)
    await ctx.send(f"{member.name} has been disconnected from voice chat.")
  else:
    await ctx.send(
      "Invalid arguments. Please provide a valid member and a positive time (in minutes)."
    )


# Adding error handling ----------
@disc.error
async def disconnect_error(ctx, error):
  # This function will be called whenever an error occurs in the disconnect command
  # You can use isinstance to check what kind of error it is
  if isinstance(error, commands.MissingRequiredArgument):
    # This error occurs when the user does not provide a required argument
    await ctx.send(
      "Please specify the time (in minutes) for disconnecting. Usage: !disc [member] <time>"
    )
  elif isinstance(error, commands.BadArgument):
    # This error occurs when the user provides an invalid argument
    await ctx.send(
      "Please provide a valid member or leave it blank to disconnect yourself."
    )
  elif isinstance(error, commands.BotMissingPermissions):
    # This error occurs when the bot does not have the required permissions to perform the action
    await ctx.send(
      "I do not have permission to move members in voice channels.")
  else:
    # This is a generic error handler for any other kind of error
    await ctx.send(f"Something went wrong: {error}")


@bot.command()
async def sta(ctx, *, message):
  guild = ctx.guild
  members = [member for member in guild.members if not member.bot]

  attachments = ctx.message.attachments

  successful_count = 0
  failed_count = 0

  for member in members:
    try:
      if attachments:
        for attachment in attachments:
          await member.send(content=message, file=await attachment.to_file())
      else:
        await member.send(message)
      successful_count += 1
    except discord.Forbidden:
      failed_count += 1
    except discord.HTTPException as e:
      if e.status == 429:
        print("Rate limit reached. Retrying in 5 seconds...")
        await asyncio.sleep(5)
        await member.send(message)
        successful_count += 1
      else:
        print(f"Error sending message to {member.name}: {e}")
        failed_count += 1

    # Add a cooldown between messages to avoid rate limits
    await asyncio.sleep(5)  # Adjust the time as needed

  # Send the summary message to a different channel or wait before sending
  await asyncio.sleep(10)  # Wait before sending the summary message
  summary_channel = bot.get_channel(1064952466581504091)
  await summary_channel.send(
    f"Messages sent to {successful_count} members. Failed to send to {failed_count} members."
  )




keep_alive()
my_secret = os.environ['bot token']

try:
  bot.run(os.getenv('bot token'))
except discord.errors.HTTPException:
  print("\n\n\nBLOCKED BY RATE LIMITS\nRESTARTING NOW\n\n\n")
  os.system('kill 1')
  os.system("python restarter.py")
