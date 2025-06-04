import os
import time
import argparse
import asyncio 
from collections import deque
from dotenv import load_dotenv
from collections import deque

from alpaca_trader import AlpacaTrader

from predict import AIPredictor
from news.registry import get_crawler


def get_args_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser for the application.
    
    Returns:
        An ArgumentParser object configured with the application's command-line arguments.
    """
    parser = argparse.ArgumentParser(description='News Driven Trader', add_help=False)

    parser.add_argument('--paper', default=True, type=bool,)

    parser.add_argument('--model_name', default='gemini-2.0-flash-exp', type=str,)
    #"gemini-1.5-flash-latest,     #gemini-2.5-pro-preview-05-06"
    parser.add_argument('--news_src', nargs='+', default=['yahoo_finance'],
                        help='List of news sources to use ' \
                        'available options: ' \
                        'yahoo_finance, (https://finance.yahoo.com/topic/latest-news/)' 
                        )
    return parser


async def main(args: argparse.Namespace) -> None:
    """
    Main function that runs the news-based trading system.
    
    Args:
        args: Command-line arguments passed to the application.
    """

    load_dotenv(override=True)
    ALPACA_API_KEY_ID = os.getenv("ALPACA_API_KEY")
    ALPACA_API_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    alpaca_trader = AlpacaTrader(ALPACA_API_KEY_ID, ALPACA_API_SECRET_KEY, paper=args.paper)


    news_crawlers = [get_crawler(src) for src in args.news_src]
    title_cache = deque(maxlen=10)
    for crawler in news_crawlers:
        try:
            news = crawler()
        except Exception as e:
            print(f"[ERROR] Error fetching news from {crawler.__name__}: {e}")
            continue
        title_cache.append(news.title)

    print("Starting news-based trading during US market hours...")
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] waiting for new news ...")
    
    while True:

        new_news = deque([]) 

        for crawler in news_crawlers:
            try:
                news = crawler()
            except Exception as e:
                print(f"[ERROR] Error fetching news from {crawler.__name__}: {e}")
                continue
            if news.title not in title_cache:
                title_cache.append(news.title)
                new_news.append(news)  
            else:
                continue

        if not new_news:
            await asyncio.sleep(10)
            continue

        while new_news:
            latest_article = new_news.popleft()
            title = latest_article.title
            print()
            print("-" * 50)
            print(f"New news detected: {title}")

            ai_predictor = AIPredictor(
                model_name=args.model_name,
                api_key=GOOGLE_API_KEY, 
            )

            article_dict = latest_article.to_dict() 
            prediction = ai_predictor.inference(news=article_dict)

            predicted_ticker = prediction.get('ticker') if prediction else "N/A"
            predicted_buy_level = prediction.get('buy_level', 0) if prediction else 0
            
            if isinstance(predicted_ticker, str) and predicted_ticker != "N/A" and predicted_buy_level > 1:
                if not getattr(alpaca_trader.trading_client.get_clock(), 'is_open', False):
                    print("[INFO] Market is closed. Waiting for market to open...")
                    await asyncio.sleep(60)  # Check every minute
                    continue
                
                # Use Alpaca buying_power instead of cash_balance for qty calculation
                account = alpaca_trader.trading_client.get_account()
                buying_power = getattr(account, 'buying_power', None)
                try:
                    buying_power = float(buying_power) if buying_power is not None else 0.0
                except Exception:
                    buying_power = 0.0
                latest_price = alpaca_trader.get_latest_price(predicted_ticker)
                if latest_price is None:
                    print(f"No trade data found for {predicted_ticker}. (Check ticker spelling, Alpaca support, or API error)")
                    continue
                qty = int((buying_power * 0.3) / latest_price)
                print(f"[INFO] Buying power: {buying_power}, Latest price: {latest_price}, Qty: {qty}")
                if qty == 0:
                    print(f"No sufficient buying power to buy {predicted_ticker}.")
                    continue
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Attempting to buy {qty} shares of {predicted_ticker} at ${latest_price:.2f} each.")
                buy_order_response = alpaca_trader.buy_stock(predicted_ticker, qty) 
                order_id = getattr(buy_order_response, 'id', None)
                if order_id:
                    print(f"Buy order successful ")
                    # Keep existing scheduled sell/cancel logic
                    asyncio.create_task(alpaca_trader.schedule_cancel_order(
                        order_id=order_id,
                        delay_seconds=60
                    ))
                    #print(f"Scheduled cancellation of order {order_id} in 60 seconds.")
                    #asyncio.create_task(alpaca_trader.schedule_sell(order_id=order_id, delay_seconds=300))
                else:
                    print(f"Buy order failed: {buy_order_response}")



            print("-" * 50)
            print()
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Checking for latest news...")
            await asyncio.sleep(10)


if __name__ == "__main__":
    parser = get_args_parser()
    args = parser.parse_args()
    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        print("[INFO] Trading loop terminated by user.")



