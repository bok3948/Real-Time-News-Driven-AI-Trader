import os
import asyncio
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderStatus 
from alpaca.data.historical import StockHistoricalDataClient 
from alpaca.data.requests import StockLatestTradeRequest 

load_dotenv()

API_KEY_ID = os.getenv("ALPACA_API_KEY")
API_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

class AlpacaTrader:
    def __init__(self, api_key_id: str, api_secret_key: str, paper: bool = True) -> None:
        """
        Initialize the AlpacaTrader class.
        
        Args:
            api_key_id: Alpaca API key ID.
            api_secret_key: Alpaca API secret key.
            paper: Whether to use paper trading. Defaults to True.
        """
        self.trading_client = TradingClient(api_key_id, api_secret_key, paper=paper)
        self.data_client = StockHistoricalDataClient(api_key_id, api_secret_key)
        self.paper = paper

    def buy_stock(self, symbol: str, qty: int):
        """
        Buy stock using Alpaca API.
        
        Args:
            symbol: The stock symbol to buy.
            qty: The quantity of shares to buy.
            
        Returns:
            The order object if successful, None otherwise.
        """
        try:
            market_order_data = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.GTC
            )
            order = self.trading_client.submit_order(market_order_data)
            print(f"Buy order for {qty} shares of {symbol} submitted successfully.") 
        except Exception as e:
            print(f"Error submitting buy order for {symbol}: {e}")
            return None

        return order

    def sell_stock(self, symbol: str, qty: int):
        """
        Sell stock using Alpaca API.
        
        Args:
            symbol: The stock symbol to sell.
            qty: The quantity of shares to sell.
            
        Returns:
            The order object if successful.
        """
        market_order_data = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.GTC
        )
        order = self.trading_client.submit_order(market_order_data)
        print(f"Sell order for {qty} shares of {symbol} submitted successfully.") # Translated
        return order
    
    def get_cash_balance(self) -> float | None:
        """Retrieves the current cash balance from the Alpaca account."""
        try:
            account_details = self.trading_client.get_account()
            return float(account_details.cash)
        except Exception as e:
            print(f"Error getting cash balance: {e}")
            return None

    def get_latest_price(self, symbol: str) -> float | None:
        """Retrieves the latest trade price for a given stock symbol."""
        try:
            request_params = StockLatestTradeRequest(symbol_or_symbols=symbol)
            latest_trade = self.data_client.get_stock_latest_trade(request_params)
            if symbol in latest_trade and latest_trade[symbol]:
                return float(latest_trade[symbol].price)
            else:
                print(f"No trade data found for {symbol}.")
                return None
        except Exception as e:
            print(f"Error getting latest price for {symbol}: {e}")
            return None

    async def schedule_sell(self, order_id: str, delay_seconds: int):
        """
        Asynchronously sell stock using Alpaca API after a delay time.
        
        Args:
            order_id: The ID of the order to sell.
            delay_seconds: The number of seconds to wait before selling.
        """
        await asyncio.sleep(delay_seconds)
        order = self.trading_client.get_order_by_id(order_id)


        if order.status == OrderStatus.FILLED and order.filled_qty: # Check if order is filled
            try:
                print(f"Scheduled sell for order {order_id}, symbol {order.symbol}, quantity {order.filled_qty}")
                sell_order_response = self.sell_stock(symbol=order.symbol, qty=order.filled_qty)
                print(f"Scheduled sell order submitted for {order.symbol}, ID: {sell_order_response.id}")
            except Exception as e: # Catch specific exceptions if possible
                print(f"Error selling stock {order.symbol} for order {order_id}: {e}")
        elif order.status != OrderStatus.FILLED:
            print(f"Order {order_id} for {order.symbol} was not filled. Sell not executed.")
        else:
            print(f"Order {order_id} for {order.symbol} has no filled quantity. Sell not executed.")


    def cancel_order(self, order_id: str): # Renamed method
        """
        Cancel a specific stock order by its ID and log its details.
        """
        try: 
            order_to_cancel = self.trading_client.get_order_by_id(order_id)
            symbol = order_to_cancel.symbol
            qty = order_to_cancel.qty

            self.trading_client.cancel_order_by_id(order_id) 
            print(f"Cancellation request for order ID {order_id} (Symbol: {symbol}, Qty: {qty}) submitted successfully.") # Translated
        except Exception as e:
            print(f"Error cancelling order {order_id}: {e}")


    async def schedule_cancel_order(self, order_id: str, delay_seconds: int):
        """
        Asynchronously cancel stock order after a specified delay if the order is not filled.
        
        Args:
            order_id: The ID of the order to potentially cancel.
            delay_seconds: The number of seconds to wait before checking if the order should be cancelled.
        """
        await asyncio.sleep(delay_seconds)
        try: # Added try-except block
            order = self.trading_client.get_order_by_id(order_id)
            if order.status != OrderStatus.FILLED: 
                print(f"Order {order_id} is not filled. Attempting to cancel.")
                self.cancel_order(order_id)
            else:
                print(f"Order {order_id} is already filled. Cannot cancel.")
        except Exception as e:
            print(f"Error in scheduled cancel for order {order_id}: {e}")



