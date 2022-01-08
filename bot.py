import discord, discord.utils

from discord.activity import Game
from discord.ext import commands, tasks
from discord.ext.commands import CommandNotFound, CheckFailure
from datetime import datetime
from sqlighter import database
from settings import config
from bot_tools import bot_filters, bot_functions
from custom_loops import event_loops


intents = discord.Intents().all()
bot = commands.Bot(command_prefix=config["PREFIX"], intents=intents)


#error event
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound): #если это не вызов не существующей функции
        return

    if isinstance(error, CheckFailure): #если фильтр возвращает False
        return 
    
    print("\n---------------------------")
    print(datetime.now())
    raise error


#auto event
@bot.event
async def on_ready()->None:
    bot_game = config["BOT_GAME_NAME"]
    await bot.change_presence(activity=discord.Game(name=bot_game))
    print("\n----------------------------------------")
    print(datetime.now())
    print(f"{bot.user} has connected to Discord!")
    print("----------------------------------------\n")
    event_loops(bot=bot)


#auto event
@bot.event
async def on_guild_join(guild):
    db = database(guild.id)
    db.close()


#auto event
@bot.event
@bot_filters.server_is_active()
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


#auto event
@bot.event
@bot_filters.server_is_active()
async def on_member_remove(member)->None:
    server_id = member.guild.id
    db = database(server_id)
    log_channel = db.get_log_channel()
    if log_channel != None:
        date = datetime.datetime.now()
        channel = bot.get_channel(id=log_channel)
        await channel.send(f"{date.year}.{date.month}.{date.day} {date.hour}:{date.minute} | {member.name} leave")
    db.close()


#user event
@bot.command(name="get_role")
@bot_filters.server_is_active()
async def get_role(ctx)->None:
    role_name = ctx.message.content.split(maxsplit=1)
    if len(role_name) > 1:
        role_name = role_name[1].strip()
    else:
        role_name = " "
    server_id = ctx.guild.id
    db = database(server_id=server_id)
    server_roles = []
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

#user event
@bot.command(name="delete_role")
@bot_filters.server_is_active()
async def delete_role(ctx)->None:
    await ctx.message.delete()
    role_name = ctx.message.content.split(maxsplit=1)[1].strip()
    server_id = ctx.guild.id
    db = database(server_id=server_id)
    user_roles = {role.name:role for role in ctx.message.author.roles if role.name != "@everyone"}
    if role_name in db.get_default_roles() or role_name not in db.get_roles():
        await ctx.reply("Эту роль невозможно удалить")
    elif role_name in user_roles:
        #delete role
        try:
            await ctx.author.remove_roles(user_roles[role_name])
            await ctx.reply(f"{ctx.author.name} удалил роль {role_name}")
        except:
            await ctx.reply("При удалении роли произошла ошибка")
    else:
        await ctx.reply("Такая роль не существует или не принадлежит вам")
    db.close()


@bot.command(name="set_roles_message")
@bot_filters.server_and_admin_filter()
async def set_roles_message(ctx)->None: #в канале создается изменяемое сообщение и обрабатываются только команды добавленя ролей написанные в нем
    await ctx.message.delete()
    server_id = ctx.guild.id
    channel_id = ctx.channel.id
    db = database(server_id=server_id)
    channel = bot.get_channel(id=channel_id)
    roles = db.get_roles()
    if roles != []:
        roles_lst = "\n- ".join(sorted(roles))
        text_message = f'''
--------------------
 Добавить роль   {config["PREFIX"]}get_role 
--------------------
 Удалить роль   {config["PREFIX"]}delete_role 
--------------------

- {roles_lst}
'''
    else:
        text_message = f"""Доступных ролей нету
--------------------
{config["PREFIX"]}get_role [role_name] - добавить роль"""
    message = await ctx.send(text_message)
    message_id = message.id
    db.add_roles_data(message_id=message_id, channel_id=channel_id)
    db.close()

#admin command
@bot.command(name="delete_roles_message")
@bot_filters.server_and_admin_filter()
async def delete_roles_message(ctx)->None:
    server_id = ctx.guild.id
    db = database(server_id=server_id)
    message_id = db.get_roles_message()
    if message_id != None:
        db.delete_roles_data()
    db.close()

@bot.command(name="update_roles_message")
@bot_filters.server_and_admin_filter()
async def update_roles_message(ctx)->None:
    await ctx.message.delete()
    await bot_functions.update_roles_message(bot=bot, ctx=ctx)


#admin commands
@bot.command(name="add_role_for_users")
@bot_filters.server_and_admin_filter()
async def add_role_for_users(ctx)->None:
    await ctx.message.delete()
    server_id = ctx.guild.id
    db = database(server_id=server_id)
    server_roles = [role.name for role in ctx.guild.roles if role.name != "@everyone"]
    role_name = ctx.message.content.split(maxsplit=1)[1].strip()
    if role_name not in db.get_roles() and role_name in server_roles:
        if role_name in db.get_default_roles():
            db.delete_default_role(role_name)
        await ctx.send(f"Добавлена роль {role_name}")
        db.add_role(role_name=role_name)
        await bot_functions.update_roles_message(bot=bot, ctx=ctx)
    elif role_name in db.get_roles():
        await ctx.send("Роль уже была добавлена")
    else:
        await ctx.send("Такой роли на сервере нет")
    db.close()

