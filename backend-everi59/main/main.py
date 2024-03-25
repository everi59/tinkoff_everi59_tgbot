import asyncio
import logging

# from database.database import Database
import uvicorn
from aiogram import Bot, Dispatcher
from config.config import load_config, Config
from handlers import user_handlers, travel_handlers, other_handlers
# from services.services import set_menu_commands

logger = logging.getLogger(__name__)


async def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(filename)s:%(lineno)d #%(levelname)-8s '
                               '[%(asctime)s] - %(name)s - %(message)s')
    logger.info('Starting bot')

    config: Config = load_config()

    await user_handlers.users_database.create_table()

    bot = Bot(token=config.bot.token,
              parse_mode='HTML')

    dp = Dispatcher()
    # await set_menu_commands(bot)

    dp.include_router(user_handlers.router)
    dp.include_router(travel_handlers.router)
    # dp.include_router(other_handlers.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
