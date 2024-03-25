from dataclasses import dataclass
from environs import Env


@dataclass
class Bot:
    token: str


@dataclass
class Database:
    name: str
    host: str
    user: str
    password: str
    port: str


@dataclass
class Config:
    bot: Bot
    database: Database


def load_config(path: str | None = None) -> Config:
    env = Env()
    env.read_env(path)
    return Config(bot=Bot(token=env('BOT_TOKEN')),
                  database=Database(name=env('DATABASE_NAME'), host=env('DATABASE_HOST'),
                                    user=env('DATABASE_USER'), password=env('DATABASE_PASSWORD'),
                                    port=env('DATABASE_PORT')))
