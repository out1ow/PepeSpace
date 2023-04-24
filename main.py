# TODO ORM-модели ☑
# TODO работа с контекстом пользователя ☐
# TODO загрузка и использование файлов ☑

import logging
import sys

from sqlalchemy.exc import IntegrityError
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import Application, MessageHandler, filters, ConversationHandler, CommandHandler
from telegram import ReplyKeyboardMarkup

from data import db_session
from data.users import Users
from data.planets import Planets

from config import BOT_TOKEN, MY_CHAT_ID

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG)

logger = logging.getLogger(__name__)


async def start(update, context):
    chat_id = update.effective_user.id
    db_sess = db_session.create_session()
    if len(list(db_sess.query(Users).filter(Users.chat_id == chat_id))) == 0:
        await update.message.reply_text(
            f"Добро пожаловать в сектор FN-2187!\n"
            f"Наша команда рада приветствовать вас в программе освоения дальнего космоса.\n"
            f"Как вас зовут?")
        return 1
    else:

        reply_keyboard = [['/profile', '/help'],
                          ['/ships', '/fabrics']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False,
                                     resize_keyboard=True)

        user = db_sess.query(Users).filter(Users.chat_id == chat_id).first()
        set_resource_job(update, context)
        await update.message.reply_text(
            f"С возвращением, {user.name}", reply_markup=markup)


async def help_command(update, context):
    set_resource_job(update, context)
    await update.message.reply_text("/start - начало работы с ботом\n"
                                    "/help - запросить помощи у бота\n"
                                    "/profile - посмотреть информацию о своём профиле\n"
                                    "/expedition - отправить экспедицию\n"
                                    "/fabrics - посмотреть информацию о количестве фабрик в колонии\n"
                                    "/build_fabric - построить новую фабрику за 500 кредитов\n"
                                    "/ships - посмотреть информацию о кораблях\n"
                                    "/build_ship - построить новый корабль за 500 ед. ресурсов\n"
                                    "/profile_img - установить/сменить фото профиля\n"
                                    "/feedback <какой-то текст> - отправить честный фидбэк разработчику")


async def user_name(update, context):
    try:
        name = update.message.text

        db_sess = db_session.create_session()
        user = Users()
        user.chat_id = update.effective_user.id
        user.name = name
        try:
            user.tg_name = update.effective_user.username
        except:
            pass
        db_sess.add(user)
        db_sess.commit()

        await update.message.reply_text(f'Вам выделена планета {user.chat_id}.\n'
                                        f'Введите название своей космической колонии.')
        return 2
    except IntegrityError:
        await update.message.reply_text('К сожалению данное имя недоступно\n'
                                        'Введите заново')
        return 1


async def planet_name(update, context):
    try:
        name = update.message.text

        db_sess = db_session.create_session()
        planet = Planets()
        planet.name = name

        chat_id = update.effective_user.id
        user = db_sess.query(Users).filter(Users.chat_id == chat_id).first()
        planet.user_id = user.id
        db_sess.add(planet)
        db_sess.commit()

        reply_keyboard = [['/profile', '/help'],
                          ['/ships', '/fabrics']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False,
                                     resize_keyboard=True)

        set_resource_job(update, context)

        await update.message.reply_text('Ваша колония зарегистрирована в базе данных программы '
                                        'освоения крайнего космоса\n'
                                        'Поздравляю!', reply_markup=markup)

        return ConversationHandler.END
    except IntegrityError:
        await update.message.reply_text('К сожалению данное название недоступно\n'
                                        'Введите заново')
        return 2


async def profile(update, context):
    try:
        set_resource_job(update, context)
        db_sess = db_session.create_session()
        chat_id = update.effective_user.id
        user = db_sess.query(Users).filter(Users.chat_id == chat_id).first()
        planet = db_sess.query(Planets).filter(Planets.user_id == user.id).first()
        try:
            await update.message.reply_photo(f'data/users_img/{user.chat_id}.png',
                                             caption=f'<b>Имя</b>: {user.name}\n'
                                                     f'<b>Планета</b>: {user.chat_id}\n'
                                                     f'<b>Колония</b>: {planet.name}\n'
                                                     f'<b>Ранг</b>: {user.level}\n'
                                                     f'<b>Опыт</b>: {user.exp}\n'
                                                     f'<b>Кредиты</b>: {user.credits}\n'
                                                     f'<b>Ресурсы</b>: {user.resources}\n'
                                                     f'<b>Заводы</b>: {planet.fabrics}\n'
                                                     f'<b>Флот</b>: {planet.available_ships}/{planet.ships}\n',
                                             parse_mode=ParseMode.HTML)
        except BadRequest:
            await update.message.reply_text(f'<b>Имя</b>: {user.name}\n'
                                            f'<b>Планета</b>: {user.chat_id}\n'
                                            f'<b>Колония</b>: {planet.name}\n'
                                            f'<b>Ранг</b>: {user.level}\n'
                                            f'<b>Опыт</b>: {user.exp}\n'
                                            f'<b>Кредиты</b>: {user.credits}\n'
                                            f'<b>Ресурсы</b>: {user.resources}\n'
                                            f'<b>Заводы</b>: {planet.fabrics}\n'
                                            f'<b>Флот</b>: {planet.available_ships}/{planet.ships}\n',
                                            parse_mode=ParseMode.HTML)
    except:
        pass


