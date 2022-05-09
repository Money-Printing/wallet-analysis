from idna import valid_contextj
from streamlit import title, subheader, write, text_input, warning, plotly_chart, number_input, set_page_config, \
	cache, sidebar, checkbox, error, code, info
from fun import *

set_page_config(layout="wide")

coin = sidebar.selectbox(
	"Choose Coin",
	("BTC", "ETH", "USDT", "Bitfinex-BTC")
)

title(f"{coin} Wallet Analyser")


@cache
def get_wallets(coin):
	if coin == 'BTC':
		return "Top 50 Rich Wallets", get_top_wallets_btc(), get_data_btc
	if coin == 'ETH':
		return "Top 100 Rich Wallets", get_top_wallets_eth(), get_data_eth
	if coin == 'USDT':
		return "Top 50 Rich Wallets", get_top_wallets_usdt(), get_data_usdt_erc
	if coin == 'Bitfinex-BTC':
		return "Bitfinex BTC Cold Wallets", get_bitfinex_btc_wallets(), get_data_btc


subheader_text, wallets, get_data = get_wallets(coin)
subheader(subheader_text)
write(wallets)

subheader("Wallet Analysis")
address = text_input("Input Wallet")
offset = number_input("Input offset", min_value=0)
threshold = number_input("Input threshold transaction", min_value=0)
inverse = checkbox('Inverse Deposit/Withdrawal')

if coin == 'USDT':
	info("Only supporting USDT ERC addresses for analysis")

if address:
	try:
		data = get_data(address=address, offset=offset)
	except Exception as e:
		print(e)
		data = []
		error("Error occured in calling APIs. Maybe API limits reached!!")		

	if len(data) == 0:
		warning("No transaction in the wallet matching the filter")
	else:
		data = assign_value_change(data)
		deposits, withdrawals = get_deposits_withdrawals(data, threshold, inverse)

		if coin == 'USDT':
			price_coin = 'BTC'
			deposit_marker_color = 'red'
			withdrawal_marker_color = 'green'
			deposit_action = 'sold'
			withdrawal_action = 'bought'
		else:
			price_coin = coin
			deposit_marker_color = 'green'
			withdrawal_marker_color = 'red'
			deposit_action = 'bought'
			withdrawal_action = 'sold'

		fig = get_chart(coin, price_coin, data, deposits, withdrawals, deposit_marker_color, withdrawal_marker_color)
		plotly_chart(fig, use_container_width=True)

		code(f"Performance is calculated based on:\n{coin} deposit ({deposit_marker_color}): {price_coin} {deposit_action}\n{coin} withdrawal ({withdrawal_marker_color}): {price_coin} {withdrawal_action}")

		if coin == 'USDT':
			usd_spent = sum(withdrawals.transaction)
			usd_purchased = sum(deposits.transaction)
			btc_purchased = sum(withdrawals.transaction / withdrawals.value)
			btc_sold = sum(deposits.transaction / deposits.value)
			coin_left = btc_purchased - btc_sold
		else:
			usd_spent = sum(deposits.transaction * deposits.value)
			usd_purchased = sum(withdrawals.transaction * withdrawals.value)
			coin_left = sum(deposits.transaction) - sum(withdrawals.transaction)

		if coin_left > 0:
			usd_purchased += abs(coin_left) * data.value[-1]
		else:
			usd_spent += abs(coin_left) * data.value[-1]

		profit = (usd_purchased - usd_spent) / usd_spent
		hodl_profit = (data.value[-1] - data.value[0]) / data.value[0]

		write(f"Profit on hodling {price_coin}:", hodl_profit * 100, " %")
		write("Profit on copytrading wallet:", profit * 100, " %")
