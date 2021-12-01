import sqlite3
import settings


class database:

    def __init__(self, server_id:int)->None:
        self.db = sqlite3.connect(settings.config["DB_FILE"]) 
        self.sql = self.db.cursor()

        self.table = f"server_{server_id}"
        self.server_id = server_id
        
        self.sql.execute(f"""CREATE TABLE IF NOT EXISTS {self.table} (
            admins INT,
            log_channel INT,
            notification_channel INT,
            default_roles TEXT,
            roles TEXT);
        """)


    def get_values(self, tab)->list[int]:
        values = [val[0] for val in self.sql.execute(f"SELECT {tab} FROM {self.table}") if val[0] != None]
        return values


    #get all active servers
    def get_servers(self)->list[int]:
        ans = self.sql.execute('SELECT name FROM sqlite_master WHERE type = "table"').fetchall()
        ans = [int(server_id[0].split("_")[1]) for server_id in ans]
        return ans

    
    #admin
    def add_admin(self, user_id:int)->None:
        if int(user_id) not in self.get_admins():
            self.sql.execute(f"INSERT INTO {self.table} (admins) VALUES (?)", (user_id, ))
            self.db.commit()

    def delete_admin(self, user_id:int)->None:
        if int(user_id) in self.get_admins():
            self.sql.execute(f"DELETE FROM {self.table} WHERE admins = ?", (user_id, ))
            self.db.commit()

    def get_admins(self)->list[int]:
        return self.get_values("admins")


    #add log channel
    def add_log_channel(self, channel_id:int)->None:
        if self.get_log_channel() != None:
            self.delete_log_channel()
        self.sql.execute(f"INSERT INTO {self.table} (log_channel) VALUES (?)", (channel_id, ))
        self.db.commit()

    def delete_log_channel(self)->None:
        channel_id = self.get_log_channel()
        if channel_id != None:
            self.sql.execute(f"DELETE FROM {self.table} WHERE log_channel = ?", (channel_id, ))
            self.db.commit()

    def get_log_channel(self):
        channels = self.get_values("log_channel")
        if len(channels) == 1:
            return channels[0]
        return None

    
    def add_notification_channel(self, channel_id:int)->None:
        if self.get_notification_channel() != None:
            self.delete_notification_channel()
        self.sql.execute(f"INSERT INTO {self.table} (notification_channel) VALUES (?)", (channel_id, ))
        self.db.commit()

    def delete_notification_channel(self)->None:
        channel_id = self.get_notification_channel()
        if channel_id != None:
            self.sql.execute(f"DELETE FROM {self.table} WHERE notification_channel = ?", (channel_id))
            self.db.commit()

    def get_notification_channel(self)->int:
        channels = self.get_values("notification_channel")
        if len(channels) == 1:
            return int(channels[0])
        return None


    def add_role(self, role_name:str)->None:
        if role_name not in self.get_roles():
            self.sql.execute(f"INSERT INTO {self.table} (roles) VALUES (?)", (role_name, ))
            self.db.commit()

    def delete_role(self, role_name:str)->None:
        if role_name in self.get_roles():
            self.sql.execute(f"DELETE FROM {self.table} WHERE roles = ?", (role_name, ))
            self.db.commit()

    def get_roles(self):
        return self.get_values("roles")


    def add_default_role(self, role_name)->None:
        if role_name not in self.get_default_roles():
            self.sql.execute(f"INSERT INTO {self.table} (default_roles) VALUES (?)", (role_name, ))
            self.db.commit()

    def delete_default_role(self, role_name):
        if role_name in self.get_default_roles():
            self.sql.execute(f"DELETE FROM {self.table} WHERE default_roles = ?", (role_name, ))
            self.db.commit()

    def get_default_roles(self):
        return self.get_values("default_roles")


    def close(self):
        self.db.close()