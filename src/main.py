#
# Created in 2020 by Jake Johnson and Preston Windfeldt
# Filename: main.py
# Purpose:  Main program that constantly checks if mountain
#           reservations become available on the Ikon pass.
#

import sys
import ikonScraperInterface
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import threading

# MACRO for if web driver should run in headless mode or not
# Must be set to 1 if running on virtual server
HEADLESS = 0

def main():	
	global driver
	"""Main function. Initializes web driver then runs main_loop in a thread
	so that if the main_loop errors out the script can reinitialize the web driver
	and run the main_loop again.
	"""

	while(True):
		# initialize web driver
		if (HEADLESS):
			options = Options()
			options.add_argument('--headless')
			options.add_argument('--disable-gpu')
			options.add_argument("window-size=1024,768")
			options.add_argument("--no-sandbox")
			options.add_argument("--log-level=3");
			driver = webdriver.Chrome(options=options)
		else:
			driver = webdriver.Chrome()

		t = threading.Thread(target=main_loop)
		t.start()
		t.join()

		# close driver
		driver.quit()

	# quit app
	sys.exit()

def main_loop():
	""" Logs into Ikon page then runs infinite loop checking for openings"""

	# list to store dates to reserve
	datesToReserve = []
	# list to store available dates
	availableDates = []
	# mountains to check for availability
	mountainsToCheck = []
	# dictionary to store which months to check. Gets updated.
	monthsToCheck = {
		1: "January",
		2: "February",
		3: "March"
		4: "April",
		5: "May",
		6: "June"
	}

	# set page load timeout
	driver.set_page_load_timeout(20)

	# login to ikon website
	ikonScraperInterface.login(driver)

	# remove months to check that have already been passed
	ikonScraperInterface.updateMonthsToCheck(monthsToCheck)

	# fill up dates lists
	ikonScraperInterface.addDatesToReserveToList(datesToReserve, mountainsToCheck)
	ikonScraperInterface.addAvailableDatesToList(driver, availableDates, mountainsToCheck, monthsToCheck)

	# Constantly check for openings in reservations
	while(True):
		ikonScraperInterface.checkForOpenings(driver, availableDates, datesToReserve, mountainsToCheck, monthsToCheck)
		print("Still checking")

		# sleep so CPU processing doesn't get taken up
		time.sleep(2)


if __name__ == "__main__":
    main()
