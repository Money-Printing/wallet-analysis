from os import getenv
from numpy import NaN, isnan
from pandas import DataFrame, to_datetime
from plotly.subplots import make_subplots
from plotly.graph_objects import Scatter
import requests
from time import sleep
import san
from undetected_chromedriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from dotenv import load_dotenv

load_dotenv()
san.ApiConfig = getenv('san_api')


def get_hour_date(dt):
	date, time = dt.split()
	hour, minute, second = time.split(':')
	return f"{date} {hour}:00:00+00:00"


def get_top_wallets_btc():
	chrome_options = ChromeOptions()
	chrome_options.add_argument("--headless")
	driver = Chrome(options=chrome_options)
	driver.get("https://btc.com/btc/top-address")
	sleep(1)
	rows = driver.find_elements(By.TAG_NAME, "tr")
	top_address = DataFrame(columns=list(map(lambda x: x.text, rows[0].find_elements(By.TAG_NAME, "th"))))
	for row in rows[1:]:
		idx = len(top_address)
		top_address.loc[idx] = list(map(lambda x: x.text, row.find_elements(By.TAG_NAME, "td")))
		top_address.at[idx, 'Address'] = row.find_element(By.TAG_NAME, "a").get_attribute("href").split('/')[-1]
	top_address.set_index('Ranking', inplace=True)
	driver.quit()
	return top_address


def get_top_wallets_eth():
	chrome_options = ChromeOptions()
	chrome_options.add_argument("--headless")
	driver = Chrome(options=chrome_options)
	driver.get("https://etherscan.io/accounts/1?ps=100")
	sleep(1)
	rows = driver.find_elements(By.TAG_NAME, "tr")
	top_address = DataFrame(columns=list(map(lambda x: x.text, rows[0].find_elements(By.TAG_NAME, "th"))))
	for row in rows[1:]:
		idx = len(top_address)
		top_address.loc[idx] = list(map(lambda x: x.text, row.find_elements(By.TAG_NAME, "td")))
	top_address.set_index('Rank', inplace=True)
	driver.quit()
	return top_address


def get_top_wallets_usdt():
	chrome_options = ChromeOptions()
	chrome_options.add_argument("--headless")
	driver = Chrome(options=chrome_options)
	driver.get("https://wallet.tether.to/richlist")
	sleep(1)
	rows = driver.find_elements(By.TAG_NAME, "tr")
	top_address = DataFrame(columns=list(map(lambda x: x.text, rows[0].find_elements(By.TAG_NAME, "th"))))
	for row in rows[1:]:
		idx = len(top_address)
		top_address.loc[idx] = list(map(lambda x: x.text, row.find_elements(By.TAG_NAME, "td")))
	driver.quit()
	return top_address


def get_data_btc(address, offset=0):
	transactions = requests.get(
		"https://api.blockchair.com/bitcoin/dashboards/address/{address}?transaction_details=true".format(
			address=address)).json()['data'][address]['transactions']
	if not transactions:
		return DataFrame()
	data = san.get('price_usd/bitcoin', from_date=get_hour_date(transactions[-1]['time']), interval='1h')
	data['transaction'] = NaN
	if offset:
		transactions = transactions[:offset]
	for transaction in transactions:
		time = get_hour_date(transaction['time'])
		balance_change = transaction['balance_change'] / 1e8
		if isnan(data.loc[time]['transaction']):
			data.loc[time]['transaction'] = balance_change
		else:
			data.loc[time]['transaction'] += balance_change
	return data


