from aiogram.fsm.state import State, StatesGroup


class SubtitleStates(StatesGroup):
    waiting_for_start_sec = State()
    waiting_for_end_sec = State()
    waiting_for_text = State()
