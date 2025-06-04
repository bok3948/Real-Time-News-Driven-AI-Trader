import os
from typing import Optional, Dict
from operator import itemgetter

import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.memory import ConversationBufferMemory
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

from pydantic import BaseModel, Field

class StockPrediction(BaseModel):
    """A prediction about a stock's movement based on a news article."""
    ticker: str = Field(description="The ticker symbol of the stock expected to rise due to this news. Return 'N/A' if not applicable.")
    buy_level: int = Field(
        description="The recommended buy level for the stock: 0: Do not buy, stock price will not increase. 1: Do not buy, stock will increase but not strong enough to make profit in short term. 2: Buy, very strong positive news that warrants purchase.",
        ge=0,
        le=2  
    )

def get_prompt_template() -> ChatPromptTemplate:
    """
    Returns a ChatPromptTemplate ready for a stateful conversation.
    """
    system_prompt_text = (
        "You are a short-term stock market trader who makes decisions based on news.\n"
        "\n"
        "You will be given a news article that includes its title, content, publication time, and a link. You can only trade stocks in the US market.\n"
        "\n"
        "Here is what you should consider when making a prediction:\n"
        "\n"
        "- Focus on recent events. If a news article is about an event that happened a long time ago, its impact is likely already reflected in the stock price. In this case, do not buy the stock.\n"
        "- If the news is not about a specific stock but about the broader market, identify the single stock that will be most influenced and make a prediction for it.\n"
        "- If you have analyzed this exact news content in a previous turn in our conversation, do not act on it again.\n"
        "- If the news is not about a specific stock but about the broader market, identify the single stock that will be most influenced and make a prediction for it.\n\n"

        "Examples:\n\n"
        "- If the news is about a stock that surged after an earnings call, the price has already moved. As a trader, you are too late to the party, and should not buy the stock.\n"
        "- If the news is about a recent market-wide event, like 'Trump reduces tariffs on Chinese products,' your task is to predict the most influenced stock and make a decision."

    )
    
    return ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt_text),
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessage(content="{input}")
    ])

class AIPredictor:
    def __init__(self, model_name: str = "gemini-1.5-flash", api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided or set as GOOGLE_API_KEY environment variable.")
        
        self.chain = None
        self.memory = None
        self._init_model()

    def _init_model(self) -> None:
        """
        Initialize the language model and chain.
        
        This method configures the Gemini API, creates the language model with structured output,
        initializes the conversation memory, and builds the chain for inference.
        """
        genai.configure(api_key=self.api_key)
        
        llm_model = ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=self.api_key,
            temperature=0,
        ).with_structured_output(StockPrediction)

        self.memory = ConversationBufferMemory(
            memory_key="chat_history", 
            return_messages=True
        )
        
        prompt_template = get_prompt_template()
 
        self.chain = (
            RunnablePassthrough.assign(

                chat_history=RunnableLambda(self.memory.load_memory_variables) | itemgetter("chat_history")
            )
            | prompt_template
            | llm_model
        )

    def inference(self, news: Dict) -> Optional[Dict]:
        """
        Make a prediction based on news article.
        
        Args:
            news: A dictionary containing news article data, with keys like 'title' and 'content'.
            
        Returns:
            A dictionary containing the prediction results with keys 'ticker' and 'intense',
            or None if an error occurs during prediction.
        """

        title = news.get("title", "N/A")
        content = news.get("content", "No content available")

        news_input_for_model = (
            f"News Title: {title}\n"
            f"Article Content:\n{content}"
        )

        try:

            structured_response = self.chain.invoke({"input": news_input_for_model})


            self.memory.save_context(
                {"input": news_input_for_model},
                {"output": str(structured_response)} 
            )

            print(
                f"[AI Prediction] Ticker={structured_response.ticker}, "
                f"Buy Level={structured_response.buy_level}"
            )
            return {
                "ticker": structured_response.ticker,
                "buy_level": structured_response.buy_level,
            }
        except Exception as e:
            print(f"[AI Prediction] Error during AI model invocation: {e}")
            return None

