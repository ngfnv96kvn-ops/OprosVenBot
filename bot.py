#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import smtplib
import logging
from email.message import EmailMessage
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from config import BOT_TOKEN, YOUR_TELEGRAM_ID, EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER, SMTP_SERVER, SMTP_PORT

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

QUESTIONS = [
    (1, "1️⃣ Тип объекта:\n\n▪️ Квартира (в многоквартирном доме)\n▪️ Частный жилой дом / коттедж\n▪️ Офисное помещение / Бизнес-центр\n▪️ Торговый зал / Магазин / ТРЦ\n▪️ Ресторан / Кафе / Столовая / Горячий цех\n▪️ Медицинское учреждение / Клиника / Стоматология\n▪️ Производственное помещение / Цех\n▪️ Склад / Логистический центр\n▪️ Спортивный зал / Фитнес-клуб / Бассейн\n▪️ Гостиница / Хостел\n▪️ Другое:", 'single'),
    (2, "2️⃣ Общая обслуживаемая площадь: _____ м²", 'free'),
    (3, "3️⃣ Количество этажей:", 'free'),
    (4, "4️⃣ Высота потолков (типовая): _____ м (если разная — укажите по помещениям)", 'free'),
    (5, "5️⃣ Назначение каждого помещения (если готово — приложите планы с экспликацией)", 'free'),
    (6, "6️⃣ Максимальное количество людей одновременно: _____ чел.", 'free'),
    (7, "7️⃣ Из них постоянно работающих / проживающих: _____ чел.", 'free'),
    (8, "8️⃣ Режим работы: круглосуточно / дневной (с __ до __) / по расписанию", 'free'),
    (9, "9️⃣ Какие планы и исходные документы есть в наличии? (можно выбрать несколько)\n\n▪️ Архитектурные планы этажей (PDF/DWG) с размерами и площадями\n▪️ План БТИ / обмерный план\n▪️ Технические условия (ТУ) на подключение к электроснабжению\n▪️ Дизайн-проект с расстановкой мебели и оборудования\n▪️ Технологическое задание (для кафе, цехов)\n▪️ Ничего нет", 'multi'),
    (10, "🔟 Какие внутренние тепловыделения нужно учесть? (можно выбрать несколько)\n\n▪️ Люди (постоянно / временно)\n▪️ Оргтехника и компьютеры\n▪️ Освещение (тип: светодиодное / люминесцентное / лампы накаливания)\n▪️ Технологическое оборудование (плиты, печи, паровые котлы, станки)\n▪️ Холодильные витрины / морозильные камеры\n▪️ Солнечная радиация через остекление (площадь остекления велика)\n▪️ Другое:", 'multi'),
    (11, "1️⃣1️⃣ Есть ли источники влаговыделений или специфических вредностей? (можно выбрать несколько)\n\n▪️ Бассейн / джакузи / аквазона\n▪️ Мокрые процессы (мойка, стерилизация, прачечная)\n▪️ Пары масла, дыма, гари (вытяжные зонты над кухонным оборудованием)\n▪️ Пыль, стружка, аэрозоли (производство)\n▪️ Химические вещества, запахи (лаборатории, стоматология)\n▪️ Табачный дым (курительная комната)\n▪️ Нет, только стандартное пребывание людей", 'multi'),
    (12, "1️⃣2️⃣ Нужно ли обеспечить особый класс чистоты воздуха (фильтрация)?\n\n▪️ Стандартная очистка (грубая фильтрация EU3–EU4)\n▪️ Тонкая фильтрация приточного воздуха (EU7–EU9, для аллергиков, офисов)\n▪️ Высокоэффективная фильтрация HEPA (медицина, чистые помещения)\n▪️ Угольные фильтры (удаление запахов, газов)\n▪️ Не требуется", 'single'),
    (13, "1️⃣3️⃣ Нужна ли система увлажнения или осушения воздуха?\n\n▪️ Да, требуется увлажнение (поддержание влажности 40–60% зимой)\n▪️ Да, требуется осушение (для бассейна, влажных помещений)\n▪️ Да, и увлажнение, и осушение (комбинированная система)\n▪️ Нет, не требуется", 'single'),
    (14, "1️⃣4️⃣ Есть ли специальные санитарно-гигиенические требования?\n\n▪️ Да, объект медицинский / фармацевтический (СанПиН, класс чистоты)\n▪️ Да, объект общественного питания (вытяжные зонты, приток в горячий цех)\n▪️ Да, производство с вредными условиями (ПДК, местные отсосы)\n▪️ Нет, только стандартный воздухообмен по СП 60", 'single'),
    (15, "1️⃣5️⃣ Тип вентиляции:\n\n▪️ Естественная (вытяжка через каналы, приток через окна / клапаны)\n▪️ Механическая вытяжка + естественный приток\n▪️ Механическая приточная + естественная вытяжка\n▪️ Приточно-вытяжная с механическим побуждением (ПВУ)\n▪️ Приточно-вытяжная с рекуперацией тепла (пластинчатый рекуператор, роторный)\n▪️ Центральная приточная установка с секцией охлаждения и нагрева\n▪️ Другое:", 'single'),
    (16, "1️⃣6️⃣ Размещение вентиляционного оборудования:\n\n▪️ Венткамера внутри здания (указать помещение)\n▪️ На кровле (наружное исполнение)\n▪️ На балконе / фасаде (для квартир)\n▪️ В подвале / цокольном этаже\n▪️ В техническом помещении / коридоре\n▪️ Пока неизвестно, нужна рекомендация", 'single'),
    (17, "1️⃣7️⃣ Система воздуховодов (можно выбрать несколько):\n\n▪️ Круглые спирально-навивные (оцинковка)\n▪️ Прямоугольные (оцинковка)\n▪️ Гибкие воздуховоды (для разводки)\n▪️ Тканевые воздуховоды (для бассейнов, спортзалов)\n▪️ Скрытая прокладка (за потолком, в коробах, в стенах)\n▪️ Открытая прокладка (индустриальный стиль)\n▪️ Нужна тепло- и шумоизоляция воздуховодов", 'multi'),
    (18, "1️⃣8️⃣ Местная вытяжка (если требуется):\n\n▪️ Кухонные зонты (над бытовыми плитами)\n▪️ Вытяжные зонты для профессиональных кухонь (с жироуловителями)\n▪️ Местные отсосы от станков (стружка, пыль)\n▪️ Вытяжные шкафы (химические, лабораторные)\n▪️ Бортовые отсосы (для бассейнов)\n▪️ Нет", 'single'),
    (19, "1️⃣9️⃣ Тип системы кондиционирования:\n\n▪️ Сплит-системы настенные (одна или несколько)\n▪️ Мультисплит-система (один наружный блок – несколько внутренних)\n▪️ Полу-промышленные кондиционеры (канальные, кассетные, напольно-потолочные)\n▪️ VRF/VRV-система (мультизональная, с изменяемым расходом хладагента)\n▪️ Чиллер-фанкойлы (водяная система охлаждения)\n▪️ Центральный кондиционер (секционный, с водяным или фреоновым охлаждением)\n▪️ Прецизионный кондиционер (для серверных)\n▪️ Кондиционирование не требуется", 'single'),
    (20, "2️⃣0️⃣ Размещение наружных блоков:\n\n▪️ На фасаде здания (под окнами, на кронштейнах)\n▪️ На кровле\n▪️ На балконе / лоджии (специально отведенное место)\n▪️ В цоколе / техническом помещении с воздуховодами\n▪️ В специальной зоне на участке (на земле)\n▪️ Нужна консультация", 'single'),
    (21, "2️⃣1️⃣ Нужно ли резервирование или зонирование?\n\n▪️ Да, нужно независимое кондиционирование по зонам (VRF с несколькими внутренними блоками)\n▪️ Да, требуется резервный контур на случай отказа (100% резерв)\n▪️ Нет, достаточно единой системы", 'single'),
    (22, "2️⃣2️⃣ Требуется ли система противодымной защиты?\n\n▪️ Да, для жилого дома выше 28 м (или общественного здания)\n▪️ Да, для торгового центра, офиса, гостиницы (по СП 7)\n▪️ Да, для производственного / складского здания\n▪️ Нет (объект малоэтажный или без требований)", 'single'),
    (23, "2️⃣3️⃣ Какие системы ПДВ нужно предусмотреть? (можно выбрать несколько)\n\n▪️ Дымоудаление из коридоров и холлов\n▪️ Дымоудаление из помещений с постоянным пребыванием людей\n▪️ Подпор воздуха в лифтовые шахты\n▪️ Подпор воздуха в незадымляемые лестничные клетки\n▪️ Дымоудаление из паркинга (подземного / встроенного)\n▪️ Автоматика и диспетчеризация ПДВ\n▪️ Пока неизвестно, уточнить по результатам расчёта пожарных рисков", 'multi'),
    (24, "2️⃣4️⃣ Уровень автоматизации:\n\n▪️ Ручное управление (включение/выключение с выключателя)\n▪️ Автоматическое поддержание температуры по датчикам (термостаты)\n▪️ Центральный контроллер с погодозависимым управлением\n▪️ Диспетчеризация (удалённый мониторинг, управление по расписанию)\n▪️ Интеграция в систему «Умный дом» / BMS (Modbus, KNX, BACnet)", 'single'),
    (25, "2️⃣5️⃣ Требования к шуму (особо важные помещения):\n\n▪️ Повышенные требования к уровню шума (спальни, переговорные, студии)\n▪️ Стандартные нормы\n▪️ Не критично", 'single'),
    (26, "2️⃣6️⃣ Ориентировочный бюджет на оборудование и монтаж (только ОВ/ВК):\n\n▪️ до 300 000 ₽\n▪️ 300 000 – 1 000 000 ₽\n▪️ 1 000 000 – 3 000 000 ₽\n▪️ свыше 3 000 000 ₽\n▪️ Бюджет открытый, нужна смета", 'single'),
    (27, "2️⃣7️⃣ Стадия проектирования:\n\n▪️ Эскизное предложение (принципиальная схема, подбор основного оборудования)\n▪️ Проектная документация (стадия «П») – для согласований\n▪️ Рабочая документация (стадия «РД») – со спецификациями, планами, аксонометрией\n▪️ Полный пакет: расчёты + П + РД + смета", 'single'),
    (28, "2️⃣8️⃣ Сроки:\n\n▪️ Начало проектирования:\n▪️ Начало монтажных работ:", 'free'),
    (29, "2️⃣9️⃣ Контактная информация:\n\n▪️ Город:\n▪️ Имя:\n▪️ Телефон:\n▪️ Телеграмм:\n▪️ Email:", 'free'),
    (30, "3️⃣0️⃣ Какие материалы вы можете предоставить? (можно выбрать несколько)\n\n▪️ Планы помещений (PDF/DWG)\n▪️ Технические условия на электроснабжение\n▪️ Теплотехнический расчёт здания (если делали)\n▪️ Технологическое задание (для ресторана, цеха)\n▪️ Фотографии помещений / существующих систем\n▪️ Ничего", 'multi'),
]

