# Chatbot
MODEL_LLM = "gpt-4o-mini"
TEMPERATURE = 0
MODEL_EMBEDDING = "text-embedding-3-large"
PROMPT_TEMPLATE = """__Rag__
        You are an AI chatbot that answers questions based on context retrieved below. Follow the rules below:
        1. **If relevant data is available:**
        - Use the context to provide an informative and accurate answer. Be concise and direct in your response and just use the information in the context below!
        2. **If the relevant data is not needed to answer:**
        - Respond in a friendly, casual, and conversational manner. You can greet the user or share light-hearted, positive thoughts.
        3. **If no relevant data is available:**
        - Apologize politely and explain that you do not have enough information to answer the question at this time.
        You can ONLY uses information contained in the context below and does not hallucinate.
        4. **If you need to display math symbols and expressions, put them in double dollar signs "$$" (example: $$ x - 1 $$)**
        """

REGENERATE_QUESTION_PROMPT = """DO NOT answer the input. 
Please reformulate the user's input based on the conversation history, maintaining the original question format and context. 
Identify any reference to previously mentioned subjects and replace it with the specific context. 
Do not add new information or fabricate the subject. 
If the input question references a prior entity (e.g., 'he' or 'it'), replace it with the full entity name from the history.
Keep the final output concise and clearly tied to the previous conversation.
Make sure to identify clearly what is social greeting input to keep the input remain the same , what is not to reformulate the input.\n
"""

# Retriever
SEARCH_KWARGS = {'k': 25, 'score_threshold': 0.1, 'sorted': True}
SEARCH_TYPE = "similarity_score_threshold"

# Vector database
SYSTEM_DATABASE = "./vectorstores/db_faiss"
USER_DATABASE = "./vectorstores/db_faiss_for_user"

SYSTEM_DOCUMENT = "./data/data_system"
USER_DOCUMENT = "./data/data_user"

# Load data
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Postgresql for memory storing
DATABASE = 'rag_1'
HOST = 'postgres_db'
PORT = '5432'
USER = 'bojjoo'
PASSWORD = '12345678'

# DATABASE = 'rag'
# HOST = 'localhost'
# PORT = '5432'
# USER = 'postgres'
# PASSWORD = '12345678'
