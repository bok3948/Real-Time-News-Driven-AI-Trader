
from typing import Dict

class Article: 
    """
    A class to represent a news article.
    
    Attributes:
        title (str): The title of the article.
        url (str): The URL of the article.
        date (str): The date the article was published.
        content (str): The content of the article.
        source (str): The source of the article.
    """
    
    def __init__(self, title: str = "N/A", url: str = "N/A", date: str = "N/A", 
                 content: str = "N/A", source: str = "N/A") -> None:
        """
        Initialize an Article instance.
        
        Args:
            title: The title of the article. Defaults to "N/A".
            url: The URL of the article. Defaults to "N/A".
            date: The date the article was published. Defaults to "N/A".
            content: The content of the article. Defaults to "N/A".
            source: The source of the article. Defaults to "N/A".
        """
        self.title = title
        self.url = url
        self.date = date
        self.content = content
        self.source = source

    def __repr__(self) -> str:
        """
        Return a string representation of the Article.
        
        Returns:
            A string representation of the Article.
        """
        return f"Article(title={self.title}, url={self.url}, date={self.date}, content={self.content[:30]})"
    
    def to_dict(self) -> Dict[str, str]:
        """
        Convert the Article instance to a dictionary.
        
        Returns:
            A dictionary representation of the Article.
        """
        return {
            "title": self.title,
            "url": self.url,
            "date": self.date,
            "content": self.content,
            "source": self.source
        }
    
    def to_str(self) -> str:
        """
        Convert the Article instance to a string.
        
        Returns:
            A string representation of the Article.
        """
        return f"Title: {self.title}\nURL: {self.url}\nDate: {self.date}\nContent: {self.content}\nSource: {self.source}"
