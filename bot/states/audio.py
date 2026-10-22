from aiogram.fsm.state import State, StatesGroup


class AudioStates(StatesGroup):
    waiting_for_sfx_time = State()
    waiting_for_volume = State()
