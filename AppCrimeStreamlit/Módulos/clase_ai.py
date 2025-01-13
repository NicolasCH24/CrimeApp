#  STREAMLIT
import streamlit as st

# TOOLS
from langchain_community.utilities import GoogleSerperAPIWrapper

# LLM
from langchain_google_genai import ChatGoogleGenerativeAI

# AGENT
from langchain.agents import initialize_agent, Tool

# MEMORY - PROMPT
from langchain.prompts import MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate

@st.cache_resource()
def CrearAI():
    # TEMPLATE PROXIMAMENTE MODIFICABLE
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """Tu función principal es retornar exclusivamente una lista de noticias sobre el barrio que el usuario mencione dentro de la Ciudad Autónoma de Buenos Aires.
                Utilizarás el `search_tool` para buscar noticias relevantes.
                Usa el historial del chat ({chat_history}) solo para proporcionar contexto adicional, si es necesario, pero siempre priorizando el formato de respuesta.
                Responde siempre utilizando este formato, sin incluir texto adicional ni explicaciones fuera de contexto:
                
                FORMATO:
                **Inseguridad:** [Lista de noticias relevantes o "No se encontraron noticias relevantes"]
                **Incidente vial:** [Lista de noticias relevantes o "No se encontraron noticias relevantes"]
                **Crimen/delito:** [Lista de noticias relevantes o "No se encontraron noticias relevantes"]
                **Otros:** [Lista de noticias relevantes o "No se encontraron noticias relevantes"]"""
            ),
            ("human", "{input}"),
        ]
    )


    # MODEL
    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.5)

    # SEARCH TOOL
    search = GoogleSerperAPIWrapper(type="news", gl="ar", hl="es-419")
    search_tool = Tool(
        name="search_tool",
        description="Herramienta útil para buscar noticias de la Ciudad Autónoma de Buenos Aires (CABA).",
        func=search.run,
    )
    
    tools = [search_tool]

    # MEMORIA
    memory = ConversationBufferMemory(
        memory_key="chat_history", 
        input_key="input", 
        return_messages=True, 
        output_key="output"
    )
    chat_history = MessagesPlaceholder(variable_name="chat_history")
    
    # INITIALIZE AGENT
    agent = initialize_agent(
        tools,
        llm=model,
        agent="conversational-react-description",
        verbose=True, 
        agent_kwargs={
            "prompt": [prompt],
            "memory_prompts": [chat_history],
            "input_variables": ["input", "chat_history"]
        },
        memory=memory,
        handle_parsing_errors=True
    )

    return agent
