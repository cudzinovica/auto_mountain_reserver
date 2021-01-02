#
# Copyright 2020 Jake Johnson and Preston Windfeldt
# Filename: ikonScraperInterface.py
# Purpose:  Provide web scraping interface for interacting with 
#           Ikon website
#

import sys
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import calendar
import mysql.connector
from mysql.connector import Error
from mysql.connector import errorcode
import smtplib
import emailInterface
import time
import datetime

# class name if the day is available
AVAILABLE = 'DayPicker-Day'
# class name if available and day is today
AVAILABLE_TODAY = 'DayPicker-Day DayPicker-Day--today'

# mountains to check for availability
mountainsToCheck = ["Arapahoe Basin", "Aspen Snowmass", "Winter Park Resort"]
# months to check for availability
monthsToCheck = {
	1: "January",
	2: "February",
	3: "March",
	4: "April",
	5: "May",
	6: "June"
}
# year to check
year = 2021

def login(driver, password):
	"""Logs into Ikon website and clicks the 'make reservation' button.
	"""
	# open login page
	url = "https://account.ikonpass.com/en/login"
	driver.get(url)

	# send login parameters
	username = driver.find_element_by_name('email')
	username.send_keys('jjohnson11096@gmail.com')
	password = driver.find_element_by_name('password')
	password.send_keys(sys.argv[1])
	password.send_keys(Keys.RETURN)

	# click 'Make a Reservation' button
	try:
		# wait for page to load
		resButton = WebDriverWait(driver, 20).until(
		EC.presence_of_element_located((By.XPATH, '//span[text()="Make a Reservation"]')))
	except:
		print("Error: Timed out")
		sys.exit()
	driver.execute_script("arguments[0].click();", resButton)

def selectMountain(driver, mountain):
	"""Selects mountain on the 'make reservation' page. From here, selectMonth() and
	then isDayAvailable() can be called.
	"""
	# select mountain
	try:
		# wait for page to load
		mountain = WebDriverWait(driver, 20).until(
		EC.presence_of_element_located((By.XPATH, '//span[text()="' + mountain + '"]')))
	except:
		print("Error: Timed out")
		sys.exit()
	driver.execute_script("arguments[0].click();", mountain)

	# click 'Continue' button
	try:
		# wait for page to load
		contButton = WebDriverWait(driver, 20).until(
		EC.presence_of_element_located((By.XPATH, '//span[text()="Continue"]')))
	except:
		print("Error: Timed out")
		sys.exit()
	driver.execute_script("arguments[0].click();", contButton)

def selectMonth(driver, month, year):
	"""Selects month by bringing scraper to the page displaying the dates for that
	month.
	"""
	# check what month is currently being checked on Ikon site.
	try:
		# wait for page to load
		monthBeingChecked = WebDriverWait(driver, 20).until(
		EC.presence_of_element_located((By.XPATH, '//span[@class="sc-pckkE goPjwB"]')))
	except:
		print("Error: Timed out")
		sys.exit()

	# loop through months until correct month is being checked. 
	# Will start from month entered and increment until June 2021.
	while (monthBeingChecked.get_attribute('innerHTML') != (month + ' ' + str(year))):
		# if we have reached June and that was not desired month, return
		if monthBeingChecked.get_attribute('innerHTML') == ("June 2021") and month != "June":
			print("Error: Failed to select month")
			return

		# go to next month
		nextMonthButton = driver.find_element(By.XPATH, '//i[@class="amp-icon icon-chevron-right"]')
		driver.execute_script("arguments[0].click();", nextMonthButton)

		try:
			monthBeingChecked = WebDriverWait(driver, 20).until(
			EC.presence_of_element_located((By.XPATH, '//span[@class="sc-pckkE goPjwB"]')))
		except:
			print("Error: Timed out")
			sys.exit()

def isDayAvailable(driver, month, day, year):
	"""Checks if a day is available. The scraper must be on the make reservation
	page with the dates available to check (ie selectMonth() must be called first).
	"""
	# parse monthInput since that is how it is labeled in the Ikon page HTML
	month = month[0:3]

	# format day, if it's single digits, prepend with 0 since that is Ikon's site format
	dayFormatted = str(day)
	if (day < 10):
		dayFormatted = "0" + dayFormatted

	# check if day is available by reading element class. Class will be 'DayPicker-Day'
	# if available
	try:
		# wait for page to load
		dayElement = WebDriverWait(driver, 20).until(
	    EC.presence_of_element_located((By.XPATH, '//div[contains(@aria-label,"' + month + ' ' + dayFormatted + '")]')))
	except:
		print("Error: Timed out")
		sys.exit()

	# print if day is available or not
	if (dayElement.get_attribute('class') == AVAILABLE or dayElement.get_attribute('class') == AVAILABLE_TODAY):
		#print(month + " " + dayFormatted + " AVAILABLE")
		return True
	else:
		#print(month + " " + dayFormatted + " RESERVED")
		return False

