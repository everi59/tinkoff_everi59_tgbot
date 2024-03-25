import asyncio
import logging
import psycopg2.errors

from aiogram import Router, F, Bot
from aiogram.utils.deep_linking import decode_payload, create_start_link
from aiogram.filters import CommandObject, CommandStart, Command, StateFilter, or_f, and_f
from aiogram.types import WebAppInfo, Message, CallbackQuery, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types.input_file import InputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from service.fsm_classes import FSMUserRegister
from service.placement import check_address, reverse_address
from service.service import check_name
from database.database import UsersDatabase
from lexicon.lexicon import lexicon
from keyboard.keyboard import create_inline_kb, keyboard_builder


users_database = UsersDatabase('UsersDatabase')
router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart(deep_link=True))
async def start_with_deeplink(message: Message, command: CommandObject, state: FSMContext):
    args = command.args
    payload = decode_payload(args)
    payload.strip('travel_')
    user_data = users_database.get_user(message.from_user.id)
    if user_data:
        await message.answer('Start text for deeplink')
    else:
        await message.answer(text='Start text with register for deeplink')


@router.message(CommandStart(deep_link=False))
async def start(message: Message, state: FSMContext):
    await state.set_state(FSMUserRegister.start_register)
    user_data = users_database.get_user(message.from_user.id)
    if user_data:
        await message.answer(text=lexicon['start'],
                             reply_markup=keyboard_builder(buttons=['Перейти в меню'], width=1, one_time_keyboard=True,
                                                           input_field_placeholder='Нажмите кнопку перехода в меню'))
    else:
        await message.answer(text=f'{lexicon["start"]}\n\n{lexicon["register"]}',
                             reply_markup=keyboard_builder(buttons=['Регистрация'], width=1, one_time_keyboard=True,
                                                           input_field_placeholder='Нажмите кнопку регистрации'))


# @router.message(lambda x: x.text.isdigit())
# async def one(message: Message, bot: Bot):
#     link = await create_start_link(bot, f'travel_{message.text}', encode=True)
#     await message.answer(text=f'Ссылка на ваше путешествие:\n{link}')


@router.message(F.text == 'Регистрация', StateFilter(FSMUserRegister.start_register))
@router.message(F.text == 'Заполнить профиль заново', StateFilter(FSMUserRegister.end_register))
@router.message(F.text == 'Изменить имя', StateFilter(FSMUserRegister.fill_age))
async def registration_start(message: Message, state: FSMContext):
    if message.text == 'Регистрация' or message.text == 'Заполнить профиль заново':
        await state.set_state(state=FSMUserRegister.fill_name)
        await message.answer(text='Введите ваше имя.',
                             reply_markup=keyboard_builder(buttons=['Использовать ник телеграмм'],
                                                           width=1,
                                                           one_time_keyboard=True,
                                                           input_field_placeholder='Введите имя или нажмите кнопку'))
    else:
        await state.set_state(state=FSMUserRegister.fill_name)
        data = await state.get_data()
        await state.update_data(fill_name=None)
        await message.answer(text='Введите ваше имя.',
                             reply_markup=keyboard_builder(
                                 buttons=[data['fill_name']],
                                 width=1,
                                 one_time_keyboard=True,
                                 input_field_placeholder='Введите имя или нажмите кнопку'
                             ))


