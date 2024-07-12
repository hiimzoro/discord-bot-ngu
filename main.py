import os
import discord
from discord.ext import commands
from google.cloud import translate_v3
from google.cloud import texttospeech
from dotenv import load_dotenv
import json
import logging

#load environment var
load_dotenv()

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not DISCORD_BOT_TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN environment variable not set")

google_credential_path = os.path.join(os.path.dirname(__file__),
                                      'credentials', 'bot-ngu-f1b992809c18.json')
if not os.path.exists(google_credential_path):
    raise FileNotFoundError(f"Credentials file not found at {google_credential_path}")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = google_credential_path

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

translate_client = translate_v3.TranslationServiceClient()
text_to_speech_client = texttospeech.TextToSpeechClient()

FILE_PATH = 'reply_channels.json'
BOT_CONFIG_ROLE = 'bot_config'

reply_channels = []

#logging
logging.basicConfig(level=logging.INFO)


def load_id():
    global reply_channels
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, 'r') as f:
            try:
                reply_channels = json.load(f)
                logging.info(f"Loaded reply channels: {reply_channels}")
            except json.JSONDecodeError:
                logging.warning('File is empty or invalid JSON. Initializing with an empty list.')
                reply_channels = []
    else:
        logging.info('File not found. Initializing with an empty list.')
        reply_channels = []


def translate_text(text) -> translate_v3.TranslationServiceClient:
    project_id = 'bot-ngu'
    location = 'global'
    parent = f"projects/{project_id}/locations/{location}"

    try:
        response = translate_client.translate_text(
            parent=parent,
            contents=[text],
            mime_type="text/plain",
            target_language_code='de'
        )
        return response.translations[0].translated_text
    except Exception as e:
        logging.error(f'Error translating text: {e}')
        return None


def text_to_speech(text) -> bytes:
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice_params = texttospeech.VoiceSelectionParams(
        language_code='de',
        name='de-DE-Wavenet-B',
        ssml_gender=texttospeech.SsmlVoiceGender.MALE
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    try:
        response = text_to_speech_client.synthesize_speech(
            input=synthesis_input, voice=voice_params, audio_config=audio_config
        )
        return response.audio_content
    except Exception as e:
        logging.error(f"Error converting text to speech: {e}")
        return None


@bot.command(name='setchannel')
@commands.has_role(BOT_CONFIG_ROLE)
async def set_channel(ctx):
    if ctx.channel.id not in reply_channels:
        reply_channels.append(ctx.channel.id)
        with open(FILE_PATH, 'w') as f:
            json.dump(reply_channels, f, indent=4)
        await ctx.send("Từ giờ tôi sẽ trả lời kênh này")
    else:
        await ctx.send("Tôi đã được gán vào kênh này")


@set_channel.error
async def set_channel_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send('Bạn không có role để dùng lệnh này')
    else:
        logging.error(f"Error in set_channel command: {error}")


@bot.command(name='clearchannel')
@commands.has_role(BOT_CONFIG_ROLE)
async def clear_channel(ctx):
    if ctx.channel.id in reply_channels:
        reply_channels.remove(ctx.channel.id)
        with open(FILE_PATH, 'w') as f:
            json.dump(reply_channels, f, indent=4)
        await ctx.send('Kênh được bỏ')
    else:
        await ctx.send('Kênh không được gán')


@clear_channel.error
async def clear_channel_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send('Bạn không có đúng role để dùng lệnh này.')
    else:
        logging.error(f"Error in clear_channel command: {error}")


#start up method
@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user.name} ({bot.user.id})')
    load_id()


@bot.event
async def on_message(message):
    # cannot reply to self
    if message.author == bot.user:
        return

    ctx = await bot.get_context(message)
    if ctx.command is not None:
        await bot.process_commands(message)
        return

    if message.channel.id in reply_channels:
        async with message.channel.typing():
            translated_message = translate_text(message.content)

            if translated_message:
                speech_content = text_to_speech(translated_message)

                if speech_content:
                    # Save the speech content to a file and send it
                    with open('ban_dich.mp3', 'wb') as f:
                        f.write(speech_content)
                    await message.channel.send(translated_message, file=discord.File('ban_dich.mp3'))
                else:
                    logging.error('Error converting to voice')
            else:
                logging.error('Error translating')
    else:
        allowed_channels = [bot.get_channel(ch_id).mention for ch_id in reply_channels if bot.get_channel(ch_id)]
        await message.channel.send(
            f"Xin lỗi, tôi không thể trả lời đc ở đây, xin vui lòng sang những kênh sau:{", ".join(allowed_channels)}")


def main():
    try:
        bot.run(DISCORD_BOT_TOKEN)
    except Exception as e:
        logging.error(f'Error running bot:{e}')


if __name__ == '__main__':
    main()
