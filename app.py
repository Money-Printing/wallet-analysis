from pandas import DataFrame
from streamlit import title, subheader, write, text_input, warning, plotly_chart, number_input, set_page_config, cache

import san
from dotenv import load_dotenv
from os import getenv
load_dotenv()
san.ApiConfig=getenv('san_api')

from fun import get_top_wallets, get_transactions, get_hour_date

from plotly.subplots import make_subplots
from plotly.graph_objects import Scatter

set_page_config(layout="wide")

title("BTC Wallet Analyser")

@cache
def get_cache():
	return get_top_wallets()

top_wallets = get_cache()
subheader("Top 50 Rich Wallets")
write(top_wallets)

subheader("Wallet Analysis")
wallet = text_input("Input Wallet")
threshold = number_input("Input threshold transaction")

if wallet:
	transactions = get_transactions(wallet=wallet, threshold=threshold)
	if len(transactions) == 0:
		warning("No transaction in the wallet matching the filter")
	else:		
		price = san.get('price_usd/bitcoin', from_date=get_hour_date(transactions.index[-1]), interval='1h')
		price=price.assign(price_change_1h=price.shift(-1)-price, price_change_4h=price.shift(-4)-price, price_change_12h=price.shift(-12)-price, price_change_1d=price.shift(-24)-price)

		df = DataFrame(columns=['datetime', 'amount', 'price', 'price_change_1h', 'price_change_4h', 'price_change_12h', 'price_change_1d']).set_index('datetime')
		for dt, data in transactions.iterrows():
			datetime = get_hour_date(dt)
			if datetime in df.index:
				df.at[datetime, 'amount'] += data.balance_change
			else:
				df.loc[datetime] = [data.balance_change] + price.loc[datetime].to_list()
		
		df_deposit = df[df.amount > threshold]
		df_withdrawal = df[df.amount < -threshold]
		df_withdrawal.amount = df_withdrawal.amount.abs()

		fig = make_subplots(subplot_titles=['Wallet Activity vs BTC price'])
		fig.add_trace(
			Scatter(
				x=price.index,
				y=price.value,
				mode='lines',
				line_width=1.3,
				fillcolor='rgb(231,138,195)',
				name="BTC Price usd",
				marker_color='rgb(231,38,195)',
				hovertemplate="%{x}<br>Price (USD): %{y}"
			)
		)
		fig.update_layout(
			xaxis=dict(
				title='Timeline',
				rangeselector=dict(
					buttons=list([
						dict(count=1,
								label="1m",
								step="month",
								stepmode="backward"),
						dict(count=6,
								label="6m",
								step="month",
								stepmode="backward"),
						dict(count=1,
								label="YTD",
								step="year",
								stepmode="todate"),
						dict(count=1,
								label="1y",
								step="year",
								stepmode="backward"),
						dict(step="all")
					]),
					# bgcolor = 'black'
				),
				rangeslider=dict(
					visible=True,
				),
				type="date"
				),
			yaxis=dict(
				title="Price (USD)",
				fixedrange=False
			),
			# template="plotly_dark",
			hoverlabel_namelength=40,
			# width=2048,
			# height=1080
		)
		deposit_marker_size = (50*df_deposit.amount)/df_deposit.amount.max()
		withdrawal_marker_size = (50*df_withdrawal.amount)/df_withdrawal.amount.max()
		deposit_marker_size[deposit_marker_size < 15] = 15
		withdrawal_marker_size[withdrawal_marker_size < 15] = 15
		fig.add_traces([
			Scatter(x=df_deposit.index,
				y=df_deposit.price,
				mode="markers",
				name="Deposits",
				opacity=0.8,
				marker={
					'size': deposit_marker_size,
				},
				customdata=df_deposit,
				hovertemplate="<br>".join([
				"%{x}",
				"Price (USD): %{y}",
				"Deposit: %{customdata[0]} BTC",
				"Price Change(1h): %{customdata[2]} USD",
				"Price Change(4h): %{customdata[3]} USD",
				"Price Change(12h): %{customdata[4]} USD",
				"Price Change(1d): %{customdata[5]} USD",
				])
			),
			Scatter(
				x=df_withdrawal.index,
				y=df_withdrawal.price,
				mode="markers",
				name="withdrawals",
				opacity=0.8,
				marker={
					'size': withdrawal_marker_size,
				},
				customdata=df_withdrawal,
				hovertemplate="<br>".join([
				"%{x}",
				"Price (USD): %{y}",
				"Withdrawal: %{customdata[0]} BTC",
				"Price Change(1h): %{customdata[2]} USD",
				"Price Change(4h): %{customdata[3]} USD",
				"Price Change(12h): %{customdata[4]} USD",
				"Price Change(1d): %{customdata[5]} USD",
				])
			)
		])

		plotly_chart(fig, use_container_width=True)

		usd_spent = sum(df_deposit.amount * df_deposit.price)
		usd_purchased = sum(df_withdrawal.amount * df_withdrawal.price)
		btc_left = sum(df_deposit.amount) - sum(df_withdrawal.amount)
		if btc_left > 0:
			usd_purchased += btc_left * price.value[-1]
		else:
			usd_spent += btc_left * price.value[-1]
		profit = (usd_purchased - usd_spent)/usd_spent

		hodl_profit = (price.value[-1]-price.value[0])/price.value[0]

		write("Profit on hodling:", hodl_profit * 100, " %")
		write("Profit on copytrading wallet:", profit * 100, " %")