@router.message(StateFilter(FSMUserRegister.fill_name))
@router.message(StateFilter(FSMUserRegister.fill_bio), F.text == 'Изменить возраст')
async def get_name(message: Message, state: FSMContext):
    if message.text:
        if message.text == 'Изменить возраст':
            data = await state.get_data()
            await state.update_data(fill_age=None)
            await state.set_state(FSMUserRegister.fill_age)
            await message.answer(text='Введите ваш возраст.\n<i>Диапазон: 13-120</i>',
                                 reply_markup=keyboard_builder(width=1,
                                                               buttons=[str(data['fill_age']), 'Изменить имя'],
                                                               one_time_keyboard=True,
                                                               input_field_placeholder='Введите возраст'
                                                                                       ' или нажмите кнопку'))
        elif message.text == 'Использовать ник телеграмм':
            if check_name(message.from_user.full_name):
                if users_database.user_exist(message.text):
                    await message.answer('Это имя уже занято!')
                else:
                    await state.update_data(fill_name=message.from_user.full_name)
                    await state.set_state(FSMUserRegister.fill_age)
                    await message.answer(text='Введите ваш возраст.\n<i>Диапазон: 13-120</i>',
                                         reply_markup=keyboard_builder(width=1, buttons=['Изменить имя'],
                                                                       one_time_keyboard=True,
                                                                       input_field_placeholder='Введите возраст'))
            else:
                await message.answer(text='Имя не может содержать символы или пробелы!'
                                          '\nДлинна имени должна быть от <b>2</b> до <b>30</b> символов!')
        elif check_name(message.text):
            if users_database.user_exist(message.text):
                await message.answer('Это имя уже занято!')
            else:
                await state.update_data(fill_name=message.text)
                await state.set_state(FSMUserRegister.fill_age)
                await message.answer(text='Введите ваш возраст.\n<i>Диапазон: 13-120</i>',
                                     reply_markup=keyboard_builder(width=1, buttons=['Изменить имя'],
                                                                   one_time_keyboard=True,
                                                                   input_field_placeholder='Введите возраст'))
        else:
            await message.answer(text='Имя не может содержать символы или пробелы!'
                                      '\nДлинна имени должна быть от <b>2</b> до <b>30</b> символов!')


@router.message(StateFilter(FSMUserRegister.fill_age))
@router.message(StateFilter(FSMUserRegister.fill_address), F.text == 'Изменить информацию о себе')
async def get_age(message: Message, state: FSMContext):
    if message.text == 'Изменить информацию о себе':
        await state.update_data(fill_bio=None)
        await state.set_state(FSMUserRegister.fill_bio)
        await message.answer(text='Введите информацию о себе или нажмите на кнопку пропустить',
                             reply_markup=keyboard_builder(
                                 buttons=['Взять информацию из профиля', 'Пропустить', 'Изменить возраст'],
                                 width=1,
                                 one_time_keyboard=True,
                                 input_field_placeholder='Введите информацию о себе или нажмите кнопку'
                             ))
    else:
        if all(i.isdigit() for i in message.text):
            age = int(message.text)
            if 12 < age < 121:
                await state.update_data(fill_age=age)
                await state.set_state(FSMUserRegister.fill_bio)
                await message.answer(text='Введите информацию о себе или нажмите на кнопку пропустить',
                                     reply_markup=keyboard_builder(
                                         buttons=['Взять информацию из профиля', 'Пропустить', 'Изменить возраст'],
                                         width=1,
                                         one_time_keyboard=True,
                                         input_field_placeholder='Введите информацию или нажмите кнопку'
                                     ))
            else:
                await message.answer(text='Возраст может быть от 13 до 120 лет!')
        else:
            await message.answer(text='Возраст должен состоять только из чисел!')


@router.message(StateFilter(FSMUserRegister.fill_bio))
@router.message(StateFilter(FSMUserRegister.end_register), F.text == 'Изменить адрес')
async def get_bio(message: Message, state: FSMContext, bot: Bot):
    if len(message.text) > 70:
        await message.answer('Длинна информации должна быть меньше 70 символов!')
    elif message.text == 'Изменить адрес':
        await state.update_data(fill_address=None)
        await state.set_state(FSMUserRegister.fill_address)
        markup = ReplyKeyboardBuilder()
        markup.row(*[KeyboardButton(text='Поделиться локацией', request_location=True),
                     KeyboardButton(text='Изменить информацию о себе')], width=1)
        await message.answer(text='Введи свое местоположение в формате:\n'
                                  '<i>Страна/Государство-Город/Деревня/Поселок</i>',
                             reply_markup=markup.as_markup(resize_keyboard=True,
                                                           one_time_keyboard=True,
                                                           input_field_placeholder='Введите местоположение'
                                                                                   ' или нажмите кнопку'))
    else:
        if message.text == 'Взять информацию из профиля':
            user_info = await bot.get_chat(message.from_user.id)
            await state.update_data(fill_bio=user_info.bio)
        elif message.text == 'Пропустить':
            await state.update_data(fill_bio='')
        else:
            await state.update_data(fill_bio=message.text)
        await state.set_state(FSMUserRegister.fill_address)
        markup = ReplyKeyboardBuilder()
        markup.row(*[KeyboardButton(text='Поделиться локацией', request_location=True),
                     KeyboardButton(text='Изменить информацию о себе')], width=1)
        await message.answer(text='Введи свое местоположение в формате:\n'
                             '<i>[Страна/Государство]</i>, <i>[Город/Деревня/Поселок]</i>, '
                                  '<i>[Улица]</i>, <i>[Дом]</i>\n'
                             'Пример: Россия, Москва, Пресненская набережная, 8с1',
                             reply_markup=markup.as_markup(resize_keyboard=True, one_time_keyboard=True,
                                                           input_field_placeholder='Введите местоположение'
                                                                                   ' или нажмите кнопку'))


