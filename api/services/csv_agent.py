from api.services import *


class CSVAgent:
    def __init__(self, df, model="gpt-4o-mini"):
        self.llm = ChatOpenAI(temperature=0, model=model, streaming=True)
        self.pandas_df_agent = create_pandas_dataframe_agent(
            self.llm,
            df,
            verbose=True,
            agent_type=AgentType.OPENAI_FUNCTIONS,
            allow_dangerous_code=True
        )

    async def get_response(self, question):
        response = await self.pandas_df_agent.arun(question)
        return response
