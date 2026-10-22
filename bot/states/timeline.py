from aiogram.fsm.state import State, StatesGroup


class TimelineStates(StatesGroup):
    waiting_for_asset_alias = State()
    waiting_for_in_sec = State()
    waiting_for_out_sec = State()
