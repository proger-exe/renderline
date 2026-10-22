from aiogram.fsm.state import State, StatesGroup


class ProjectStates(StatesGroup):
    waiting_for_title = State()
