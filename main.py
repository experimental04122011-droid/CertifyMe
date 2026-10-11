import asyncio
import random
import io
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ReportLab (PDF yaratish uchun)
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors

# BOT TOKENINGIZ
BOT_TOKEN = "8741571995:AAHt6ktOSs4E3oYLXrHEgShbxsSa8YEmWQk"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Savollar bazasi (General English)
QUESTIONS = [
    {
        "question": "Choose the correct verb: She ___ to school every day.",
        "options": ["go", "goes", "going", "gone"],
        "correct": "goes"
    },
    {
        "question": "What is the past simple of 'buy'?",
        "options": ["bought", "buyd", "buying", "boughten"],
        "correct": "bought"
    },
    {
        "question": "Fill in the blank: They ___ completed their homework.",
        "options": ["has", "have", "is", "are"],
        "correct": "have"
    },
    {
        "question": "Choose the correct word: Look at ___ birds in the sky!",
        "options": ["this", "that", "those", "them"],
        "correct": "those"
    },
    {
        "question": "Select the antonym of 'ancient':",
        "options": ["old", "modern", "historical", "classic"],
        "correct": "modern"
    }
]

# FSM holatlari
class QuizState(StatesGroup):
    waiting_for_name = State()
    answering_questions = State()

# A4 Landscape Sertifikat yaratish funksiyasi
def generate_certificate(name: str) -> io.BytesIO:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    # Tashqi va ichki hoshiyalar (Border)
    pdf.setStrokeColor(colors.HexColor("#1A365D"))
    pdf.setLineWidth(5)
    pdf.rect(20, 20, width - 40, height - 40)
    
    pdf.setStrokeColor(colors.HexColor("#D69E2E"))
    pdf.setLineWidth(2)
    pdf.rect(25, 25, width - 50, height - 50)

    # Sertifikat Sarlavhasi
    pdf.setFont("Helvetica-Bold", 32)
    pdf.setFillColor(colors.HexColor("#1A365D"))
    pdf.drawCentredString(width / 2, height - 120, "CERTIFICATE OF ATTENDANCE")

    # Matn
    pdf.setFont("Helvetica", 16)
    pdf.setFillColor(colors.black)
    pdf.drawCentredString(width / 2, height - 180, "This is to certify that")

    # Ism-familiya
    pdf.setFont("Helvetica-Bold", 26)
    pdf.setFillColor(colors.HexColor("#D69E2E"))
    pdf.drawCentredString(width / 2, height - 230, name)

    # Tafsilotlar
    pdf.setFont("Helvetica", 16)
    pdf.setFillColor(colors.black)
    pdf.drawCentredString(width / 2, height - 280, "has successfully completed the General English Quiz.")

    pdf.setFont("Helvetica-Oblique", 12)
    pdf.drawCentredString(width / 2, 80, "Thank you for participating!")

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer

@dp.message(CommandStart())
async def start_cmd(message: types.Message, state: FSMContext):
    await message.answer("Salom! General English testiga xush kelibsiz.\nSertifikat uchun Ism va Familiyangizni kiriting:")
    await state.set_state(QuizState.waiting_for_name)

@dp.message(QuizState.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    user_name = message.text.strip()
    
    # Savollarni tasodifiy tartiblash
    shuffled_questions = QUESTIONS.copy()
    random.shuffle(shuffled_questions)

    await state.update_data(
        name=user_name,
        questions=shuffled_questions,
        current_index=0,
        score=0
    )
    await send_next_question(message, state)

async def send_next_question(message: types.Message, state: harakat := None, state_context: FSMContext = None):
    # Aiogram argument moslashuvi
    pass

# Yuqoridagi yordamchi o'rniga to'g'ridan-to'g'ri chaqiruv funksiyasi:
async def send_next_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    questions = data["questions"]
    index = data["current_index"]

    if index < len(questions):
        q = questions[index]
        options = q["options"].copy()
        random.shuffle(options)

        kb = types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text=opt)] for opt in options],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer(f"{index + 1}-Savol: {q['question']}", reply_markup=kb)
        await state.set_state(QuizState.answering_questions)
    else:
        user_name = data["name"]
        await message.answer("Tabriklaymiz! Testni yakunladingiz. Sertifikatingiz tayyorlanmoqda...", reply_markup=types.ReplyKeyboardRemove())

        pdf_buffer = generate_certificate(user_name)
        cert_file = types.BufferedInputFile(pdf_buffer.getvalue(), filename=f"Certificate_{user_name}.pdf")

        await message.answer_document(document=cert_file, caption=f"Hurmatli {user_name}, sertifikatingizni yuklab oling!")
        await state.clear()

@dp.message(QuizState.answering_questions)
async def process_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    questions = data["questions"]
    index = data["current_index"]
    user_answer = message.text

    correct_answer = questions[index]["correct"]
    score = data["score"]

    if user_answer == correct_answer:
        score += 1

    await state.update_data(current_index=index + 1, score=score)
    await send_next_question(message, state)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
