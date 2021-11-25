import enum
import random
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class PageState(enum.Enum):
	Login = 0
	CityType = 1
	TownMap = 2
	Castle = 3
	Resources = 4
	Production = 5
	Sovereignty = 6
	Inventory = 7
	Growth = 8

class Buildings(enum.Enum):
	Lumberjack = "Lumberjack"
	Paddock = "Paddock"

class XPath(enum.Enum):
	MainPageLoginButton = "/html/body/div[1]/div[1]/nav/div[2]/a/img"
	LoginPageLoginButton = "//*[@id=\"btnLogin\"]"
	LoginPlayerName = "//*[@id=\"txtPlayerName\"]"
	LoginPassword = "//*[@id=\"txtPassword\"]"

	PageCity = "/html/body/div[1]/div[2]/table/tbody/tr[1]/td[1]/div/div/div/div[1]/a[1]"
	PageTownMap = "/html/body/div[1]/div[2]/table/tbody/tr[1]/td[1]/div/div/div/div[1]/a[2]"
	PageCastle = "/html/body/div[1]/div[2]/table/tbody/tr[1]/td[1]/div/div/div/div[1]/a[3]"
	PageResources = "/html/body/div[1]/div[2]/table/tbody/tr[1]/td[1]/div/div/div/div[1]/a[4]"
	PageProduction = "/html/body/div[1]/div[2]/table/tbody/tr[1]/td[1]/div/div/div/div[1]/a[5]"
	PageSovereignty = "/html/body/div[1]/div[2]/table/tbody/tr[1]/td[1]/div/div/div/div[1]/a[6]"
	PageInventory = "/html/body/div[1]/div[2]/table/tbody/tr[1]/td[1]/div/div/div/div[1]/a[7]"
	PageGrowth = "/html/body/div[1]/div[2]/table/tbody/tr[1]/td[1]/div/div/div/div[1]/a[8]"

	OuterTownMap = "//*[@id=\"townMapOutline\"]"
def buildingXpath(buildingNumber : int):
	return "/html/body/div[1]/div[2]/table/tbody/tr[1]/td[1]/div/div/div/div[2]/div/map/area[{}]".format(buildingNumber)

pageStatePathMap = {
	PageState.CityType : XPath.PageCity.value,
	PageState.TownMap : XPath.PageTownMap.value,
	PageState.Castle : XPath.PageCastle.value,
	PageState.Resources : XPath.PageResources.value,
	PageState.Production : XPath.PageProduction.value,
	PageState.Sovereignty : XPath.PageSovereignty.value,
	PageState.Inventory : XPath.PageInventory.value,
	PageState.Growth :  XPath.PageGrowth.value
}

def slowType(element, text, delay):
	for character in text:
		element.send_keys(character)
		time.sleep(delay)

def slowTypeRandDelay(element, text, mu, sigma):
	for character in text:
		element.send_keys(character)
		time.sleep(random.gauss(mu, sigma))

class IllyriadEngine:
	NumberOfBuildings = 51
	def __init__(self, username, password):
		self.username = username
		self.password = password

		self.pageState = PageState.Login
		self.cityState = "New Settlement"
		self.loginState = False


		self.browser = webdriver.Firefox()
		self.browser.implicitly_wait(1);

	def __del__(self):
		self.browser.quit()

	def login(self):
		# navigate to page
		self.browser.get("https://www.illyriad.co.uk/")

		# click mainpage login button to get to actual login page
		element = self.browser.find_element(By.XPATH, XPath.MainPageLoginButton.value)
		WebDriverWait(self.browser, 15).until(EC.element_to_be_clickable(element))
		element.click()

		# type username
		element = self.browser.find_element(By.XPATH, XPath.LoginPlayerName.value)
		WebDriverWait(self.browser, 15).until(EC.element_to_be_clickable(element))
		slowTypeRandDelay(element, self.username, 0.1, 0.03)

		# type password
		element = self.browser.find_element(By.XPATH, XPath.LoginPassword.value)
		slowTypeRandDelay(element, self.password, 0.1, 0.03)

		# click login button
		time.sleep(1)
		self.browser.find_element(By.XPATH, XPath.LoginPageLoginButton.value).click()

		# set current state
		self.loginState = True
		self.pageState = PageState.TownMap

	def navigate(self, requestedState : PageState):
		if not self.loginState:
			return
		if requestedState is self.pageState:
			return

		elementString = pageStatePathMap[requestedState]
		if not elementString:
			return

		element = self.browser.find_element(By.XPATH, elementString).click()
		self.pageState = requestedState

	def __getNumBuildings(self):
		if(self.pageState == PageState.TownMap):
			elements = self.browser.find_element(By.XPATH, XPath.OuterTownMap.value)
			return len(elements)
		else:
			return 0

	def findBuildings(self, buildingToFind : Buildings):
		returnElements = []
		if not self.loginState or self.pageState is not PageState.TownMap:
			return returnElements

		# get outer element containing all buildings and iterate through finding all buildings with the correct title
		buildingElements = self.browser.find_element(By.XPATH, XPath.OuterTownMap.value)
		for building in buildingElements.find_elements(By.TAG_NAME, "area"):
			buildingText = building.get_attribute('title').split(" ")
			if(buildingText[0] == buildingToFind.value):
				returnElements.append(building)

		return returnElements


	def upgradeBuilding(self, building : Buildings):
		if not self.loginState:
			return

		self.navigate(PageState.TownMap)
		buildingElements = self.findBuildings(building)
		if(len(buildingElements) > 0):
			buildingElements[0].click()



	def getBrowser(self):
		return self.browser



if __name__ == "__main__":
	engine = IllyriadEngine("fuasbi", "fuasbi123")
	engine.login()
	engine.navigate(PageState.Castle)
	engine.upgradeBuilding(Buildings.Paddock)


