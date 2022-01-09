from sqlighter import database
from settings import config
from discord.ext import commands


class filters:

    def server_is_active(server_id:int)->bool:
        db = database(server_id)
        server_state = db.get_server_state()
        db.close()
        if server_state == 1:
            return True
        return False

    def is_admin(server_id:int, user_id:int)->bool:
        db = database(server_id)
        admins = db.get_admins()
        db.close()
        check_user_id = user_id == config["OWNER_ID"] and config["OWNER_ID"] != None
        if check_user_id or user_id in admins:
            return True
        return False


class bot_filters(filters):
    
    async def is_admin_predicate(ctx)->bool:
        user_id = ctx.author.id
        server_id = ctx.guild.id
        return filters.is_admin(server_id=server_id, user_id=user_id)
        
    async def server_is_active_predicate(ctx)->bool:
        server_id = ctx.guild.id
        return filters.server_is_active(server_id=server_id)
        
    def is_admin(): 
        return commands.check(predicate=bot_filters.is_admin_predicate)
    
    def server_is_active():
        return commands.check(predicate=bot_filters.server_is_active_predicate)

    def server_and_admin_filter()->bool:
        async def predicate(ctx):
            return await bot_filters.is_admin_predicate(ctx) and await bot_filters.server_is_active_predicate(ctx)
        return commands.check(predicate=predicate)



class bot_functions:

    async def get_server_roles(ctx)->list:
        server_roles = [role.name for role in ctx.guild.roles if role.name != "@everyone"]
        return server_roles
    
    
    async def get_user_roles(ctx)->list:
        user_roles = [role.name for role in ctx.message.author.roles if role.name != "@everyone"]
        return user_roles

    
    async def update_roles_message(bot, ctx):
        server_id = ctx.guild.id
        db = database(server_id)
        roles_message_id = db.get_roles_message()
        if roles_message_id != None:
            roles = db.get_roles()
            server_roles = [role.name for role in ctx.guild.roles if role.name != "@everyone"]
            for role in roles:
                if role not in server_roles:
                    db.delete_role(role) #delete role if role not in server
            try:
                channel_id = db.get_roles_channel()
                channel = bot.get_channel(channel_id)
                if channel != None:
                    message = await channel.fetch_message(roles_message_id)
                    if message != None:
                        roles_lst = "\n- ".join(sorted(roles))
                        if roles_lst != []:
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
                        await message.edit(content=text_message)
            except:
                await ctx.send("Команда введена не в канале с сообщением или сообщение было удалено")
        else:
            await ctx.send("Не установлено сообщение с ролями")
        db.close()