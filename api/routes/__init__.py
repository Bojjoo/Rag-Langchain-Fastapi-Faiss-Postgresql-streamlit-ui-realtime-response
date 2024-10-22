from api.services.chatbot import ChatBot
from api.services.vectorstore_faiss import VectorStore
from fastapi import UploadFile, File, Form, APIRouter
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from api.database.database import SQLDatabase
from api.services.csv_agent import CSVAgent
import pandas as pd
import os

apikeys_cache = {}
router = APIRouter()
retriever_cache = {}
vectorstore_cache = {}
bm25_retriever_cache = {}

dataframe_cache = {}
sql_conn = SQLDatabase()

agent_cache = {}

model_openai = ["gpt-4", "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
model_gemini = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro", "gemini-1.5-flash-002", "gemini-1.5-pro-002",
                "gemini-1.5-flash-8b"]


class QuestionRequest(BaseModel):
    question: str
    conversation_id: str
    prompt_template: str
    user_id: str
    model: str


class UserID(BaseModel):
    user_id: str


class FileDelete(BaseModel):
    file_name: str
    user_id: str


class PromptTemplate(BaseModel):
    title: str
    prompt_text: str
    user_id: str


class CSVQuestion(BaseModel):
    user_id: str
    question: str
    model: str


class SignInAccount(BaseModel):
    user_name: str
    password: str


class SignUpAccount(BaseModel):
    user_name: str
    password: str

