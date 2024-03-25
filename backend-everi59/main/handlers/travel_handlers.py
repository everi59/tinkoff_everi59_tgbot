from aiogram.types import (CallbackQuery, Message, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup,
                           ReplyKeyboardRemove)
from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from service.fsm_classes import FSMCreateTravel
from service.placement import reverse_address, url_web_example, check_address
from keyboard.keyboard import create_inline_kb, keyboard_builder
from database.database import UsersDatabase
import logging

users_database = UsersDatabase('UsersDatabase')
router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == 'create_travel')
async def user_create_travel(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FSMCreateTravel.creating_travel)
    await callback.message.edit_text(text='Выберите тип маршрута',
                                     reply_markup=create_inline_kb(lst=['hike', 'car', 'bike', 'back']))


@router.callback_query(lambda x: x.data in ['hike', 'car', 'bike'])
async def get_points(callback: CallbackQuery, state: FSMContext):
    await state.update_data(route_type=callback.data)
    user_place = users_database.get_user_place(user_id=callback.from_user.id)
    await state.update_data(fill_points=[user_place])
    await state.set_state(FSMCreateTravel.fill_points)
    await callback.message.edit_text(text='Отлично!\n'
                                          'Теперь отправляй мне точки, в которые ты планируешь отправиться.\n'
                                          'Начинай с точки, в которую ты бы хотел попасть в <b>первую</b> очередь.\n'
                                          'Последняя отправленная тобой точка является <b>финишем</b> путешествия.\n'
                                          'Максимальное количество точек - <b>6</b>.\n\n'
                                          'Доступные форматы ввода точек:\n'
                                          '1. Адрес (по экземпляру как в регистрации) или название места.\n'
                                          '2. Геолокация телеграмм. (скрепка - геопозиция - отправить геопозицию).\n'
                                          '3. Координаты вида: lat, lon.\n'
                                          'Пожалуйста, убедитесь, что к вашему месту возможно добраться, иначе'
                                          ' маршрут может не построиться!')
    await callback.answer('Список ваших точек:\n'
                          'Еще нет добавленных точек!')


@router.message(F.location, StateFilter(FSMCreateTravel.fill_points))
async def get_points_by_location(message: Message, state: FSMContext):
    lat = message.location.latitude
    lon = message.location.longitude
    data = await state.get_data()
    address_json = reverse_address(lat=str(lat), lon=str(lon))
    if address_json:
        data['fill_points'].append({'lat': lat, 'lon': lon, 'name': address_json['display_name']})
        url = url_web_example % data['route_type']
        await state.update_data(data=data)
        points = data['fill_points']
        text = ('Точка была добавлена!\n'
                'Список ваших точек:')
        url_points = ''
        counter = 1
        for point in points:
            text += f'\n{counter}. {point["name"][:25]}...'
            url_points += f"&point={point['lat']}%2C{point['lon']}"
        button = InlineKeyboardButton(text='Просмотреть маршрут', web_app=WebAppInfo(url=url+url_points))
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])
        await message.answer(text=text, reply_markup=keyboard)
    else:
        await message.answer('Не получилось найти указанную точку')


@router.message(F.text)
async def get_point(message: Message, state: FSMContext):
    if any([i.isalpha() for i in message.text]):
        lat_lon = message.text.split(', ')
        if len(lat_lon) != 2:
            await message.answer('Некорректные адрес или координаты')
        else:
            lat = lat_lon[0]
            lon = lat_lon[1]
            data = await state.get_data()
            address_json = reverse_address(lat=str(lat), lon=str(lon))
            if address_json:
                data['fill_points'].append({'lat': lat, 'lon': lon, 'name': address_json['display_name']})
                url = url_web_example % data['route_type']
                await state.update_data(data=data)
                points = data['fill_points']
                text = ('Точка была добавлена!\n'
                        'Список ваших точек:')
                url_points = ''
                counter = 1
                for point in points:
                    text += f'\n{counter}. {point["name"][:25]}...'
                    url_points += f"&point={point['lat']}%2C{point['lon']}"
                button = InlineKeyboardButton(text='Просмотреть маршрут', web_app=WebAppInfo(url=url + url_points))
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])
                await message.answer(text=text, reply_markup=keyboard)
            else:
                await message.answer('Не получилось найти указанную точку')
    else:
        plain_address = message.text.split(', ')
        if len(plain_address) >= 4:
            plain_address = ('+'.join(['+'.join(x.split()) for x in plain_address[:2]])
                             + f'+{plain_address[3]}/{plain_address[2]}')
            address_json = check_address(plain_address)
            if address_json and ((address_json[0]['address'].get('city') or address_json[0]['address'].get('town')
                                  or address_json[0]['address'].get('village'))
                                 and address_json[0]['address'].get('country')):
                address = address_json[0]['display_name']
                lat_lon = address_json[0]['lat'] + '_' + address_json[0]['lon']
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
