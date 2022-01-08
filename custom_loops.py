from discord.ext import tasks, commands
from bot_tools import filters
from sqlighter import database
from datetime import datetime
from bot_tools import bot_filters
from webparser import get_schedule


class event_loops(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.send_schedule.start()

    def check_time(self, hour:int, minute:int):
        time_now = datetime.now()
        time_is_correct = int(time_now.hour) == hour and int(time_now.minute) == minute
        return time_is_correct
    
    @tasks.loop(seconds = 60)
    async def send_schedule(self)->None:
        time_now = datetime.now()
        time_is_correct = int(time_now.hour) == 8 and int(time_now.minute) == 0
        server_id = 883692688598261791 #infobez id
        server_is_active = filters.server_is_active(server_id)
        db = database(server_id)
        notification_channel = db.get_notification_channel()
        if time_is_correct and server_is_active and notification_channel != None:
            schedule = get_schedule()
            if len(schedule) > 0:
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
                    channel = self.bot.get_channel(id=notification_channel)
                    await channel.send(message)
        db.close()
