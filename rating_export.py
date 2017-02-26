#Aleksandr Iskhakov, 2017. Code and its parts are free to use for non-commercial purposes
#requires python 3 with following packages: beautifulsoup4, imdbpie, transliterate, selenium and also geckodriver
import sys
from bs4 import BeautifulSoup
from imdbpie import Imdb
from transliterate import translit, get_available_language_codes
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

try:
	html = open(sys.argv[1]).read()
	soup = BeautifulSoup(html, 'html.parser')

	profile = webdriver.FirefoxProfile(sys.argv[2])
	browser = webdriver.Firefox(profile)
	browser.set_page_load_timeout(10)
except FileNotFoundError as ex:
	print('Error in arguments: ' + ex.filename + ' - ' + ex.strerror)
	sys.exit()

imdb = Imdb()

table = soup.find('table')
rows = table.findAll('tr')
for row in rows[1:]:
	cols = row.findAll('td')
	title = cols[1].string
	title_rus = cols[0].string
	year = cols[2].string
	rating = cols[7].string
	
	if rating == '-':
		print('Film has no rating, skipped')
		with open('skipped_films.txt', 'a') as skipped_films:
			skipped_films.write(title + '|' + title_rus + '|' + year + '|' + rating + '\n')
		continue
	
	if not title:
		title = translit(title_rus, 'ru', reversed=True)
	
	search_res = imdb.search_for_title(title)
	
	print('\n==========================================================')
	print(str(title) + '\n' + str(title_rus) + '\nYear: ' + str(year) + '\nRating: ' + str(rating))
	
	for founded_film in search_res:
		print('\nFounded: ' + str(founded_film['title']) + ' (' + str(founded_film['year']) + ')')
		if year == founded_film['year']:
			if title != founded_film['title']:
				print('Year matches, but the title is different')
				with open('titles_didn\'t_match.txt', 'a') as titles_didnt_match:
					titles_didnt_match.write(title + '|' + title_rus + '|' + year + '|' + rating + '\n'
						+ founded_film['title'] + ': http://www.imdb.com/title/' + founded_film['imdb_id'] + '\n\n')
			
			try:
				browser.get('http://www.imdb.com/title/' + founded_film['imdb_id'])
			except TimeoutException:
				#seems like it's the only way to restrict 'get' by timer
				pass
			
			browser.find_element_by_xpath('//*[@data-reactid=".2.0"]').click()
			browser.find_element_by_xpath('//*[@data-reactid=".2.1.0.1.$' + rating + '"]').click()
			
			print('Rated')
			break
		else:
			print('Year does not match')
	else:
		print('\nFilm not found in the search results, skipped')
		with open('skipped_films.txt', 'a') as skipped_films:
			skipped_films.write(title + '|' + title_rus + '|' + year + '|' + rating + '\n')

browser.quit()
print('Export finished')