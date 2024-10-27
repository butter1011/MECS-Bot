
import time
import logging
from pymexc import futures
from decimal import Decimal, ROUND_DOWN
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants
API_KEY = "mx0vgl4HISws5aHQvh"
API_SECRET = "6e828400061d4c52a03dda483a8ea244"
SYMBOL = "BTC_USDT"
TRIGGER_PRICE = Decimal("63100")
STOP_LOSS_PRICE = Decimal("63099")
TAKE_PROFIT_PRICE = Decimal("63200")
LEVERAGE = 5
AMOUNT = Decimal("1000")

class TradingBot:
    def __init__(self):
        self.client = futures.HTTP(api_key=API_KEY, api_secret=API_SECRET)

    def get_market_price(self) -> Optional[Decimal]:
        try:
            ticker = self.client.ticker(symbol=SYMBOL)
            return Decimal(ticker['data']['lastPrice'])
        except Exception as e:
            logger.error(f"Error getting market price: {e}")
            return None

    def get_open_order(self) -> Optional[Dict[str, Any]]:
        try:
            orders = self.client.open_orders(symbol=SYMBOL)
            for order in orders['data']:
                if order["orderType"] == "LIMIT" and order["side"] == "SELL":
                    logger.info(f"Found open order: {order['status']}")
                    return order
            return None
        except Exception as e:
            logger.error(f"Error checking open orders: {e}")
            return None

    def get_open_position(self) -> Optional[Dict[str, Any]]:
        try:
            positions = self.client.open_positions(symbol=SYMBOL)  # Changed from position_info to get_position_risk
            for pos in positions['data']:
                if pos["positionAmt"] != "0":
                    logger.info(f"Found position... PNL: {pos['unrealizedProfit']}")
                    return pos
            return None
        except Exception as e:
            logger.error(f"Error checking open positions: {e}")
            return None

    def get_order_history(self) -> Optional[list[Dict[str, Any]]]:
        try:
            order_history = self.client.history_orders(symbol=SYMBOL, page_size=1)  # Changed from order_history to get_orders
            return order_history['data']
        except Exception as e:
            logger.error(f"Error checking order history: {e}")
            return None

    def place_order(self) -> bool:
        try:
            order = self.client.order(# Changed from place_order to create_order
                symbol=SYMBOL,
                price=str(TRIGGER_PRICE),
                vol=str(AMOUNT),
                leverage=LEVERAGE,
                side=1,
                type=2,
                open_type=1,
                stop_loss_price=str(STOP_LOSS_PRICE),
                take_profit_price=str(TAKE_PROFIT_PRICE),
            )
            logger.info(f"New Order placed: {order}")
            return True
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return False

    def run(self):
        try:
            is_opened_position = False

            while True:
                market_price = self.get_market_price()
                if not market_price:
                    time.sleep(5)
                    continue

                logger.info(
                    f"Market price: {market_price}, trigger price: {TRIGGER_PRICE}, "
                    f"stop loss price: {STOP_LOSS_PRICE}, take profit price: {TAKE_PROFIT_PRICE}"
                )

                order_placed = self.get_open_order()
                open_position = self.get_open_position()
                order_history = self.get_order_history()

                if open_position:
                    is_opened_position = True
                else:
                    if is_opened_position:
                        logger.info("Closing position...")
                        if order_history and order_history[0]["status"] == "FILLED":
                            logger.warning("Position filled")
                            break
                        else:
                            logger.warning("Position closed")
                            order_placed = self.place_order()

                        is_opened_position = False
                    elif not order_placed:
                        order_placed = self.place_order()

                time.sleep(1)
        except Exception as e:
            logger.error(f"An error occurred in run: {e}")

if __name__ == "__main__":
    try:
        bot = TradingBot()
        bot.run()
    except Exception as e:
        logger.error(f"An unhandled exception occurred: {e}")
