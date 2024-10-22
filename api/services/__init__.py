from api.config import *

# For chatbot
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.document_compressors.flashrank_rerank import FlashrankRerank
from flashrank import Ranker
from langchain.retrievers import ContextualCompressionRetriever
from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv
from langchain.callbacks import AsyncIteratorCallbackHandler

import asyncio
from typing import AsyncIterable

# For vectorstore_faiss
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    DirectoryLoader,
    TextLoader,
    CSVLoader,
    UnstructuredWordDocumentLoader
)
from langchain_community.vectorstores import FAISS
import os
from fastapi import UploadFile, File, Form
import shutil
from langchain.retrievers.ensemble import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever

from api.database.database import SQLDatabase


# For csv_agent
from langchain.agents import AgentType
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_google_genai import ChatGoogleGenerativeAI
import pandas as pd


# load_dotenv(find_dotenv())
load_dotenv()
admin_openaikey = os.getenv('OPENAIKEY')

model_embedding = OpenAIEmbeddings(model=MODEL_EMBEDDING, api_key=admin_openaikey)
sql_conn = SQLDatabase()


class QuestionRequest(BaseModel):
    question: str
    conversation_id: str
    prompt_template: str
    user_id: str
    model: str



