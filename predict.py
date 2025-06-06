import os
from typing import Optional, Dict
from pydantic import BaseModel, Field

from langchain.chat_models import init_chat_model
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import  HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph

class StockPrediction(BaseModel):
    """A prediction about a stock's movement based on a news article.
    
    Attributes:
        ticker: The ticker symbol of the stock expected to rise due to this news.
        buy_level: The recommended buy level for the stock on a scale of 0-2.
    """
    ticker: str = Field(description="The ticker symbol of the stock expected to rise due to this news. Return 'N/A' if not applicable.")
    buy_level: int = Field(
        description="The recommended buy level for the stock: 0: Do not buy, stock price will not increase. 1: Do not buy, stock will increase but not strong enough to make profit in short term. 2: Buy, very strong positive news that warrants purchase.",
        ge=0,
        le=2  
    )


def get_dummy_news() -> str:
    """Returns a dummy news article for testing purposes.
    
    Creates a sample news dictionary with title, URL, date, content, and source,
    then formats it as a string.
    
    Returns:
        str: Formatted news article as a string.
    """
    news_dict = {
        'title': 'Dollar mired in US economic weakness and trade limbo', 
        'url': 'https://finance.yahoo.com/news/dollar-mired-us-economic-weakness-014950162.html', 
        'date': '2025-06-06T01:49:50.000Z', 
        'content': 'By Rae Wee\nSINGAPORE (Reuters) -The dollar was headed for a weekly loss on Friday... (중략)', 
        'source': 'Yahoo Finance'
    }
    
    return f"Title: {news_dict['title']}\nDate: {news_dict['date']}\nContent: {news_dict['content']}\nSource: {news_dict['source']}\nURL: {news_dict['url']}"


def get_prompt_template() -> ChatPromptTemplate:
    """Returns a ChatPromptTemplate for stock trading based on news.
    
    Creates a system prompt that instructs the model to analyze news articles
    and make stock trading decisions, then wraps it in a ChatPromptTemplate.
    
    Returns:
        ChatPromptTemplate: A template for generating prompts for the AI model.
    """
    system_prompt = """
     You are a short-term stock market trader who makes decisions based on news.

     You will be given a news article that includes its title, content, publication time, and a link. You can only trade stocks in the US market.

     Here is what you should consider when making a prediction:

     - Focus on recent events. If a news article is about an event that happened a long time ago, its impact is likely already reflected in the stock price. In this case, do not buy the stock.
     - If the news is not about a specific stock but about the broader market, identify the single stock that will be most influenced and make a prediction for it.
     - If you have analyzed this exact news content in a previous turn in our conversation, do not act on it again.

     Examples:
     - If the news is about a stock that surged after an earnings call, the price has already moved. As a trader, you are too late to the party, and should not buy the stock.
     - If the news is about a recent market-wide event, like 'Trump reduces tariffs on Chinese products,' your task is to predict the most influenced stock and make a decision.
    """

    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])


class AIPredictor:
    """Predicts stock movements based on news articles using Gemini AI model.
    
    This class manages a LangGraph workflow that processes news articles and
    predicts which stocks are likely to rise based on the news content.
    
    Attributes:
        model_name: Name of the Gemini model to use.
        api_key: Google API key for accessing Gemini models.
        thread_id: Unique identifier for conversation thread.
        app: Compiled LangGraph application.
    """
    def __init__(self, model_name: str = "gemini-2.0-flash", api_key: Optional[str] = None):
        """Initializes the AIPredictor with a specified model.
        
        Args:
            model_name: The name of the Gemini model to use for predictions.
            api_key: Google API key for accessing Gemini models.
                If not provided, it will look for GOOGLE_API_KEY in environment.
                
        Raises:
            ValueError: If API key is not provided and not in environment.
        """
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided or set as GOOGLE_API_KEY environment variable.")
        
        self.thread_id = "abc123_fixed"
        self.app = None
        self._init_model()
        
    def _init_model(self) -> None:
        """Initializes the language model and prediction workflow.
        
        Sets up the Gemini model with structured output, creates a LangGraph workflow,
        and initializes it with a sample news article.
        """
        model = init_chat_model(
            self.model_name, 
            model_provider="google_genai",
        ).with_structured_output(StockPrediction)
        workflow = StateGraph(MessagesState)

        def call_model(state: MessagesState):
            response = model.invoke(state["messages"])
            response_content = response.model_dump_json()
            response = AIMessage(content=response_content)
            return {"messages": response}

        workflow.add_node("model", call_model)
        workflow.add_edge(START, "model")

        memory = MemorySaver()
        self.app = workflow.compile(checkpointer=memory)

        prompt_template = get_prompt_template()
        news = get_dummy_news()
        
        # Create a human message with the news content
        messages = [HumanMessage(content=news)]
        
        # Format the prompt with the messages
        prompt = prompt_template.invoke({"messages": messages})
        input_messages = prompt.to_messages()

        self.app.invoke({"messages": input_messages}, {"configurable": {"thread_id": self.thread_id}})


    def inference(self, news: str) -> Optional[Dict]:            
        """Makes a stock prediction based on a news article.
        
        Args:
            news: A dictionary containing news article information.
                Should have 'title' and 'content' keys.
                
        Returns:
            Optional[Dict]: The model's response containing the prediction,
                or None if an error occurred.
        """

        try:
            message = HumanMessage(content=news)
            output = self.app.invoke({"messages": [message]}, {"configurable": {"thread_id": self.thread_id}})

            return output
        except Exception as e:
            print(f"[AI Prediction] Error during AI model invocation: {e}")
            return None
