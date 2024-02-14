import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters.command import Command, CommandStart, CommandObject
from aiogram.filters import StateFilter
from filters import ChatTypeFilter
from aiogram.utils.deep_linking import create_start_link, decode_payload
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from database import MessageDatabase
from decouple import config


logging.basicConfig(level=logging.INFO)
bot = Bot(token=config("BOT_TOKEN"))
dp = Dispatcher()
dp["started_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
dp["group_id"] = config("GROUP_ID")

group_router = Router()
group_router.message.filter(
    ChatTypeFilter(chat_type=["group", "supergroup"])
)

private_router = Router()
private_router.message.filter(
    ChatTypeFilter(chat_type=["private"])
)

database = MessageDatabase("messages.db")


class SendMessage(StatesGroup):
    message = State()
    
    
@private_router.message(StateFilter(None), CommandStart(deep_link=True))
async def start_deeplink(message: types.Message, state: FSMContext, command: CommandObject):
    send_to = decode_payload(command.args)
    database.insert_user(message.chat.id, message.from_user.username)
    await message.answer("Напиши сюда что бы ты хотел(а) отправить тому, чью ссылку ты открыл(а)\nПредупреждение: премиум-эмодзи отправить нельзя!")
    await state.set_state(SendMessage.message)
    await state.set_data({"send_to": send_to})


@private_router.message(StateFilter(None), CommandStart(deep_link=False))
async def cmd_start(message: types.Message):
    database.insert_user(message.chat.id, message.from_user.username)
    await message.answer(f"Привет! Твоя ссылка: {await create_start_link(bot, message.chat.id, encode=True)}")


@private_router.message(SendMessage.message)
async def send_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await bot.send_message(data["send_to"], "У Вас новая валентинка!")
    msg = await bot.copy_message(data["send_to"], message.chat.id, message.message_id)
    database.insert_message(data["send_to"], msg.message_id, message.chat.id, message.message_id)
    await state.clear()
    await message.reply("Ваше сообщение было отправлено!")
    
    await bot.send_message(dp["group_id"], f"@{message.from_user.username} отправил сообщение пользователю @{database.get_username(data['send_to'])}")
    await bot.copy_message(dp["group_id"], message.chat.id, message.message_id)
    

@private_router.message(F.reply_to_message)
async def reply_to_message(message: types.Message):
    reply = message.reply_to_message
    result = database.get_message(reply.chat.id, reply.message_id)
    if not result:
        return await message.reply("Сообщение не найдено")
    msg = await bot.copy_message(result[3], message.chat.id, message.message_id, reply_to_message_id=result[4])
    database.insert_message(result[3], msg.message_id, message.chat.id, message.message_id)
    
    await bot.send_message(dp["group_id"], f"@{message.from_user.username} ответил на сообщение пользователя @{database.get_username(result[3])}")
    await bot.copy_message(dp["group_id"], message.chat.id, message.message_id)
    

@group_router.message(Command("setgroup"))
async def setgroup(message: types.Message):
    dp["group_id"] = message.chat.id
    print(message.chat.id)
    return await message.reply("Айди группы установлено")


async def main():
    dp.include_routers(
        group_router,
        private_router
    )

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
