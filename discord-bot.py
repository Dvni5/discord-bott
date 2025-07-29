import discord
from discord.ext import commands
from discord.ui import View, Button

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

CHANNEL_IDS = {
    1399282231100571749: "🔫｜𝗸𝗶𝗹𝗹𝗳𝘅",
    1397422724149940375: "🔫｜𝗦𝗵𝘂𝗱𝗴𝗮𝗻",
    1397676630293352559: "🧪｜𝗖𝘂𝘀𝘁𝗼𝗺-𝗩𝗮𝘂𝗹𝘁-𝗙𝗫",
    1397403629723586641: "🔫｜𝗥𝗲𝘃𝗼𝗹𝘃𝗲𝗿",
    1397422417856692346: "🔫｜𝗥𝗜𝗙𝗟𝗘𝗦",
    1397493393117937704: "🔫｜𝗠𝗔𝗖𝗥𝗢",
    1397493937975066694: "🔫｜𝗦𝗠𝗚",
    1397494133848801300: "🔫｜𝗗𝗿𝘂𝗺𝗴𝗲𝗻",
    1397494526284927016: "🔫｜𝗦𝗻𝗶𝗽𝗲𝗿",
    1399321793893761145: "🔫｜𝗧𝗿𝗮𝗰𝗲𝗿𝘀",
}

MAX_SIZE = 8 * 1024 * 1024  # 8 ميجابايت

user_states = {}

class ChannelSelectView(View):
    def __init__(self, user_id, content):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.content = content

        for channel_id, name in CHANNEL_IDS.items():
            self.add_item(ChannelButton(channel_id, name))

    async def on_timeout(self):
        user_states.pop(self.user_id, None)

class ChannelButton(Button):
    def __init__(self, channel_id, label):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.channel_id = channel_id

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        if user_id != self.view.user_id:
            await interaction.response.send_message("❌ هذا الزر ليس لك.", ephemeral=True)
            return

        channel = bot.get_channel(self.channel_id)
        if not channel:
            await interaction.response.send_message("❌ ما قدرت ألقى القناة.", ephemeral=True)
            return

        content = self.view.content
        text = content.get('text')
        attachments = content.get('attachments', [])

        try:
            if text:
                await channel.send(text)

            for attach in attachments:
                if attach.size > MAX_SIZE:
                    await interaction.response.send_message(f"❌ الملف `{attach.filename}` كبير جدًا!", ephemeral=True)
                    return
                await channel.send(file=await attach.to_file())

            await interaction.response.send_message(f"✅ تم إرسال المحتوى إلى {channel.mention}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ حدث خطأ أثناء الإرسال: {e}", ephemeral=True)

        user_states.pop(user_id, None)
        self.view.clear_items()
        await interaction.message.edit(view=self.view)
        self.view.stop()

@bot.command()
async def hi(ctx):
    # تحقق وجود رتبة admin (غير حساسة لحالة الأحرف)
    if "admin" not in [role.name.lower() for role in ctx.author.roles]:
        await ctx.send("❌ ما عندك صلاحية تستخدم هذا الأمر.")
        return

    user_states[ctx.author.id] = {'awaiting_content': True}
    await ctx.send("مرحباً! أرسل لي النص أو الصورة أو كلاهما الذي تريد إرساله، ثم سأطلب منك اختيار القناة.")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # جزء جديد: استقبال محتوى المستخدم بعد أمر !hi
    state = user_states.get(message.author.id)
    if state and state.get('awaiting_content', False):
        text = message.content if message.content else None
        attachments = message.attachments if message.attachments else []

        user_states[message.author.id]['content'] = {'text': text, 'attachments': attachments}
        user_states[message.author.id]['awaiting_content'] = False

        view = ChannelSelectView(message.author.id, user_states[message.author.id]['content'])
        await message.channel.send("🎯 اختر القناة التي تريد إرسال المحتوى إليها:", view=view)

    # جزء قديم: إرسال ملفات 2 فأكثر مع فيديو
    attachments = message.attachments
    if len(attachments) >= 2:
        has_video = any(a.filename.lower().endswith((".mp4", ".mov", ".avi", ".mkv")) for a in attachments)
        if has_video:
            view = ChannelSelectView(message.author.id, attachments)
            await message.channel.send("🎯 اختر القناة التي تريد إرسال الملفات إليها:", view=view)

    await bot.process_commands(message)
    
import os
bot.run(os.getenv("DISCORD_TOKEN"))