def remove_job_if_exists(name, context):
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def set_resource_job(update, context):
    chat_id = update.effective_user.id
    name = 'resource_' + str(chat_id)
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        context.job_queue.run_repeating(add_resources, interval=300, first=60,  # 5 минут
                                        chat_id=chat_id, name=''.join(['resource_', str(chat_id)]))


async def ships(update, context):
    try:
        set_resource_job(update, context)
        reply_keyboard = [['/build_ship', '/expedition'],
                          ['/back']]
        markup = ReplyKeyboardMarkup(reply_keyboard,
                                     resize_keyboard=True, one_time_keyboard=True)

        db_sess = db_session.create_session()
        chat_id = update.effective_user.id
        user = db_sess.query(Users).filter(Users.chat_id == chat_id).first()
        planet = db_sess.query(Planets).filter(Planets.user_id == user.id).first()
        await update.message.reply_text(f'У вас {planet.ships} кораблей', reply_markup=markup)
    except:
        pass


async def build_ship(update, context):
    try:
        set_resource_job(update, context)
        reply_keyboard = [['/profile', '/help'],
                          ['/ships', '/fabrics']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False,
                                     resize_keyboard=True)

        db_sess = db_session.create_session()
        chat_id = update.effective_user.id
        user = db_sess.query(Users).filter(Users.chat_id == chat_id).first()
        planet = db_sess.query(Planets).filter(Planets.user_id == user.id).first()
        if user.resources >= 500:
            planet.ships += 1
            user.resources -= 500
            await update.message.reply_text(f'У вас {planet.ships} кораблей', reply_markup=markup)
        else:
            await update.message.reply_text(f'У вас недостаточно ресурсов: {user.resources}/500', reply_markup=markup)

        db_sess.commit()
    except:
        pass


async def expedition(update, context):
    try:
        set_resource_job(update, context)
        reply_keyboard = [['/profile', '/help'],
                          ['/ships', '/fabrics']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False,
                                     resize_keyboard=True)
        db_sess = db_session.create_session()
        tguser = update.effective_user
        user = db_sess.query(Users).filter(Users.chat_id == tguser.id).first()
        planet = db_sess.query(Planets).filter(Planets.user_id == user.id).first()

        if planet.available_ships == 0:
            await update.message.reply_text('У вас нет свободных кораблей',
                                            reply_markup=markup)
            return

        time = 180  # 3 минут
        chat_id = update.effective_message.chat_id
        job_removed = remove_job_if_exists(str(chat_id), context)
        context.job_queue.run_once(return_ships, time, chat_id=chat_id, name=str(chat_id), data=time)

        planet.available_ships = 0
        db_sess.commit()

        await update.message.reply_text('Корабли отправлены в экспедицию, вернутся через 3 минуты',
                                        reply_markup=markup)
    except:
        pass


async def return_ships(context):
    db_sess = db_session.create_session()
    chat_id = context.job.chat_id
    user = db_sess.query(Users).filter(Users.chat_id == chat_id).first()
    planet = db_sess.query(Planets).filter(Planets.user_id == user.id).first()
    planet.available_ships = planet.ships
    user.credits += planet.ships * 10
    user.resources += planet.ships * 10
    user.exp += 10
    if user.exp >= (user.level * 100):
        user.level += 1
    db_sess.commit()

    await context.bot.send_message(chat_id, text='Корабли вернулись')


async def fabrics(update, context):
    try:
        set_resource_job(update, context)
        reply_keyboard = [['/build_fabric'],
                          ['/back']]
        markup = ReplyKeyboardMarkup(reply_keyboard,
                                     resize_keyboard=True, one_time_keyboard=True)

        db_sess = db_session.create_session()
        chat_id = update.effective_user.id
        user = db_sess.query(Users).filter(Users.chat_id == chat_id).first()
        planet = db_sess.query(Planets).filter(Planets.user_id == user.id).first()
        await update.message.reply_text(f'У вас {planet.fabrics} фабрик', reply_markup=markup)
    except:
        pass


