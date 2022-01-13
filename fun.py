import requests
from pandas import DataFrame
from time import sleep

from undetected_chromedriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By



def get_transactions(wallet, threshold=0):
	transactions = DataFrame(requests.get(
		"https://api.blockchair.com/bitcoin/dashboards/address/{wallet}?transaction_details=true".format(
			wallet=wallet)).json()['data'][wallet]['transactions']).set_index('time')
	transactions.balance_change /= 10e7
	return transactions[transactions.balance_change.abs() > threshold]


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


def get_hour_date(dt):
	date, time = dt.split()
	hour, minute, second = time.split(':')
	return f"{date} {hour}:00:00+00:00"
