#  STREAMLIT
import streamlit as st

# AGENTE
from langchain.agents.agent_types import AgentType
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

# LLM
from langchain_google_genai import ChatGoogleGenerativeAI

@st.cache_resource()
def DataframeAgent(_df):
    prefix = """Retornas recomendaciones al usuario de no más de 4 renglones en base a la información de tu df. EN ESPAÑOL."""
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.8,
        max_tokens=None,
        timeout=30,
        max_retries=10,
    )

    agent = create_pandas_dataframe_agent(llm=llm,
                            df=_df,
                            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                            allow_dangerous_code=True,
                            prefix= prefix,
                            handle_parsing_errors=True,
                            max_iterations=15,
                            max_execution_time=45,
                            verbose=True)
    return agent