def make_single_keyboard(options_text):
    lines = options_text.strip().split('\n')
    options = []
    for line in lines:
        line = line.strip()
        if line and (line.startswith('▪️') or line.startswith('-') or (line and line[0].isdigit())):
            clean = line.lstrip('▪️- ').strip()
            if clean:
                options.append(clean)
    if not options:
        options = [l.strip() for l in lines if l.strip()]
    keyboard = [options[i:i+2] for i in range(0, len(options), 2)]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def extract_options(question_text):
    lines = question_text.split('\n')
    opts = []
    for line in lines:
        line = line.strip()
        if line.startswith('▪️'):
            opts.append(line[2:].strip())
    return opts

async def send_email_report(user_data):
    text = "📋 Анкета по системам вентиляции и кондиционирования\n\n"
    for step, q_text, _ in QUESTIONS:
        answer = user_data.get(step, "—")
        short_q = q_text.split('\n')[0][:80]
        text += f"{short_q}:\n{answer}\n\n"
    msg = EmailMessage()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = "Новая анкета ОВ"
    msg.set_content(text)
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        logging.info("Письмо отправлено")
    except Exception as e:
        logging.error(f"Ошибка почты: {e}")

async def send_telegram_copy(update, context, user_data):
    report_lines = ["✅ Ваши ответы на анкету:"]
    for step, q_text, _ in QUESTIONS:
        answer = user_data.get(step, "—")
        header = q_text.split('\n')[0][:60]
        report_lines.append(f"{header}: {answer}")
    report = "\n\n".join(report_lines)
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text=report)
    if YOUR_TELEGRAM_ID:
        await context.bot.send_message(
            chat_id=YOUR_TELEGRAM_ID,
            text=f"📬 Новая анкета от @{update.effective_user.username or 'Пользователь'}\n\n{report}"
        )

