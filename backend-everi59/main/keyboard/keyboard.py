from dataclasses import dataclass
from typing import Any

from aiogram.filters.callback_data import CallbackData
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder, KeyboardButton
from lexicon.lexicon import keyboard_lexicon


def create_inline_kb(*args: str,
                     lst: list | None = None,
                     width: int = 1,
                     last_btn: str | None = None,
                     dct: dict | None = None,
                     back_button: Any | None = None,
                     **kwargs: str) -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()
    buttons: list[InlineKeyboardButton] = []
    if lst:
        for button in lst:
            buttons.append(InlineKeyboardButton(
                text=keyboard_lexicon[button] if button in keyboard_lexicon else button,
                callback_data=button))
    if args:
        for button in args:
            buttons.append(InlineKeyboardButton(
                text=keyboard_lexicon[button] if button in keyboard_lexicon else button,
                callback_data=button))
    if dct:
        for button, text in dct.items():
            buttons.append(InlineKeyboardButton(
                text=text,
                callback_data=button))
    if kwargs:
        for button, text in kwargs.items():
            buttons.append(InlineKeyboardButton(
                text=text,
                callback_data=button))
    kb_builder.row(*buttons, width=width)
    if last_btn:
        kb_builder.row(InlineKeyboardButton(
            text=keyboard_lexicon[last_btn] if last_btn in keyboard_lexicon else last_btn,
            callback_data=last_btn
        ))
    if back_button:
        kb_builder.row(InlineKeyboardButton(
            text='Назад',
            callback_data=back_button
        ))
    return kb_builder.as_markup()


def keyboard_builder(buttons: list,
                     width: int | None = None,
                     adjust: list | None = None,
                     one_time_keyboard: True | False = False,
                     input_field_placeholder: str | None = None):
    kb_builder = ReplyKeyboardBuilder()
    buttons = [KeyboardButton(text=button) for button in buttons]
    if width:
        kb_builder.row(*buttons, width=width)
    else:
        kb_builder.add(*buttons)
        kb_builder.adjust(*adjust)
    if input_field_placeholder:
        return kb_builder.as_markup(resize_keyboard=True, one_time_keyboard=one_time_keyboard,
                                    input_field_placeholder=input_field_placeholder)
    return kb_builder.as_markup(resize_keyboard=True, one_time_keyboard=one_time_keyboard)