#admin event
@bot.command(name="delete_role_for_users")
@bot_filters.server_and_admin_filter()
async def delete_role_for_users(ctx)->None:
    await ctx.message.delete()
    server_id = ctx.guild.id
    db = database(server_id=server_id)
    server_roles = [role.name for role in ctx.guild.roles if role.name != "@everyone"]
    role_name = ctx.message.content.split(maxsplit=1)[1].strip()
    if role_name in db.get_roles() and role_name in server_roles:
        db.delete_role(role_name)
        await ctx.send(f"Удалена роль {role_name}")
        await bot_functions.update_roles_message(bot=bot, ctx=ctx)
    elif role_name not in db.get_roles():
        await ctx.send("Роль и так не добавлена")
    else:
        await ctx.send("Такой роли на сервере нет")
    db.close()


#admin event
@bot.command(name="add_default_role")
@bot_filters.server_and_admin_filter()
async def add_default_role(ctx)->None:
    await ctx.message.delete()
    server_id = ctx.guild.id
    db = database(server_id=server_id)
    server_roles = [role.name for role in ctx.guild.roles if role.name != "@everyone"]
    role_name = ctx.message.content.split(maxsplit=1)[1].strip()
    if role_name not in db.get_default_roles() and role_name in server_roles:
        if role_name in db.get_roles():
            db.delete_role(role_name)
            await bot_functions.update_roles_message(bot=bot, ctx=ctx)
        db.add_default_role(role_name)
        await ctx.send(f"Добавлена базовая роль {role_name}")
    elif role_name in db.get_default_roles():
        await ctx.send("Базовая роль уже была добавлена")
    else:
        await ctx.send("Такой роли на сервере нет")
    db.close()

#admin event
@bot.command(name="delete_default_role")
@bot_filters.server_and_admin_filter()
async def delete_default_role(ctx)->None:
    await ctx.message.delete()
    server_id = ctx.guild.id
    db = database(server_id=server_id)
    server_roles = [role.name for role in ctx.guild.roles if role.name != "@everyone"]
    role_name = ctx.message.content.split(maxsplit=1)[1].strip()
    if role_name in db.get_default_roles() and role_name in server_roles:
        db.delete_role(role_name)
        await ctx.send(f"Удалена роль {role_name}")
    elif role_name not in db.get_default_roles():
        await ctx.send("Базовая роль и так не добавлена")
    else:
        await ctx.send("Такой роли на сервере нет")
    db.close()


#admin_event
@bot.command(name="set_log_channel")
@bot_filters.server_and_admin_filter()
async def set_log_channel(ctx)->None:
    await ctx.message.delete()
    server_id = ctx.guild.id
    db = database(server_id=server_id)
    db.add_log_channel(ctx.channel.id)
    await ctx.send("Log канал установлен")
    db.close()

#admin event
@bot.command(name="delete_log_channel")
@bot_filters.server_and_admin_filter()
async def delete_log_channel(ctx)->None:
    await ctx.message.delete()
    server_id = ctx.guild.id
    db = database(server_id=server_id)
    db.delete_log_channel()
    await ctx.send("Log канал удален")
    db.close()


#admin event
@bot.command(name="set_notification_channel")
@bot_filters.server_and_admin_filter()
async def set_notification_channel(ctx)->None:
    await ctx.message.delete()
    server_id = ctx.guild.id
    db = database(server_id=server_id)
    db.add_notification_channel(ctx.channel.id)
    await ctx.send("Канал для уведомлений установлен")
    db.close()

#admin event
@bot.command(name="delete_notification_channel")
@bot_filters.server_and_admin_filter()
async def delete_notification_channel(ctx)->None:
    await ctx.message.delete()
    db = database(ctx.guild.id)
    db.delete_notification_channel(ctx.channel.id)
    await ctx.send("Канал для уведомлений удален")
    db.close()


#admin event
@bot.command(name="add_admin")
@bot_filters.server_and_admin_filter()
async def add_admin(ctx, user: discord.User)->None:
    try:
        await ctx.message.delete()
        server_id = ctx.guild.id
        db = database(server_id=server_id)
        if user.id not in db.get_admins():
            db.add_admin(user.id)
            await ctx.send(f"Админ {ctx.author.name} добавлен")
        else:
            await ctx.send(f"{ctx.author.name} уже является администратором")
    except:
        await ctx.send(f"Ошибка при добавлении админа {ctx.author.name}")
    db.close()
    
#admin event
@bot.command(name="delete_admin")
@bot_filters.server_and_admin_filter()
async def delete_admin(ctx, user: discord.User)->None:
    try:
        await ctx.message.delete()
        server_id = ctx.guild.id
        db = database(server_id=server_id)
        if user.id in db.get_admins():
            db.delete_admin(user.id)
            await ctx.send(f"Админ {ctx.author.name} удален")
        else:
            await ctx.send(f"{ctx.author.name} не является администратором")
    except:
        await ctx.send(f"Ошибка при удалении админа {ctx.author.name}")
    db.close()


@bot.command(name="on_server")
@bot_filters.is_admin()
async def on_server(ctx):
    await ctx.message.delete()
    if bot_filters.server_is_active_predicate(ctx) == False:
        server_id = ctx.guild.id
        db = database(server_id)
        await ctx.send("Сервер включен")
        db.close()
    else:
        await ctx.send("Сервер уже включен")

@bot.command(name="off_server")
@bot_filters.is_admin()
async def off_server(ctx):
    await ctx.message.delete()
    if bot_filters.server_is_active_predicate(ctx) == True:
        server_id = ctx.guild.id
        db = database(server_id)
        await ctx.send("Сервер выключен")
        db.close()
    else:
        await ctx.send("Сервер уже выключен")


#run bot
if __name__ == "__main__":
    bot.run(config["TOKEN"])