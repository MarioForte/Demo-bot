import sqlite3

class BotDB:

    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()

    def user_exists(self, user_id, peer_id):
        """Проверяем, есть ли юзер в базе"""
        result = self.cursor.execute("SELECT rowid FROM users WHERE user_id = ? AND peer_id = ?", (user_id, peer_id))
        return bool(len(result.fetchall()))

    def get_users_nicks(self, peer_id):
        """Достаем id юзера в базе по его user_id"""
        result = self.cursor.execute("SELECT user_id, name FROM users WHERE peer_id = ?", (peer_id,))
        return result.fetchall()

    def add_user(self, user_id, peer_id, name):
        """Добавляем юзера в базу"""
        self.cursor.execute("INSERT INTO `users` (`user_id`, 'peer_id', 'name') VALUES (?, ?, ?)", (user_id, peer_id, name))
        return self.conn.commit()

    def update_user(self, user_id, name, peer_id):
        """Обновляем юзера в базе"""
        self.cursor.execute("UPDATE users SET name = ? WHERE user_id = ? AND peer_id = ?", (name, user_id, peer_id))
        return self.conn.commit()

    def get_name(self, user_id, peer_id):
        """Получаем имя юзера"""
        result = self.cursor.execute("SELECT name FROM users WHERE user_id = ? AND peer_id = ?", (user_id, peer_id))
        return result.fetchone()[0]

    def close(self):
        """Закрываем соединение с БД"""
        self.connection.close()