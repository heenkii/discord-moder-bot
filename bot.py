import discord, settings, discord.utils, datetime, webparser
from discord.ext import commands, tasks


intents = discord.Intents().all()
bot = commands.Bot(command_prefix=settings.config["PREFIX"], intents=intents)


schedule = []


@bot.event
async def on_ready()->None:
    print(f"{bot.user} has connected to Discord!")
    send_schedule.start()


#send schedule infobez
@tasks.loop(seconds = 60)
async def send_schedule()->None:
    time_now = datetime.datetime.now()
    if int(time_now.hour) == 8 and int(time_now.minute) == 0:
        global schedule
        schedule = webparser.get_data()
        data = schedule[0]
        date = data[0]["date"].split(".")
        if int(date[0]) == time_now.day and int(date[1]) == time_now.month:
            schedule_day = []
            for unit in data[1:]:
                lesson = unit["lesson"]
                tutor = unit["tutor"]
                time = unit["time"]
                location = unit["location"]
                lesson_type = unit["type"]
                schedule_day += [" ".join([lesson, tutor, time, location, lesson_type])]
            message = f'Расписание на {data[0]["date"]}, {data[0]["week_day"]}:' + "\n -- " + "\n -- ".join(schedule_day)
            server_id = settings.config["INFOBEZ"]
            channel = bot.get_channel(id=settings.config[server_id]["SCHEDULE_CHANEL_ID"])
            await channel.send(message)


@bot.event
async def on_member_join(ctx)->None:
    server_id = ctx.guild.id
    if server_id in settings.config:
        for role_name in settings.config[server_id]["DEFAULT_ROLES"]:
            try:
                role = discord.utils.get(ctx.guild.roles, name=role_name)
                await ctx.add_roles(role)
            except:
                continue
        date = datetime.datetime.now() #get dete and time
        channel = bot.get_channel(id=settings.config[server_id]["LOG_CHANNEL"]) #get log channel 
        await channel.send(f"{date.year}.{date.month}.{date.day} {date.hour}:{date.minute}  {ctx.name} join")


@bot.event
async def on_member_remove(member)->None:
    server_id = member.guild.id
    if server_id in settings.config:
        log_channel = settings.config[server_id]["LOG_CHANNEL"]
        date = datetime.datetime.now()
        channel = bot.get_channel(id=log_channel)
        await channel.send(f"{date.year}.{date.month}.{date.day} {date.hour}:{date.minute}  {member.name} leave")


@bot.command(name="set_role_message")
async def set_role_message(ctx, argv="")->None:
    server_id = ctx.guild.id
    if ctx.author.id in settings.config[server_id]["ADMINS"] or ctx.author.id == settings.config["OWNER_ID"]:
        await ctx.message.delete()
        channel = bot.get_channel(id=ctx.message.channel.id)
        if len(settings.config[server_id]["ROLES"]) > 0:
            roles_lst = "\n- ".join(settings.config[server_id]["ROLES"])
            message = f'''
--------------------
 Добавить роль
--------------------
!get_role 
- {roles_lst}

------------------
 Удалить роль
------------------
!delete_role 
- {roles_lst}
'''
            await channel.send(message)
        else:
            await channel.send("Нету доступных ролей")


@bot.command(name="get_role")
async def get_role(ctx, argv="")->None:
    user_roles = [role.name for role in ctx.guild.roles]
    text = ctx.message.content.split(maxsplit=1)[1]
    try:
        role_name = argv.strip()
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        await ctx.author.add_roles(role)
        channel = bot.get_channel(ctx.channel.id)
        await channel.send(f"{ctx.author.name} добавил роль {text}")
    except:
        await ctx.reply("Такой роли на сервере не существует")


@bot.command(name="delete_role")
async def delete_role(ctx, argv="")->None:
    user_roles = {role.name:role for role in ctx.guild.roles} #all user roles
    role = argv.strip()
    default_roles = settings.config[ctx.guild.id]["DEFAULT_ROLES"]
    if user_roles in default_roles:
        await ctx.send("Эту роль невозможно удалить")
    elif role in user_roles:
        #delete role
        await ctx.author.remove_roles(user_roles[role])
        channel = bot.get_channel(ctx.channel.id)
        await channel.send(f"{ctx.author.name} удалил роль {role}")
    else:
        await ctx.send("Такая роль не существует")


if __name__ == "__main__":
    token = settings.config["TOKEN"]
    bot.run(token)
