import discord, discord.utils, datetime
import webparser, settings

from sqlighter import database
from discord.ext import commands, tasks
from discord.ext.commands import CommandNotFound


intents = discord.Intents().all()
bot = commands.Bot(command_prefix=settings.config["PREFIX"], intents=intents)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        return
    raise error


@bot.event
async def on_ready()->None:
    print(f"{bot.user} has connected to Discord!")
    send_schedule.start()


@bot.event
async def on_guild_join(guild):
    db = database(guild.id)
    db.close_db()
    db.close()

#events loop

#send schedule infobez
@tasks.loop(seconds = 60)
async def send_schedule()->None:
    time_now = datetime.datetime.now()
    if int(time_now.hour) == 8 and int(time_now.minute) == 0:
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
            server_id = 883692688598261791 #infobez id
            db = database(server_id)
            notification_channel = db.get_notification_channel()
            db.close()
            if notification_channel != None:
                channel = bot.get_channel(id=notification_channel)
                await channel.send(message)


@bot.event
async def on_member_join(member)->None:
    server_id = member.guild.id
    db = database(server_id)
    default_roles = db.get_default_roles()
    if default_roles != []:
        for role_name in default_roles:
            try:
                role = discord.utils.get(member.guild.roles, name=role_name)
                await member.add_roles(role)
            except:
                continue
    date = datetime.datetime.now() #get dete and time
    log_channel = db.get_log_channel()
    if log_channel != None:
        channel = bot.get_channel(id=log_channel) #get log channel 
        await channel.send(f"{date.year}.{date.month}.{date.day} {date.hour}:{date.minute} | {member.name} join")
    db.close()


@bot.event
async def on_member_remove(member)->None:
    server_id = member.guild.id
    db = database(server_id)
    log_channel = db.get_log_channel()
    if log_channel != None:
        date = datetime.datetime.now()
        channel = bot.get_channel(id=log_channel)
        await channel.send(f"{date.year}.{date.month}.{date.day} {date.hour}:{date.minute} | {member.name} leave")
    db.close()


@bot.command(name="set_role_message")
async def set_role_message(ctx, argv="")->None:
    server_id = ctx.guild.id
    db = database(server_id)
    if ctx.author.id in db.get_admins() or ctx.author.id == int(settings.config["OWNER_ID"]):
        await ctx.message.delete()
        channel = bot.get_channel(id=ctx.message.channel.id)
        roles = db.get_roles()
        if roles != []:
            roles_lst = "\n- ".join(sorted(db.get_roles()))
            message = f'''
--------------------
 Добавить роль
--------------------
{settings.config["PREFIX"]}get_role 

------------------
 Удалить роль
------------------
{settings.config["PREFIX"]}delete_role 


- {roles_lst}
'''
            await ctx.send(message)
        else:
            await ctx.send(f"""Доступных ролей нету
--------------------
{settings.config["PREFIX"]}get_role [role_name] - добавить роль""")
    db.close()


@bot.command(name="get_role")
async def get_role(ctx, argv="")->None:
    role_name = ctx.message.content.split(maxsplit=1)[1].strip()
    db = database(ctx.guild.id)
    if role_name in db.get_roles():
        user_roles = [role.name for role in ctx.message.author.roles if role.name != "@everyone"]
        if role_name in user_roles:
            await ctx.reply("Роль уже добавлена")
        else:
            try:
                role = discord.utils.get(ctx.guild.roles, name=role_name)
                await ctx.author.add_roles(role)
                await ctx.reply(f"{ctx.author.name} добавил роль {role_name}")
            except:
                await ctx.reply("При добавлении роли произошла ошибка")
    elif role_name in db.get_default_roles():
        await ctx.reply("Это дефолтная роль")
    else:
        await ctx.reply("Такая роль не существует или ее нельзя добавить")
    db.close()


@bot.command(name="delete_role")
async def delete_role(ctx)->None:
    role_name = ctx.message.content.split(maxsplit=1)[1].strip()
    db = database(ctx.guild.id)
    user_roles = {role.name:role for role in ctx.message.author.roles if role.name != "@everyone"}
    if role_name in db.get_default_roles() or role_name not in db.get_roles():
        await ctx.reply("Эту роль невозможно удалить")
    elif role_name in user_roles:
        #delete role
        await ctx.author.remove_roles(user_roles[role_name])
        await ctx.reply(f"{ctx.author.name} удалил роль {role_name}")
    else:
        await ctx.reply("Такая роль не существует или не принадлежит вам")
    db.close()



#admin commands
@bot.command(name="add_role_for_users")
async def add_role_for_users(ctx)->None:
    db = database(ctx.guild.id)
    if ctx.author.id in db.get_admins() or ctx.author.id == int(settings.config["OWNER_ID"]):
        server_roles = [role.name for role in ctx.guild.roles if role.name != "@everyone"]
        role_name = ctx.message.content.split(maxsplit=1)[1].strip()
        await ctx.message.delete()
        if role_name not in db.get_roles() and role_name in server_roles:
            if role_name in db.get_default_roles():
                db.delete_default_role(role_name)
            db.add_role(role_name)
            await ctx.send(f"Добавлена роль {role_name}")
        elif role_name in db.get_roles():
            await ctx.send("Роль уже была добавлена")
        else:
            await ctx.send("Такой роли на сервере нет")
    db.close()


