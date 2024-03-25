import psycopg2
import logging

from config.config import load_config

conn_settings = load_config()

conn = psycopg2.connect(host='localhost', dbname='postgres', user='postgres', password='1234', port=5432)

logger = logging.getLogger(__name__)


class UsersDatabase:
    def __init__(self, name):
        self.name = name

    async def create_table(self):
        cur = conn.cursor()
        cur.execute(f"""CREATE TABLE IF NOT EXISTS {self.name}
            (user_id BIGINT PRIMARY KEY,
            user_chat_id BIGINT,
            user_name TEXT,
            user_age INT,
            user_bio TEXT,
            user_address TEXT,
            user_lat_lon TEXT);""")
        conn.commit()
        cur.close()
        logger.info('[INFO] THE TABLE WAS CREATED SUCCESSFULLY')

    def add_user(self, user_id: int, user_chat_id: int, user_name: str, user_age: int, user_bio: str,
                 user_address: str, user_lat_lon: str):
        cur = conn.cursor()
        cur.execute(f"""INSERT INTO {self.name} (user_id, user_chat_id, user_name,
         user_age, user_bio, user_address, user_lat_lon)
         VALUES ({user_id}, {user_chat_id}, '{user_name}', {user_age}, '{user_bio}', '{user_address}', 
         '{user_lat_lon}')""")
        conn.commit()
        cur.close()
        logger.info('[INFO] THE USER WAS ADDED SUCCESSFULLY')

    def get_user(self, user_id: int):
        cur = conn.cursor()
        cur.execute(f"""SELECT * FROM {self.name} WHERE user_id={user_id}""")
        conn.commit()
        user_data = cur.fetchone()
        cur.close()
        logger.info("[INFO] THE USER WAS SELECTED SUCCESSFULLY")
        return user_data if user_data else False

    def update_user(self, user_id: int, user_name: str, user_age: int, user_bio: str,
                    user_address: str, user_lat_lon: str):
        cur = conn.cursor()
        cur.execute(f"""UPDATE {self.name} SET (user_name='{user_name}', user_age={user_age}, user_bio='{user_bio}',
         user_address='{user_address}', user_city='{user_city}', user_lat_lon='{user_lat_lon}') WHERE user_id={user_id}""")
        conn.commit()
        cur.close()
        logger.info('[INFO] THE USER WAS UPDATED SUCCESSFULLY')

    def user_exist(self, user_name: str):
        cur = conn.cursor()
        cur.execute(f"""SELECT * FROM {self.name} WHERE user_name='{user_name}'""")
        exist_name = cur.fetchone()
        conn.commit()
        cur.close()
        logger.info("[INFO] THE USER WAS SELECTED SUCCESSFULLY")
        return True if exist_name else False

    def get_user_place(self, user_id: int):
        cur = conn.cursor()
        cur.execute(f"""SELECT user_lat_lon, user_address FROM {self.name} WHERE user_id={user_id}""")
        place = cur.fetchone()
        conn.commit()
        cur.close()
        place_dict = {'lat': float(place[0].split('_')[0]),
                      'lon': float(place[0].split('_')[1]),
                      'name': place[1]}
        return place_dict