def addAvailableDatesToList(driver, datesAvailable):
	"""Scrapes Ikon site and adds available dates to list.
	"""
	# check reserved dates for each mountain. Only check Jan-June 
	# TODO: make this scalable to whatever current year is
	for mountain in mountainsToCheck:
		# reload to allow new mountain selection
		url = "https://account.ikonpass.com/en/myaccount/add-reservations/"
		driver.get(url)
		selectMountain(driver, mountain)
		for month in monthsToCheck:
			selectMonth(driver, monthsToCheck[month], year)
			# check each days availability and add to list
			for day in range(1, calendar.monthrange(year, month)[1] + 1):
				if isDayAvailable(driver, monthsToCheck[month], day, year):
					datesAvailable.append([mountain, month, day, year])

def checkForOpenings(driver, datesAvailable, datesToReserve):
	"""Checks if any reserved days have become available by scraping Ikon site and comparing
	to the current stored available dates in our list
	"""
	# check current available dates
	for mountain in mountainsToCheck:
		# reload to allow new mountain selection
		url = "https://account.ikonpass.com/en/myaccount/add-reservations/"
		driver.get(url)
		selectMountain(driver, mountain)

		for month in monthsToCheck:
			selectMonth(driver, monthsToCheck[month], year)

			for day in range(1, calendar.monthrange(year, month)[1] + 1):
				if isDayAvailable(driver, monthsToCheck[month], day, year):
					# reserve day if desired
					if [mountain, month, day, year] in datesToReserve:
						reserveDay(driver, monthsToCheck[month], day, year)
						# refresh scraper
						selectMountain(driver, mountain)
						selectMonth(driver, monthsToCheck[month], year)
						# remove from list
						datesToReserve.remove([mountain, month, day, year])

					# if day is not stored as available send alert, add to available dates
					if [mountain, month, day, year] not in datesAvailable:
						# get day of week
						dayOfWeek = datetime.date(year, month, day).strftime("%A")
						# send alerts
						emailInterface.sendEmailAlert("jjohnson11096@gmail.com", mountain, monthsToCheck[month], str(day), str(year), dayOfWeek)
						emailInterface.sendEmailAlert("prestonwindfeldt@gmail.com", mountain, monthsToCheck[month], str(day), str(year), dayOfWeek)
						# add to list
						datesAvailable.append([mountain, month, day, year])
				else:
					# if day is stored as available but is no longer available, remove it from list
					if [mountain, month, day, year] in datesAvailable:
						datesAvailable.remove([mountain, month, day, year])

def reserveDay(driver, month, day, year):
	"""Reserves a day in Ikon if available.
	"""
	# parse monthInput since that is how it is labeled in the Ikon page HTML
	month = month[0:3]

	# format day, if it's single digits, prepend with 0 since that is Ikon's site format
	dayFormatted = str(day)
	if (day < 10):
		dayFormatted = "0" + dayFormatted

	# Select the day
	# if available
	try:
		# wait for page to load
		dayElement = WebDriverWait(driver, 20).until(
	    EC.presence_of_element_located((By.XPATH, '//div[contains(@aria-label,"' + month + ' ' + dayFormatted + '")]')))
	except:
		print("Error: Timed out")
		sys.exit()

	driver.execute_script("arguments[0].click();", dayElement)

	# click save button
	try:
		# wait for page to load
		saveButton = WebDriverWait(driver, 20).until(
		EC.presence_of_element_located((By.XPATH, '//span[text()="Save"]')))
	except:
		print("Error: Timed out no save")
		sys.exit()
	driver.execute_script("arguments[0].click();", saveButton)

	# give time for button click
	time.sleep(1)

	# click confirm button
	try:
		# wait for page to load
		confirmButton = WebDriverWait(driver, 20).until(
		EC.presence_of_element_located((By.XPATH, '//span[text()="Continue to Confirm"]')))
	except:
		print("Error: Timed out no confirm")
		sys.exit()
	driver.execute_script("arguments[0].click();", confirmButton)

	# click confirm checkbox
	try:
		# wait for page to load
		confirmCheckbox = WebDriverWait(driver, 20).until(
		EC.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/main/section[2]/div/div[2]/div[4]/div/div[4]/label/input')))
	except:
		print("Error: Timed out no checkbox")
		sys.exit()
	driver.execute_script("arguments[0].click();", confirmCheckbox)

	# give time for button click
	time.sleep(1)

	# click confirm button again
	try:
		# wait for page to load
		confirmButton = WebDriverWait(driver, 20).until(
		EC.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/main/section[2]/div/div[2]/div[4]/div/div[5]/button/span')))
	except:
		print("Error: Timed out no checkbox")
		sys.exit()
	driver.execute_script("arguments[0].click();", confirmButton)

	# return to make reservation page
	url = "https://account.ikonpass.com/en/myaccount/add-reservations/"
	driver.get(url)
