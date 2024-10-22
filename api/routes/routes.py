from api.routes import *


@router.get("/")
def read_root():
    return {
        'Hello This is Rag Langchain application on FastAPI !!!'
    }


@router.post("/get_retriever/")
def get_retriever(user_id: UserID):
    user_vectorstore = VectorStore(user_id.user_id)
    user_db = user_vectorstore.user_db
    user_retriever = user_vectorstore.user_retriever
    user_bm25_retriever = user_vectorstore.user_bm25_retriever

    retriever_cache[f'{user_id.user_id}'] = user_retriever
    vectorstore_cache[f'{user_id.user_id}'] = user_db
    bm25_retriever_cache[f'{user_id.user_id}'] = user_bm25_retriever
    if user_db is not None:
        return {"OK"}
    else:
        return {"None"}

@router.post("/get_apikey/")
def get_apikey(user_id: UserID):
    apikey = sql_conn.get_api_key(user_id.user_id)
    apikeys_cache[f'{user_id.user_id}'] = dict(apikey)
    return len(apikeys_cache[f'{user_id.user_id}'])

@router.post('/upload_data')
async def upload_file(file: UploadFile = File(...), user_id: str = Form(...)):
    vectorstore = VectorStore(user_id)
    chunks = vectorstore.upload_file(file, user_id)

    new_vectorstore = VectorStore(user_id)

    user_db = new_vectorstore.user_db
    user_retriever = new_vectorstore.user_retriever
    user_bm25_retriever = new_vectorstore.user_bm25_retriever

    retriever_cache[f'{user_id}'] = user_retriever
    vectorstore_cache[f'{user_id}'] = user_db
    bm25_retriever_cache[f'{user_id}'] = user_bm25_retriever

    return chunks


@router.post('/add_prompt_template/')
async def add_prompt_template(prompt_template: PromptTemplate):
    sql_conn.add_prompt_template(prompt_template.title, prompt_template.prompt_text, prompt_template.user_id)


@router.post('/get_answer_about_users_data/')
async def get_response(question_request: QuestionRequest):
    try:
        # With openai model
        if question_request.model in model_openai:
            apikey = apikeys_cache[f"{question_request.user_id}"]["openaikey"]
            bot = ChatBot(openai_apikey=apikey)

            user_retriever = retriever_cache[f'{question_request.user_id}']
            user_bm25_retriever = bm25_retriever_cache[f'{question_request.user_id}']

            prompt = await bot.question_handler(user_retriever, user_bm25_retriever, question_request)
            generator = bot.send_message_openai(prompt, question_request.model)

            return StreamingResponse(generator, media_type="text/event-stream")

        # With gemini model
        else:
            apikey = apikeys_cache[f"{question_request.user_id}"]["geminikey"]
            bot = ChatBot(gemini_apikey=apikey)

            user_retriever = retriever_cache[f'{question_request.user_id}']
            user_bm25_retriever = bm25_retriever_cache[f'{question_request.user_id}']

            prompt = await bot.question_handler(user_retriever, user_bm25_retriever, question_request)
            generator = bot.send_message_gemini(prompt, question_request.model)

            return StreamingResponse(generator, media_type="text/event-stream")

    except:
        return {"Error"}


@router.post('/upload_CSV_file/')
async def csv_file_handler(file: UploadFile = File(...), user_id: str = Form(...)):
    file_formats = {
        "csv": pd.read_csv,
        "xls": pd.read_excel,
        "xlsx": pd.read_excel,
        "xlsm": pd.read_excel,
        "xlsb": pd.read_excel,
    }
    try:
        ext = os.path.splitext(file.filename)[1][1:].lower()
    except:
        ext = file.filename.split(".")[-1]
    if ext in file_formats:
        df = file_formats[ext](file.file)
        try:
            #dataframe_cache[f"{user_id}"]:
            dataframe_cache[f"{user_id}"].append(df)
            df = dataframe_cache[f"{user_id}"]
            agent_cache[f"{user_id}"] = CSVAgent(df)
        except:
            dataframe_cache[f'{user_id}'] = [df]
            agent_cache[f"{user_id}"] = CSVAgent(df)
        return "Saved dataframe successfully!"
    else:
        return f"Unsupported file format: {ext}"


@router.post('/get_answer_about_csv_file/')
async def get_response(question: CSVQuestion):
    agent = agent_cache[f"{question.user_id}"]
    agent.model = question.model
    response = await agent.get_response(question.question)
    return response


@router.delete("/delete_file/")
def delete_file(file: FileDelete):
    user_id = file.user_id
    file_name = file.file_name
    vectorstore = VectorStore(user_id)
#######################
    user_db = vectorstore.user_db
    user_retriever = vectorstore.user_retriever
    user_bm25_retriever = vectorstore.user_bm25_retriever

    retriever_cache[f'{user_id}'] = user_retriever
    vectorstore_cache[f'{user_id}'] = user_db
    bm25_retriever_cache[f'{user_id}'] = user_bm25_retriever

    try:
        vectorstore.delete_from_vectorstore(file_name, user_id)
        return 1
    except:
        return 0


# Router for UI
# Signin endpoint
@router.post("/sign_in_user/")
async def verify_sign_in(account: SignInAccount):
    try:
        stored_password = sql_conn.get_password_of_user(account.user_name)
        user_id = sql_conn.get_userid_from_username(account.user_name)
        if stored_password == account.password:
            return user_id
        else:
            return 0
    except:
        return 0


# get conversation endpoint
@router.post("/get_conversation/")
async def get_conversation(user_id: UserID):
    conversations = sql_conn.get_conversation_session_user(user_id.user_id)
    return conversations

@router.post("/register_account/")
async def register_account(new_acc: SignUpAccount):
    result = sql_conn.register_account(new_acc.user_name, new_acc.password)
    return result
