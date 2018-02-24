import ctypes
import codecs
import time
import selenium
import re
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

def writeBug(err):
	file = open("stderr.txt", "w+")
	file.write(err)
	file.close()

#################################################################################################
# opens and logs into illyriad, should be split iunto parts to login to multuiple profiles		#
#################################################################################################
def openAPage(document="html.txt"):
	driver = webdriver.Chrome("C:\Program Files (x86)\chromedriver_win32\chromedriver.exe")
	driver.get("https://elgea.illyriad.co.uk/Account/LogOn")
	time.sleep(.75)

	return driver

#################################################################################################
# main section of functions																		#
#################################################################################################

# Obtains and stores information about a city
# later if raspberry pi can handle it I could have both accounts open
# and updating from this script at the same time
class City:
	def __init__(self, driver, waitTime=.75, timeout=1.5):
		self.timeout = timeout
		self.waitTime = waitTime
		self.driver = driver
		self.driver.implicitly_wait(self.waitTime)
		self.basicProduction = None
		self.buildings = None
		self.basicNames = ["Lumberjack", "Clay", "Iron", "Quarry", "Farmyard"]

	# returns wether or not something is upgrading
	def upgradeNeeded(self, saturate=False):
		middles = self.driver.find_elements_by_class_name("middle")
		numUpgrading = 0
		for sub in middles:
			text = sub.get_attribute("innerHTML")
			if(text.find("Upgrading") != -1 and text.find("None") == -1):
				numUpgrading += 1

		self.navToMap()
		self.findBuildings(overwrite=True)
		self.findResourceProduction(overwrite=True)
		
		print(numUpgrading)
		if(numUpgrading > 2):
			return False
		elif(numUpgrading == 2 and saturate):
			return True
		elif(numUpgrading == 2):
			return False
		else:
			return True

	# one of the main functions: calls othermethods to upgrade the lowest cost building
	# in this case it will upgrade the lowest cost production building
	def upgradeLowest(self):
		self.navToMap()
		self.findBuildings()
		self.findResourceProduction()
		idOfBuilding = self.findLowestofType(self.findLowestProduction())
		self.upgradeBuilding(idOfBuilding)
		self.clickUpgrade()

	def checkProduction(self):
		address = self.driver.execute(webdriver.remote.command.Command.GET_CURRENT_URL)
		if "Production" not in address:
			self.clickProduction()
		
		elements = WebDriverWait(self.driver, self.timeout).until(lambda x: find_selectors(x, '[style="padding:15px;margin:10px"]'))
		
		for x in range(len(elements)):
			element = elements[x]
			element = get_class(element, "odd")
			
			if(element == None):
				# click and produce, at this point it is assumed the bottom will be there
				element = elements[x]
				element = get_selector(element, '[style="vertical-align:-17px;"]')
				if(element != None):
					ActionChains(self.driver).move_to_element(element).move_by_offset(-15,0).click().perform()
			else:
				print("already upgrading")
			
			self.clickProduction()
			elements = get_selectors(self.driver, '[style="padding:15px;margin:10px"]')

	# wow this is coming together much quicker now
	# Clicks the production tab
	def clickProduction(self):
		try:
			element = WebDriverWait(self.driver, self.timeout).until(lambda x: find_class(x, "headLinks"))
			button = element.find_element_by_link_text("Production")
			ActionChains(self.driver).move_to_element(button).click().perform()
		except selenium.common.exceptions.StaleElementReferenceException:
			print("Trying again")
			self.clickProduction()

	# returns index of lowest production 
	def findLowestProduction(self, foodCutOff=None, relativeFood=0.1):
		index = 0
		low = self.basicProduction[0]
		high = self.basicProduction[0]

		for x in range(len(self.basicProduction) - 1):
			if(low > self.basicProduction[x]):
				low = self.basicProduction[x]
				index = x
			if(high < self.basicProduction[x]):
				high = self.basicProduction[x]
		
		if(foodCutOff == None):
			foodCutOff = relativeFood * high

		if(self.basicProduction[4] <= foodCutOff):
			return 4

		return index

	def findLowestofType(self, idOfType):
		low = 21		# max building level is 20
		index = -1		# index of the lowest building
		name = self.basicNames[idOfType]
		for y in range(25):		# always 25 basic production structures
			if(name != self.buildings[y][0]):
				continue
			if(self.buildings[y][1] < low):
				print(name)
				low = self.buildings[y][1]
				index = y

		return index

	# returns if it was successful
	def findBuildings(self, overwrite=False):
		if self.buildings != None and overwrite == False:
			return False

		content = self.driver.find_element_by_id("MainContentDiv")
		# get down to only the plots
		html = content.get_attribute("innerHTML")
		html = html.split("<!-- Land Plot Images -->")
		html = html[1]

		# find where the title, level and lcoation are stored
		match = re.findall('title=".*?"', html)
		ref = re.findall('alt=".*?"', html)
		self.buildings = [["building", -1, -1]] #buildingName, level, location

		for x in range(len(match)):
			strings = match[x].split('"')
			strings = strings[1].split(" ")
			name = (str)(strings[0][0:])
			refString = ref[x].split("e")

			try:
				level = (int)(strings[1][1:-1])
				location = (int)(refString[1][:-1])
			except ValueError:
				try:
					level = (int)(strings[2][1:-1])
					location = (int)(refString[1][:-1])
				except ValueError:
					continue

			self.buildings.append([name, level, location])

		return True

	# returns the production rates of the core 5 resources
	def findResourceProduction(self, overwrite=False):
		if self.basicProduction != None and overwrite == False:
			return False
		content = self.driver.find_element_by_id("tbRes")
		content = content.text
		self.basicProduction = []
		for x in range(5):
			holder = content.split(" ")[8+x][1:]
			holder = holder.split(",")
			if(len(holder) > 1):
				val = 0
				for x in range(len(holder)):
					val = (val * 1000) + (int)(holder[x])
			else:
				val = (int)(holder[0])

			self.basicProduction.append(val)

		return True

	# finds the building to upgrade and gets to the page
	def upgradeBuilding(self, buildingID):
		content = self.driver.find_element_by_id("townMap")
		html = content.get_attribute("innerHTML")
		match = re.findall('<area title.*?>', html)

		for x in match:
			data = x.split('"')
			if(data[3] == "#/Town/Castle?TownOrLand=0&amp;plotid=26"):
				continue

			val = (int)(data[7].split("e")[1])
			if(val == buildingID):
				coords = data[9].split(', ')
				xCoord = ((int)(coords[2]) + (int)(coords[0])) / 2
				yCoord = ((int)(coords[3]) + (int)(coords[1])) / 2
				# these offsets are just from trial and error
				ActionChains(self.driver).move_to_element(content).move_by_offset(-323, -232).move_by_offset(xCoord, yCoord).click().perform()
				break

		self.driver.implicitly_wait(1)
		return True

	def clickUpgrade(self):
		# content = self.driver.find_element_by_css_selector("[id='UpgradePanel']")
		element = WebDriverWait(self.driver, 1.5).until(lambda x: find_selector(x, "[id='UpgradePanel']"))
		try:
			element = element.find_element_by_class_name("short")
			ActionChains(self.driver).move_to_element(element).click().perform()			
			return True
		except selenium.common.exceptions.NoSuchElementException:
			return False


	def navToMap(self):
		# <div class="iconBox ib2">
		outerClass = self.driver.find_element_by_class_name("logo")
		if(outerClass != None):
			#content = outerClass.find_element_by_css_selector('a[href$="Map"]')
			try:
				content = outerClass.find_element_by_css_selector("[class='iconBox ib2'")
			except selenium.common.exceptions.NoSuchElementException:
				content = outerClass.find_element_by_css_selector("[class='iconBox ib2 top'")

			if(content != None):
				content.click()
				time.sleep(self.waitTime)
			else:
				writeBug("Couldnt find class = 'iconBox ib2'")
		else:
			writeBug("Couldnt find class = 'logo'")

	# clicks on the next city button, if false doesnt update this class' city data
	def nextCity(self, getInfo=True):
		element = self.driver.find_element_by_class_name("nTownTD")
		ActionChains(self.driver).move_to_element(element).click().perform()

		time.sleep(self.waitTime)
		if(getInfo == True):
			self.findBuildings(overwrite=True)
			self.findResourceProduction(overwrite=True)

	def logout(self):
		element = self.driver.find_element_by_css_selector("[title='Logout'")
		ActionChains(self.driver).move_to_element(element).click().perform()