@router.message(F.location, StateFilter(FSMUserRegister.fill_address))
async def get_reverse_address(message: Message, state: FSMContext):
    lat = message.location.latitude
    lon = message.location.longitude
    address_json = reverse_address(lat=str(lat), lon=str(lon))
    if address_json:
        await state.update_data(fill_address=address_json['display_name'])
        await state.update_data(fill_lat_lon=address_json['lat']+'_'+address_json['lon'])
        data = await state.get_data()
        await state.set_state(FSMUserRegister.end_register)
        await message.answer(text=('Вы заполнили свой профиль! Проверьте свои данные перед выходом в меню:\n' +
                                   lexicon['profile'] % (data['fill_name'], data['fill_age'],
                                                         data['fill_bio'], data['fill_address'])),
                             reply_markup=keyboard_builder(width=1,
                                                           buttons=['Изменить адрес', 'Перейти в меню',
                                                                    'Заполнить профиль заново'],
                                                           one_time_keyboard=True,
                                                           input_field_placeholder='Нажмите кнопку'
                                                           )
                             )
    else:
        await message.answer('Не получилось найти ваше местоположение!')


@router.message(StateFilter(FSMUserRegister.fill_address), F.text)
async def get_address(message: Message, state: FSMContext):
    plain_address = message.text.split(', ')
    if len(plain_address) >= 4:
        plain_address = ('+'.join(['+'.join(x.split()) for x in plain_address[:2]])
                         + f'+{plain_address[3]}/{plain_address[2]}')
        address_json = check_address(plain_address)
        if address_json and ((address_json[0]['address'].get('city') or address_json[0]['address'].get('town')
                              or address_json[0]['address'].get('village'))
                             and address_json[0]['address'].get('country')):
            address = address_json[0]['display_name']
            lat_lon = address_json[0]['lat']+'_'+address_json[0]['lon']
            await state.update_data(fill_address=address)
            await state.update_data(fill_lat_lon=lat_lon)
            data = await state.get_data()
            await state.set_state(FSMUserRegister.end_register)
            await message.answer(text=('Вы заполнили свой профиль!\nПроверьте свои данные перед выходом в меню:\n' +
                                       lexicon['profile'] % (data['fill_name'], data['fill_age'],
                                                             data['fill_bio'], data['fill_address'])),
                                 reply_markup=keyboard_builder(width=1,
                                                               buttons=['Перейти в меню',
                                                                        'Заполнить профиль заново',
                                                                        'Изменить адрес'],
                                                               one_time_keyboard=True,
                                                               input_field_placeholder='Нажмите кнопку')
                                 )
        else:
            await message.answer(text='Не получилось найти ваше местоположение.')
    else:
        await message.answer(text='Введите адрес по экземпляру в примере')


@router.message(StateFilter(FSMUserRegister.start_register), F.text == 'Перейти в меню')
@router.message(StateFilter(FSMUserRegister.end_register), F.text == 'Перейти в меню')
async def main_menu(message: Message, state: FSMContext):
    st = await state.get_state()
    if st == FSMUserRegister.end_register:
        data = await state.get_data()
        users_database.add_user(user_id=message.from_user.id, user_name=data['fill_name'],
                                user_address=data['fill_address'].replace("'", "/'"), user_age=data['fill_age'],
                                user_bio=data['fill_bio'].replace("'", "/'"), user_chat_id=message.chat.id,
                                user_lat_lon=data['fill_lat_lon'])
        await state.clear()
    await state.set_state(default_state)
    await message.answer(text=lexicon['menu'],
                         reply_markup=create_inline_kb(dct={'create_travel': 'Создать путешествие',
                                                            'view_travels': 'Посмотреть путешествия',
                                                            'view_profile': 'Посмотреть профиль',
                                                            'friends_list': 'Список друзей'},
                                                       width=2))