def get_data_eth(address, offset=0, threshold=0, sort='desc'):
	etherscan_api = getenv('etherscan_api')
	response = requests.get(
		f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999"
		f"&page=1&offset={offset}&sort={sort}&apikey={etherscan_api}").json()
	transactions = response['result']
	if not transactions:
		return DataFrame()
	data = san.get(
		'price_usd/ethereum',
		from_date=get_hour_date(to_datetime(transactions[-1]['timeStamp'], unit='s').__str__()),
		interval='1h'
	)
	data['transaction'] = NaN
	for transaction in transactions:
		time = get_hour_date(to_datetime(transaction['timeStamp'], unit='s').__str__())
		value = float(transaction['value']) / 1e18
		if transaction['from'] == address:
			value = -value
		if isnan(data.loc[time]['transaction']):
			data.loc[time]['transaction'] = value
		else:
			data.loc[time]['transaction'] += value
	return data


def get_data_usdt():
	return DataFrame()


def assign_value_change(data):
	return data.assign(
		value_change_1h=data.value.shift(-1)-data.value,
		price_change_4h=data.value.shift(-4)-data.value,
		price_change_12h=data.value.shift(-12)-data.value,
		price_change_1d=data.value.shift(-24)-data.value
	)


def get_deposits_withdrawals(data, threshold=0, inverse=False):
	deposit = data[data.transaction > threshold]
	withdrawal = data[data.transaction < -threshold]
	withdrawal.transaction = withdrawal.transaction.abs()
	if inverse:
		return withdrawal, deposit
	return deposit, withdrawal


def get_chart(coin, price, deposit, withdrawal):
	fig = make_subplots(subplot_titles=[f'Wallet Activity vs {coin} Price'])
	fig.add_trace(
		Scatter(
			x=price.index,
			y=price.value,
			mode='lines',
			line_width=1.3,
			fillcolor='rgb(231,138,195)',
			name=f"{coin} Price usd",
			marker_color='rgb(231,38,195)',
			hovertemplate="%{x}<br>Price (USD): %{y}"
		)
	)
	fig.update_layout(
		xaxis=dict(
			title='Timeline',
			rangeselector=dict(
				buttons=list([
					dict(
						count=1,
						label="1m",
						step="month",
						stepmode="backward"
					),
					dict(
						count=6,
						label="6m",
						step="month",
						stepmode="backward"
					),
					dict(
						count=1,
						label="YTD",
						step="year",
						stepmode="todate"
					),
					dict(
						count=1,
						label="1y",
						step="year",
						stepmode="backward"
					),
					dict(
						step="all"
					)
				]),
				bgcolor='black'
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
		template="plotly_dark",
		hoverlabel_namelength=40,
		width=2048,
		height=1080
	)
	deposit_marker_size = (50 * deposit.transaction) / deposit.transaction.max()
	withdrawal_marker_size = (50 * withdrawal.transaction) / withdrawal.transaction.max()
	deposit_marker_size[deposit_marker_size < 15] = 15
	withdrawal_marker_size[withdrawal_marker_size < 15] = 15
	fig.add_traces([
		Scatter(
			x=deposit.index,
			y=deposit.value,
			mode="markers",
			name="Deposits",
			opacity=0.8,
			marker={
				'size': deposit_marker_size,
			},
			customdata=deposit,
			hovertemplate="<br>".join([
				"%{x}",
				"Price (USD): %{y}",
				"Deposit: %{customdata[1]} " + coin,
				"Price Change(1h): %{customdata[2]} USD",
				"Price Change(4h): %{customdata[3]} USD",
				"Price Change(12h): %{customdata[4]} USD",
				"Price Change(1d): %{customdata[5]} USD",
			])
		),
		Scatter(
			x=withdrawal.index,
			y=withdrawal.value,
			mode="markers",
			name="withdrawals",
			opacity=0.8,
			marker={
				'size': withdrawal_marker_size,
			},
			customdata=withdrawal,
			hovertemplate="<br>".join([
				"%{x}",
				"Price (USD): %{y}",
				"Withdrawal: %{customdata[1]} " + coin,
				"Price Change(1h): %{customdata[2]} USD",
				"Price Change(4h): %{customdata[3]} USD",
				"Price Change(12h): %{customdata[4]} USD",
				"Price Change(1d): %{customdata[5]} USD",
			])
		)
	])
	return fig
