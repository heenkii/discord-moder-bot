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

    def is_admin_predicate(ctx)->bool:
        user_id = ctx.author.id
        server_id = ctx.guild.id
        return filters.is_admin(server_id=server_id, user_id=user_id)
        
    def server_is_active_predicate(ctx):
        server_id = ctx.guild.id
        return filters.server_is_active(server_id=server_id)
        
    def is_admin(): 
        return commands.check(predicate=bot_filters.is_admin_predicate)
    
    def server_is_active():
        return commands.check(predicate=bot_filters.server_is_active_predicate)

    def server_and_admin_filter()->bool:
        async def predicate(ctx):
            return await bot_filters.is_admin_predicate(ctx) and await bot_filters.server_is_active_predicate(ctx)
        return commands.check(predicate)