#################################################################################################
# end of class 																					#
#################################################################################################

# checks if the driver window is still open
def isDriverAlive(driver):
	try:
		# if the webdriver can execute this then it is still open
		driver.execute(webdriver.remote.command.Command.GET_CURRENT_URL)
		return True
	except (selenium.common.exceptions.WebDriverException):
		return False

# helper for printing html to a file
def printHTML(driver, file="html.txt"):
	f = codecs.open(file, "w+", "utf-8")
	htmlSource = driver.page_source

	#soup = BeautifulSoup(html_source, "html.parser")
	f.write(htmlSource)
	f.close()

# logins into an account with the given name
def login(driver, username, password):
	flag = True
	while(flag):
		try:
			loginInfo = driver.find_element_by_class_name("inputdata")
			html = loginInfo.get_attribute("innerHTML")
			val = re.search('value=".*?"', html)

			if(val.group(0) != ""):
				inputList = loginInfo.find_elements_by_id("txtPlayerName")
				inputList[0].clear()

			if(len(val.groups()) < 1): 
				writeBug('Could not find value=".*?"' + html + "\n\n")
			
			inputList = loginInfo.find_elements_by_id("txtPlayerName")
			inputList[0].send_keys(username)
			inputList = loginInfo.find_elements_by_id("txtPassword")
			inputList[0].send_keys(password)
			inputList[0].send_keys(Keys.RETURN)
			flag = False
		except selenium.common.exceptions.NoSuchElementException:
			# replace with or add print to error
			flag = True

	time.sleep(.75)
	checkForLoginBonus(driver)

