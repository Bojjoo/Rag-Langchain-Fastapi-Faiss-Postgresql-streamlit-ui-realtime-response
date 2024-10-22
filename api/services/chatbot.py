from api.services import *


class ChatBot:
    def __init__(self, openai_apikey=None, gemini_apikey=None):
        self.model_llm = None
        self.openai_apikey = openai_apikey
        self.gemini_apikey = gemini_apikey
        self.model_reformulate_question = ChatOpenAI(temperature=TEMPERATURE, model=MODEL_LLM, api_key=admin_openaikey)
        self.sender = ['human', 'ai']

    # Reformulate the question based on history
    def reformulate_question(self, question, history):
        remake_question_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", REGENERATE_QUESTION_PROMPT),
                ("system", "Chat history: \n {chat_history}\n"),
                ("system", "Reformulate this input: {question}"),
            ]
        )

        question_pt = remake_question_prompt.format(chat_history=history, question=question)
        new_question = self.model_reformulate_question.invoke(question_pt)
        return new_question.content

    # Retrieve relevant data
    async def retriever(self, question, retriever, bm25_retriever):
        ensemble_retriever = EnsembleRetriever(retrievers=[bm25_retriever, retriever],
                                               weights=[0.5, 0.5])

        compressed_docs = await ensemble_retriever.ainvoke(question)
        content_text = "\n\n---\n\n".join([doc.page_content for doc in compressed_docs[:6]])
        return content_text

    def prompt_rag(self, question, context, history, prompt_template):
        llm_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", prompt_template),
                ("system", "Chat history: \n {chat_history}\n"),
                ("system", "Context about relevant data: \n"),
                ("system", "{context}\n"),
                ("system", "Answer the question based on the above context: {question}"),
            ]
        )
        prompt = llm_prompt.format(chat_history=history, context=context, question=question)
        return prompt

    def prompt_user(self, question, history, prompt_template):
        llm_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", prompt_template),
                ("system", "Chat history: \n {chat_history}\n"),
                ("system", "Answer the question: {question}"),
            ]
        )
        prompt = llm_prompt.format(chat_history=history, question=question)
        return prompt

    # Handle all above elements --> prompt for llm
    async def question_handler(self, retriever, bm25_retriever, question_request: QuestionRequest):
        # Get history and generate new question
        history = sql_conn.get_chat_history(question_request.conversation_id)[-8::]
        new_question = self.reformulate_question(question_request.question, history)
        # Nếu prompt template là system rag thì sử dụng retriever để retrieve data, còn không thì thôi
        if retriever:
            if question_request.prompt_template.startswith("__Rag__"):
                context = await self.retriever(new_question, retriever, bm25_retriever)
                prompt = self.prompt_rag(new_question, context, history, question_request.prompt_template)
            else:
                prompt = self.prompt_user(new_question, history, question_request.prompt_template)
            return prompt
        else:
            prompt = self.prompt_user(new_question, history, " ")
            return prompt

    # Streaming response to fastapi endpoint
    async def send_message_openai(self, prompt: str, model: str) -> AsyncIterable[str]:
        callback = AsyncIteratorCallbackHandler()
        self.model_llm = ChatOpenAI(temperature=TEMPERATURE, model=model, streaming=True, callbacks=[callback],
                                    api_key=self.openai_apikey)
        task = asyncio.create_task(
            self.model_llm.ainvoke(prompt)
        )

        try:
            async for token in callback.aiter():
                yield token
        except Exception as e:
            print(f"Caught exception: {e}")
        finally:
            callback.done.set()
        await task

    def send_message_gemini(self, prompt: str, model: str) -> AsyncIterable[str]:
        self.model_llm = ChatGoogleGenerativeAI(temperature=TEMPERATURE, model=model, streaming=True,
                                    api_key=self.gemini_apikey)
        answer = self.model_llm.stream(prompt)
        for i in answer:
            yield i.content