async def build_fabric(update, context):
    try:
        set_resource_job(update, context)
        reply_keyboard = [['/profile', '/help'],
                          ['/ships', '/fabrics']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False,
                                     resize_keyboard=True)

        db_sess = db_session.create_session()
        chat_id = update.effective_user.id
        user = db_sess.query(Users).filter(Users.chat_id == chat_id).first()
        planet = db_sess.query(Planets).filter(Planets.user_id == user.id).first()
        if user.credits >= 500:
            planet.fabrics += 1
            user.credits -= 500
            await update.message.reply_text(f'У вас {planet.fabrics} фабрик', reply_markup=markup)
        else:
            await update.message.reply_text(f'У вас недостаточно кредитов: {user.credits}/500', reply_markup=markup)

        db_sess.commit()
    except:
        pass


async def add_resources(context):
    try:
        db_sess = db_session.create_session()
        chat_id = context.job.chat_id
        user = db_sess.query(Users).filter(Users.chat_id == chat_id).first()
        planet = db_sess.query(Planets).filter(Planets.user_id == user.id).first()
        user.resources += 5 * planet.fabrics
        db_sess.commit()
        print(f'|-----------------------------ADDED-{user.name}----------------------------|')
    except:
        pass


async def profile_img(update, context):
    try:
        set_resource_job(update, context)
        await update.message.reply_text('Отправьте изображение')
        return 1
    except:
        pass


async def get_img(update, context):
    db_sess = db_session.create_session()
    chat_id = update.effective_user.id
    user = db_sess.query(Users).filter(Users.chat_id == chat_id).first()

    file_id = update.message.photo[-1].file_id
    file = await context.bot.get_file(file_id)
    await file.download_to_drive(f'data/users_img/{chat_id}.png')
    await update.message.reply_text('Изображение успешно установлено')
    return ConversationHandler.END


async def feedback(update, context):
    try:
        set_resource_job(update, context)
        text = update.message.text[10:]

        db_sess = db_session.create_session()
        chat_id = update.effective_user.id
        user = db_sess.query(Users).filter(Users.chat_id == chat_id).first()

        text = f'<b>FEEDBACK</b>\nUser\'s id: {user.id}({user.name})\n' + text

        await context.bot.send_message(MY_CHAT_ID, text,
                                       parse_mode=ParseMode.HTML)
        await update.message.reply_text('Большое спасибо, ваше обращение направлено в отдел разработок.')
    except:
        pass


async def dev_message(update, context):  # Функция для отправки сообщений пользователям бота от имени разработчика
    if update.effective_user.id == MY_CHAT_ID:
        text = update.message.text[13:]
        chat_id = int(text.split()[0])
        text = ' '.join(text.split()[1:])
        await context.bot.send_message(chat_id, text,
                                       parse_mode=ParseMode.HTML)


async def discussion(update, context):
    text = update.message.text
    q_a = {
        'Привет': 'Здравствуйте, вас приветствует команда Стражей бесконечностей'
                  'по освоению крайнего космоса.',
        'Как какать?': 'https://journal.tinkoff.ru/a-kak-kakat/',
        'Hello there': 'General Kenobi'
    }
    if text in q_a.keys():
        text = update.message.text
        await update.message.reply_text(q_a[text])


async def back(update, context):
    reply_keyboard = [['/profile', '/help'],
                      ['/ships', '/fabrics']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False,
                                 resize_keyboard=True)
    await update.message.reply_text('Возвращение', reply_markup=markup)


def main():
    db_session.global_init("db/final_space.db")

    application = Application.builder().token(BOT_TOKEN).build()
    start_conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_name)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, planet_name)]
        },
        fallbacks=[MessageHandler(filters.TEXT & ~filters.COMMAND, planet_name)]
    )
    application.add_handler(start_conv)

    img_conv = ConversationHandler(
        entry_points=[CommandHandler('profile_img', profile_img)],
        states={
            1: [MessageHandler(filters.PHOTO, callback=get_img)]
        },
        fallbacks=[MessageHandler(filters.PHOTO, callback=get_img)]
    )
    application.add_handler(img_conv)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("expedition", expedition))
    application.add_handler(CommandHandler("fabrics", fabrics))
    application.add_handler(CommandHandler("build_fabric", build_fabric))
    application.add_handler(CommandHandler("ships", ships))
    application.add_handler(CommandHandler("build_ship", build_ship))
    application.add_handler(CommandHandler("profile_img", profile_img))
    application.add_handler(CommandHandler("feedback", feedback))
    application.add_handler(CommandHandler("dev_message", dev_message))
    application.add_handler(CommandHandler("back", back))

    messages = ['Привет', 'Как какать?', 'Hello there']
    application.add_handler(MessageHandler(filters.Text(messages), discussion))

    application.run_polling()


if __name__ == '__main__':
    main()