#################################################################################################
# lambda/stale things 																			#
#################################################################################################
def find_selector(driver, selector="[class='short claimBonus'"):
	element = driver.find_element_by_css_selector(selector)
	if element:
		return element
	else:
		return False

def find_selectors(driver, selector="[class='short claimBonus'"):
	element = driver.find_elements_by_css_selector(selector)
	if element:
		return element
	else:
		return False

def find_class(driver, name):
	element = driver.find_element_by_class_name(name)
	if element:
		return element
	else:
		return False

#################################################################################################
# start of gets. These functions might replace the above as they solve the issue in a different
# way than the webdriver wait functions
# it will still probably be useful to use the waits whenever the driver gets changed just so there 
# is a buffer time for the page to load. Or just a wait in general
# Also gets are the same as finds but these will handle the excepts and may replace most other calls
# didnt know you could have multiple excepts and this lets me do that in one call and an if else statement
# doesnt save a massive amount of room but it might be tidier, they will return either an element or none 
# when the page doesnt contain the element

def get_selector(driver, text, recurse=0):
	print(text)
	try:
		element = driver.find_element_by_css_selector(text)
		return element
	except selenium.common.exceptions.StaleElementReferenceException:
		time.sleep(.2)
		if(recurse < 10):
			return get_selector(driver, text, recurse=recurse+1)
		else:
			print("still stale")
			return None
	except selenium.common.exceptions.NoSuchElementException:
		return None

def get_selectors(driver, text, recurse=0):
	print(text)
	try:
		element = driver.find_elements_by_css_selector(text)
		return element
	except selenium.common.exceptions.StaleElementReferenceException:
		time.sleep(.2)
		if(recurse < 10):
			return get_selectors(driver, text, recurse=recurse+1)
		else:
			print("still stale")
			return None
	except selenium.common.exceptions.NoSuchElementException:
		return None

def get_class(driver, text, recurse=0):
	try:
		element = driver.find_element_by_class_name(text)
		return element
	except selenium.common.exceptions.StaleElementReferenceException:
		time.sleep(.2)
		if(recurse < 10):
			return get_class(driver, text, recurse=recurse+1)
		else:
			print("still stale")
			return None
	except selenium.common.exceptions.NoSuchElementException:
		return None

#################################################################################################
# end of said things																			#
#################################################################################################

def checkForLoginBonus(driver):
	element = driver.find_element_by_class_name("heraldBonus")
	print(element.text)

	if(element.text == "Claim your FREE daily bonus here!"):
		# click through the bonus menu
		ActionChains(driver).move_to_element(element).click().perform()
		print("Success")
		try:
			element = WebDriverWait(driver, 1.5).until(lambda x: find_selector(x, "[class='short claimBonus'"))
			print("Text", element.get_attribute("outerHTML"))
			ActionChains(driver).move_to_element(element).click().perform()
			print("Could find")
		except selenium.common.exceptions.NoSuchElementException:
			print("Could not find")	

		element = get_class(driver, "ui-button-text")
		if(element != None):
			ActionChains(driver).move_to_element(element).click().perform()

# main loop for the bot
def loop(driver, usernames, passwords):
	# main loop for execution
	# finds if something needs to be upgraded, researched, produced, if so do a corresponding action
	myCity = City(driver)
	i = 0
	j = 0
	while(isDriverAlive(driver)):
		upgradeNeeded = myCity.upgradeNeeded()
		if(upgradeNeeded == True):
			myCity.upgradeLowest();	# for testing
		if(upgradeNeeded == False):
			myCity.nextCity()

		time.sleep(.75)
		if(i == 5):
			i = 0
			j = (j+1) % len(usernames)
			myCity.logout()
			login(driver, usernames[j], passwords[j])
		else:
			i += 1
	print("Closing process")

def main():
	driver = openAPage()
	usernames = ["Fuasbi", "Zeratul"]
	passwords = ["Fuasbi123", "Fuasbi123"]
	login(driver, usernames[1], passwords[1])
	time.sleep(1)
	loop(driver, usernames, passwords)

if __name__ == '__main__':
	main()
