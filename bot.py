
import time
import logging
from pybit.unified_trading import HTTP
from decimal import Decimal, ROUND_DOWN
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants
API_KEY = ""
API_SECRET = ""
SYMBOL = "BTCUSDT"
TRIGGER_PRICE = Decimal("63300")
STOP_LOSS_PRICE = Decimal("63301")
TAKE_PROFIT_PRICE = Decimal("63100")
LEVERAGE = 5
AMOUNT = Decimal("1000")

class TradingBot:
    def __init__(self):
        self.session = HTTP(testnet=True, api_key=API_KEY, api_secret=API_SECRET)

    def get_market_price(self) -> Optional[Decimal]:
        try:
            ticker = self.session.get_tickers(category="linear", symbol=SYMBOL)
            return Decimal(ticker["result"]["list"][0]["lastPrice"])
        except Exception as e:
            logger.error(f"Error getting market price: {e}\n")
            return None

    def get_open_order(self) -> Optional[Dict[str, Any]]:
        try:
            orders = self.session.get_open_orders(category="linear", symbol=SYMBOL)
            for order in orders["result"]["list"]:
                if order["orderType"] == "Limit" and order["side"] == "Sell":
                    logger.info(f"Found open order: {order['orderStatus']}")
                    return order
            return None
        except Exception as e:
            logger.error(f"Error checking open orders: {e}\n")
            return None

    def get_order_history(self) -> Optional[list[Dict[str, Any]]]:
        try:
            order_history = self.session.get_order_history(category="linear", symbol=SYMBOL, limit=1)
            return order_history["result"]["list"]
        except Exception as e:
            logger.error(f"Error checking order history: {e}\n")
            return None

    def get_open_position(self) -> Optional[Dict[str, Any]]:
        try:
            positions = self.session.get_positions(category="linear", symbol=SYMBOL)
            for pos in positions["result"]["list"]:
                if pos["takeProfit"] != "":
                    logger.info(f"Found position... {pos['curRealisedPnl']}")
                    return pos
            return None
        except Exception as e:
            logger.error(f"Error checking open positions: {e}\n")
            return None

    def place_order(self) -> bool:
        try:
            qty = (AMOUNT / TRIGGER_PRICE).quantize(Decimal("0.001"), rounding=ROUND_DOWN)
            order = self.session.place_order(
                category="linear",
                symbol=SYMBOL,
                side="Sell",
                orderType="Limit",
                qty=str(qty),
                price=str(TRIGGER_PRICE),
                timeInForce="PostOnly",
                stopLoss=str(STOP_LOSS_PRICE),
                takeProfit=str(TAKE_PROFIT_PRICE),
                triggerPrice=str(TRIGGER_PRICE),
                leverage=str(LEVERAGE),
                triggerDirection=2,
            )
            logger.info(f"New Order placed: {order}")
            return True
        except Exception as e:
            logger.error(f"Error placing order: {e}\n")
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
                        if order_history and order_history[0]["orderStatus"] == "Filled":
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
            logger.error(f"An error occurred in run: {e}\n")

if __name__ == "__main__":
    try:
        bot = TradingBot()
        bot.run()
    except Exception as e:
        logger.error(f"An unhandled exception occurred: {e}\n")