@bot.command(name="delete_role_for_users")
async def delete_role_for_users(ctx)->None:
    db = database(ctx.guild.id)
    if ctx.author.id in db.get_admins() or ctx.author.id == int(settings.config["OWNER_ID"]):
        server_roles = [role.name for role in ctx.guild.roles if role.name != "@everyone"]
        role_name = ctx.message.content.split(maxsplit=1)[1].strip()
        await ctx.message.delete()
        if role_name in db.get_roles() and role_name in server_roles:
            db.delete_role(role_name)
            await ctx.send(f"Удалена роль {role_name}")
        if role_name not in db.get_roles():
            await ctx.send("Роль и так не добавлена")
        else:
            await ctx.send("Такой роли на сервере нет")
    db.close()




@bot.command(name="add_default_role")
async def add_default_role(ctx)->None:
    db = database(ctx.guild.id)
    if ctx.author.id in db.get_admins() or ctx.author.id == int(settings.config["OWNER_ID"]):
        server_roles = [role.name for role in ctx.guild.roles if role.name != "@everyone"]
        role_name = ctx.message.content.split(maxsplit=1)[1].strip()
        await ctx.message.delete()
        if role_name not in db.get_default_roles() and role_name in server_roles:
            if role_name in db.get_roles():
                db.delete_role(role_name)
            db.add_default_role(role_name)
            await ctx.send(f"Добавлена базовая роль {role_name}")
        elif role_name in db.get_default_roles():
            await ctx.send("Базовая роль уже была добавлена")
        else:
            await ctx.send("Такой роли на сервере нет")
    db.close()


@bot.command(name="delete_default_role")
async def delete_default_role(ctx)->None:
    db = database(ctx.guild.id)
    if ctx.author.id in db.get_admins() or ctx.author.id == int(settings.config["OWNER_ID"]):
        server_roles = [role.name for role in ctx.guild.roles if role.name != "@everyone"]
        role_name = ctx.message.content.split(maxsplit=1)[1].strip()
        await ctx.message.delete()
        if role_name in db.get_default_roles() and role_name in server_roles:
            db.delete_role(role_name)
            await ctx.send(f"Удалена роль {role_name}")
        elif role_name not in db.get_default_roles():
            await ctx.send("Базовая роль и так не добавлена")
        else:
            await ctx.send("Такой роли на сервере нет")
    db.close()




@bot.command(name="set_log_channel")
async def set_log_channel(ctx)->None:
    db = database(ctx.guild.id)
    if ctx.author.id in db.get_admins() or ctx.author.id == int(settings.config["OWNER_ID"]):
        db.add_log_channel(ctx.channel.id)
        await ctx.send("Log канал установлен")
    db.close()


@bot.command(name="delete_log_channel")
async def delete_log_channel(ctx)->None:
    db = database(ctx.guild.id)
    if ctx.author.id in db.get_admins() or ctx.author.id == int(settings.config["OWNER_ID"]):
        db.delete_log_channel(ctx.channel.id)
        await ctx.send("Log канал удален")
    db.close()




@bot.command(name="set_notification_channel")
async def set_notification_channel(ctx)->None:
    db = database(ctx.guild.id)
    if ctx.author.id in db.get_admins() or ctx.author.id == int(settings.config["OWNER_ID"]):
        db.add_notification_channel(ctx.channel.id)
        await ctx.send("Канал для уведомлений установлен")
    db.close()


@bot.command(name="delete_notification_channel")
async def delete_log_channel(ctx)->None:
    db = database(ctx.guild.id)
    if ctx.author.id in db.get_admins() or ctx.author.id == int(settings.config["OWNER_ID"]):
        db.delete_notification_channel(ctx.channel.id)
        await ctx.send("Канал для уведомлений удален")
    db.close()




@bot.command(name="add_admin")
async def add_admin(ctx, user: discord.User)->None:
    db = database(ctx.guild.id)
    if ctx.author.id in db.get_admins() or ctx.author.id == int(settings.config["OWNER_ID"]):
        try:
            if user.id not in db.get_admins():
                db.add_admin(user.id)
                await ctx.send("Админ добавлен")
        except:
            await ctx.send("Ошибка")
    db.close()
    

@bot.command(name="delete_admin")
async def delete_admin(ctx, user: discord.User)->None:
    db = database(ctx.guild.id)
    if ctx.author.id in db.get_admins() or ctx.author.id == int(settings.config["OWNER_ID"]):
        try:
            if user.id in db.get_admins():
                db.delete_admin(user.id)
                await ctx.send("Админ удален")
        except:
            await ctx.send("Ошибка")
    db.close()



if __name__ == "__main__":
    token = settings.config["TOKEN"]
    bot.run(token)
    