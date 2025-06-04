# News-Driven-AI-Trader

Real-time AI-driven stock trading bot. This Python project automatically scrapes live financial news, leverages Gemini AI for sentiment-based stock prediction, and executes trades via the Alpaca API. It's designed for rapid, event-driven trading, reacting instantly to market-moving news.

***

## Features

* **Real-Time News Analysis**: Automatically scrapes financial news from top sources.
* **AI-Powered Predictions**: Uses Google's Gemini AI to analyze news sentiment and predict stock price movements (buy, sell, or hold).
* **Automated Trading**: Seamlessly executes trades through the Alpaca API without manual intervention.
* **Event-Driven**: Built to react quickly to breaking news that can impact the market.

***

## How It Works

1.  **News Scraping**: The bot continuously monitors and scrapes the latest articles from financial news websites.
2.  **Sentiment Analysis**: Each relevant news article is sent to the Gemini AI API. The AI analyzes the content and returns a sentiment score and a trading decision (e.g., `BUY`, `SELL`, `HOLD`).
3.  **Trade Execution**: Based on the AI's decision, the bot places a corresponding order through the Alpaca trading API.

***

## Getting Started

Follow these steps to set up and run the trading bot.

### Prerequisites

* An **Alpaca Trading Account**.
* A **Google AI API Key**.

### Installation & Usage

1.  **Set Up Your Accounts & API Keys**
    * **Alpaca**: Create an account at [alpaca.markets](https://alpaca.markets/). Navigate to your dashboard to find your **API Key ID** and **Secret Key**.
    * **Google AI**: Get your Gemini API key from the [Google AI Studio](https://ai.google.dev/gemini-api/docs/api-key).

2.  **Clone the Repository**
    Clone this project to your local machine.
    ```bash
    git clone https://github.com/bok3948/Real-Time-News-Driven-AI-Trader.git
    cd News-Driven-AI-Trader
    ```

3.  **Configure Environment Variables**
    Create a file named `.env` in the root directory of the project. Copy and paste the following, replacing the placeholder values with your actual keys.
    ```env
    # Alpaca API Keys
    APCA_API_KEY_ID=your_alpaca_api_key_id
    APCA_API_SECRET_KEY=your_alpaca_secret_key

    # Google Gemini API Key
    GOOGLE_API_KEY=your_google_api_key
    ```

4.  **Install Dependencies**
    Install the required Python packages using the `requirements.txt` file.
    ```bash
    pip install -r requirements.txt
    ```

5.  **Run the Bot**
    Start the main application script.
    ```bash
    python main.py
    ```
    The bot will now be running, actively scraping news and executing trades based on AI analysis.

***

## Disclaimer

⚠️ **Trading financial instruments involves significant risk. This project is for educational and experimental purposes only. Use it at your own risk. The creators are not responsible for any financial losses you may incur.**
