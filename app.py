from streamlit import title, subheader, write, text_input, warning, plotly_chart, number_input, set_page_config, \
	cache, sidebar, checkbox
from fun import *

set_page_config(layout="wide")

coin = sidebar.selectbox(
	"Choose Coin",
	("BTC", "ETH", "USDT")
)

title(f"{coin} Wallet Analyser")


@cache
def get_top_wallets(coin):
	if coin == 'BTC':
		return get_top_wallets_btc()
	if coin == 'ETH':
		return get_top_wallets_eth()
	if coin == 'USDT':
		return get_top_wallets_usdt()


top_wallets = get_top_wallets(coin)
subheader("Top 50 Rich Wallets")
write(top_wallets)

subheader("Wallet Analysis")
address = text_input("Input Wallet")
offset = number_input("Input offset", min_value=0)
threshold = number_input("Input threshold transaction", min_value=0)
inverse = checkbox('Inverse Deposit/Withdrawal')

if address:
	data = DataFrame()
	if coin == 'BTC':
		data = get_data_btc(address=address, offset=offset)
	elif coin == 'ETH':
		data = get_data_eth(address=address, offset=offset, threshold=threshold)
	elif coin == 'USDT':
		data = get_data_usdt()

	if len(data) == 0:
		warning("No transaction in the wallet matching the filter")
	else:
		data = assign_value_change(data)
		deposits, withdrawals = get_deposits_withdrawals(data, threshold, inverse)
		fig = get_chart(coin, data, deposits, withdrawals)
		plotly_chart(fig, use_container_width=True)

		hodl_profit = (data.value[-1] - data.value[0]) / data.value[0]
		usd_spent = sum(deposits.transaction * deposits.value)
		usd_purchased = sum(withdrawals.transaction * withdrawals.value)
		coin_left = sum(deposits.transaction) - sum(withdrawals.transaction)
		if coin_left > 0:
			usd_purchased += coin_left * data.value[-1]
		else:
			usd_spent += coin_left * data.value[-1]
		profit = (usd_purchased - usd_spent) / usd_spent

		write("Profit on hodling:", hodl_profit * 100, " %")
		write("Profit on copytrading wallet:", profit * 100, " %")