async def show_multi_question(update, context, step, q_text):
    options = extract_options(q_text)
    if 'multi_selected' not in context.user_data:
        context.user_data['multi_selected'] = {}
    if step not in context.user_data['multi_selected']:
        context.user_data['multi_selected'][step] = [False] * len(options)
    selected = context.user_data['multi_selected'][step]
    keyboard = []
    for i, opt in enumerate(options):
        status = "✅" if selected[i] else "⬜"
        keyboard.append([InlineKeyboardButton(f"{status} {opt}", callback_data=f"multi_{step}_{i}")])
    keyboard.append([InlineKeyboardButton("✅ Готово", callback_data=f"multi_done_{step}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text=q_text, reply_markup=reply_markup)

async def start(update, context):
    await update.message.reply_text("Привет! Я задам 30 вопросов по системам вентиляции и кондиционирования. Для отмены /cancel.")
    context.user_data.clear()
    context.user_data['current_step'] = 1
    await ask_current_question(update, context)

async def ask_current_question(update, context):
    step = context.user_data.get('current_step')
    if not step or step > len(QUESTIONS):
        await finish_survey(update, context)
        return
    _, q_text, q_type = QUESTIONS[step-1]
    if q_type == 'single':
        parts = q_text.split('\n\n', 1)
        options_part = parts[1] if len(parts) > 1 else q_text
        reply_markup = make_single_keyboard(options_part)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=q_text, reply_markup=reply_markup)
    elif q_type == 'multi':
        await context.bot.send_message(chat_id=update.effective_chat.id, text="(Выберите несколько вариантов, затем нажмите 'Готово')")
        await show_multi_question(update, context, step, q_text)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=q_text + "\n(Введите ваш ответ текстом)", reply_markup=ReplyKeyboardRemove())

async def handle_message(update, context):
    step = context.user_data.get('current_step')
    if not step:
        await update.message.reply_text("Начните с /start")
        return
    if step > len(QUESTIONS):
        await finish_survey(update, context)
        return
    _, _, q_type = QUESTIONS[step-1]
    if q_type == 'multi':
        await update.message.reply_text("Пожалуйста, используйте кнопки для выбора вариантов и нажмите 'Готово'.")
        return
    context.user_data[step] = update.message.text
    next_step = step + 1
    context.user_data['current_step'] = next_step
    await ask_current_question(update, context)

async def handle_multi_callback(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    step = context.user_data.get('current_step')
    if not step:
        return
    _, q_text, _ = QUESTIONS[step-1]
    options = extract_options(q_text)
    if data.startswith("multi_done_"):
        selected = context.user_data.get('multi_selected', {}).get(step, [])
        answer = ", ".join([opt for i, opt in enumerate(options) if i < len(selected) and selected[i]]) if any(selected) else "Ничего не выбрано"
        context.user_data[step] = answer
        await query.edit_message_reply_markup(reply_markup=None)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Ответ сохранён!")
        context.user_data.pop('multi_selected', None)
        next_step = step + 1
        context.user_data['current_step'] = next_step
        await ask_current_question(update, context)
        return
    elif data.startswith("multi_"):
        parts = data.split("_")
        idx_option = int(parts[2])
        if 'multi_selected' not in context.user_data:
            context.user_data['multi_selected'] = {}
        if step not in context.user_data['multi_selected']:
            context.user_data['multi_selected'][step] = [False] * len(options)
        context.user_data['multi_selected'][step][idx_option] = not context.user_data['multi_selected'][step][idx_option]
        selected = context.user_data['multi_selected'][step]
        keyboard = []
        for i, opt in enumerate(options):
            status = "✅" if selected[i] else "⬜"
            keyboard.append([InlineKeyboardButton(f"{status} {opt}", callback_data=f"multi_{step}_{i}")])
        keyboard.append([InlineKeyboardButton("✅ Готово", callback_data=f"multi_done_{step}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_reply_markup(reply_markup=reply_markup)
        return

async def finish_survey(update, context):
    user_data = {k: v for k, v in context.user_data.items() if isinstance(k, int)}
    await send_email_report(user_data)
    await send_telegram_copy(update, context, user_data)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🎉 Спасибо! Анкета успешно отправлена.\nМы свяжемся с вами.",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()

async def cancel(update, context):
    await update.message.reply_text("❌ Опрос отменён.", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('cancel', cancel))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_multi_callback))
    print("✅Бот для анкеты по вентиляции и кондиционированию запускается...")
    application.run_polling(poll_interval=1.0, timeout=30)

if __name__ == "__main__":
    main()
