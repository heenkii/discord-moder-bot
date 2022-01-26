import sqlite3

from settings import config


class database:
    def __init__(self, server_id: int) -> None:
        self.db = sqlite3.connect(config["DB_FILE"])
        self.sql = self.db.cursor()

        self.table = f"server_{server_id}"

        self.sql.execute(
            f"""CREATE TABLE IF NOT EXISTS {self.table} (
            admins INT,
            log_channel INT,
            notification_channel INT,
            default_roles TEXT,
            roles TEXT,
            roles_message_channel INT,
            roles_message_id INT,
            server_state INT);
        """
        )

    def get_values(self, column_name) -> list:
        ans = self.sql.execute(
            f"SELECT {column_name} FROM {self.table} WHERE {column_name} IS NOT NULL"
        )
        values = list(map(lambda val: val[0], ans))
        return values

    # get all active servers
    def get_servers(self) -> list:
        ans = self.sql.execute(
            'SELECT name FROM sqlite_master WHERE type = "table"'
        ).fetchall()
        ans = [int(server_id[0].split("_")[1]) for server_id in ans]
        return ans

    # server_state
    def on_server(self) -> None:
        ans = self.get_server_state()
        if ans == False:
            self.sql.execute(
                f"UPDATE {self.table} SET server_state = 1 WHERE server_state = 0"
            )
            self.db.commit()

    def off_server(self) -> None:
        if self.get_server_state() == True:
            self.sql.execute(
                f"UPDATE {self.table} SET server_state = 0 WHERE server_state = 1"
            )
            self.db.commit()

    def get_server_state(self) -> bool:
        state = self.get_values("server_state")
        if len(state) == 0:
            self.sql.execute(f"INSERT INTO {self.table} (server_state) VALUES (1)")
            self.db.commit()
            return True
        else:
            if state[0] == 1:
                return True
            return False

    # admins
    def add_admin(self, user_id: int) -> None:
        if int(user_id) not in self.get_admins():
            self.sql.execute(f"INSERT INTO {self.table} (admins) VALUES ({user_id})")
            self.db.commit()

    def delete_admin(self, user_id: int) -> None:
        if int(user_id) in self.get_admins():
            self.sql.execute(f"DELETE FROM {self.table} WHERE admins = {user_id}")
            self.db.commit()

    def get_admins(self) -> list:
        return self.get_values("admins")

    # log_channel
    def add_log_channel(self, channel_id: int) -> None:
        if self.get_log_channel() != None:
            self.delete_log_channel()
        self.sql.execute(
            f"INSERT INTO {self.table} (log_channel) VALUES ({channel_id})"
        )
        self.db.commit()

    def delete_log_channel(self) -> None:
        channel_id = self.get_log_channel()
        if channel_id != None:
            self.sql.execute(
                f"DELETE FROM {self.table} WHERE log_channel = {channel_id}"
            )
            self.db.commit()

    def get_log_channel(self) -> int:
        channels = self.get_values("log_channel")
        if len(channels) == 1:
            return channels[0]
        return None

    # notification_channel
    def add_notification_channel(self, channel_id: int) -> None:
        if self.get_notification_channel() != None:
            self.delete_notification_channel()
        self.sql.execute(
            f"INSERT INTO {self.table} (notification_channel) VALUES ({channel_id})"
        )
        self.db.commit()

    def delete_notification_channel(self) -> None:
        channel_id = self.get_notification_channel()
        if channel_id != None:
            self.sql.execute(
                f"DELETE FROM {self.table} WHERE notification_channel = {channel_id}"
            )
            self.db.commit()

    def get_notification_channel(self) -> int:
        channels = self.get_values("notification_channel")
        if len(channels) == 1:
            return int(channels[0])
        return None

    def add_roles_data(self, channel_id, message_id) -> None:
        if self.get_roles_channel() != None or self.get_roles_message() != None:
            self.delete_roles_data()
        self.sql.execute(
            f"INSERT INTO {self.table} (roles_message_channel) VALUES ({channel_id})"
        )
        self.sql.execute(
            f"INSERT INTO {self.table} (roles_message_id) VALUES ({message_id})"
        )
        self.db.commit()

    def delete_roles_data(self) -> None:
        channel_id = self.get_roles_channel()
        message_id = self.get_roles_message()
        if channel_id != None:
            self.sql.execute(
                f"DELETE FROM {self.table} WHERE roles_message_channel = {channel_id}"
            )
        if message_id != None:
            self.sql.execute(
                f"DELETE FROM {self.table} WHERE roles_message_id = {message_id}"
            )
        self.db.commit()

    def get_roles_channel(self) -> int:
        channel_id = self.get_values("roles_message_channel")
        if len(channel_id) == 1:
            return channel_id[0]
        return None

    def get_roles_message(self) -> int:
        message_id = self.get_values("roles_message_id")
        if len(message_id) == 1:
            return message_id[0]
        return None

    # server_roles
    def add_role(self, role_name: str) -> None:
        if role_name not in self.get_roles():
            self.sql.execute(
                f"INSERT INTO {self.table} (roles) VALUES (?)", (role_name,)
            )
            self.db.commit()

    def delete_role(self, role_name: str) -> None:
        if role_name in self.get_roles():
            self.sql.execute(
                f"DELETE FROM {self.table} WHERE roles = (?)", (role_name,)
            )
            self.db.commit()

    def get_roles(self) -> int:
        return self.get_values("roles")

    # default roles
    def add_default_role(self, role_name) -> None:
        if role_name not in self.get_default_roles():
            self.sql.execute(
                f"INSERT INTO {self.table} (default_roles) VALUES (?)", (role_name,)
            )
            self.db.commit()

    def delete_default_role(self, role_name) -> None:
        if role_name in self.get_default_roles():
            self.sql.execute(
                f"DELETE FROM {self.table} WHERE default_roles = ?", (role_name,)
            )
            self.db.commit()

    def get_default_roles(self) -> list:
        return self.get_values("default_roles")

    def close(self):
        self.db.close()
