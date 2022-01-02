from sqlighter import database
from settings import config
from discord.ext import commands

class filters:

    def is_admin():
        async def predicate(ctx)->bool:
            user_id = ctx.author.id
            server_id = ctx.guild.id
            db = database(server_id)
            admins = db.get_admins()
            db.close()
            check_user_id = user_id == config["OWNER_ID"] and config["OWNER_ID"] != None
            if check_user_id or user_id in admins:
                return True
            return False
        return commands.check(predicate)
    
    def server_is_active():
        async def predicate(ctx)->bool:
            server_id = ctx.guild.id
            db = database(server_id)
            server_state = db.get_server_state()
            if server_state == 1:
                return True
            return False
        return commands.check(predicate)