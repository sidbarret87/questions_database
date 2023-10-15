from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy.orm.exc import NoResultFound # исключение в SQLAlchemy, которое генерируется,
# когда операция, требующая результата, не дает результат
from fastapi import FastAPI, HTTPException
import httpx #  библиотека для асинхронных HTTP запросов.
from pydantic import BaseModel
import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

app = FastAPI()
# связанные с базой данных компоненты
load_dotenv() # берет переменные окружения из .env
DATABASE_URL = os.getenv('DATABASE_URL')

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base() # базовый класс для описания моделей в декларативном стиле


# с использованием указанного URL
#  модель данных, представляющая запрос
class QuestionRequest(BaseModel):
    questions_num: int # количество вопросов, которое нужно получить

# модель данных, представляющая вопрос
class Question(BaseModel):
    id: int # уникальный идентификатор вопроса
    question: str # текст вопроса
    answer: str # ответ на вопрос
    created_at: datetime  # дата создания

#  модель данных вопроса, основываясь на классе Question
class QuestionModel(Base):
    __tablename__="questions"
    id = Column(Integer, primary_key=True, index=True)
    question  = Column(String)
    answer = Column(String)
    created_date = Column(DateTime)

Base.metadata.create_all(bind=engine)#будет создавать только те таблицы, которые еще не существуют,
# то есть он не уничтожит или не перезапишет существующие таблицы.
#  он должен быть выполнен при старте  приложения.


@app.post("/questions/")
async def process_questions(questions: QuestionRequest)-> Question:
    unique_questions =[]
    async with httpx.AsyncClient() as client:

        while len(unique_questions)<questions.questions_num:

            # AsyncClient используется для выполнения асинхронных HTTP-запросов

            #Ниже выполняется асинхронный HTTP GET-запрос к определенному URL. Мы передаем URL в метод client.get()
            # URL содержит параметры, которые определяют, что мы хотим получить - в данном случае, случайный набор вопросов.
            response = await client.get(f"https://jservice.io/api/random?count={questions.questions_num}")



        # обработка ответов сервера при выполнении HTTP-запроса выше
        # самый общий код 200 означает "ОК" и используется для указания, что запрос был успешно обработан
        # и выполнен.

            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Не удалось получить вопросы")

            potential_questions = response.json() # перевод в Python словарь JSON ответа

            db = SessionLocal()
            # Для каждого потенциального вопроса, проверяем, есть ли он уже в базе данных

            for pq in potential_questions:
                try:
                # Попытка получить вопрос из базы данных, если он там присутствует
                    db.query(QuestionModel).filter(QuestionModel.id==pq['id']).one()
                except NoResultFound:
                    # Если вопроса нет в базе данных, то добавляем его в список уникальных вопросов
                    unique_question = QuestionModel(id=pq['id'], question=pq['question'],
                     answer = pq['answer'],created_date = datetime.now())
                    db.add(unique_question)
                    db.commit()
                    unique_questions.append(Question(id=unique_question.id, question=unique_question.question,
                                                     answer=unique_question.answer,
                                                     created_at=unique_question.created_date))
            last_question = db.query(QuestionModel).order_by(QuestionModel.created_date.desc()).first()
            db.close()

            if last_question is not None:
                return Question(id=last_question.id, question=last_question.question,
                        answer=last_question.answer, created_at=last_question.created_date)

            else:
                return Question()


