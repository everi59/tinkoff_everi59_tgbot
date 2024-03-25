from aiogram.fsm.state import StatesGroup, State


class FSMUserRegister(StatesGroup):
    start_register = State()
    fill_name = State()
    fill_age = State()
    fill_bio = State()
    fill_address = State()
    fill_lat_lon = State()
    end_register = State()


class FSMCreateTravel(StatesGroup):
    creating_travel = State()
    route_type = State()
    fill_points = State()
