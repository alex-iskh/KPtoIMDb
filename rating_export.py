#Copyright (c) 2017 Aleksandr Iskhakov
#Published under the terms of the Do What The Fuck You Want To Public License, Version 2. See the LICENSE file for more details.
import sys
from datetime import datetime
from bs4 import BeautifulSoup
from imdbpie import Imdb
from transliterate import translit, get_available_language_codes
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

def append_to_file(filename, message):
	with open(filename, 'ab') as file:
		file.write((message + '\n').encode('utf8'))

def log(message):
	print(message)
	append_to_file('log.txt', message)

log('Export started: ' + str(datetime.now()))

try:
	html = open(sys.argv[1]).read()
	soup = BeautifulSoup(html, 'html.parser')

	profile = webdriver.FirefoxProfile(sys.argv[2])
	browser = webdriver.Firefox(profile)
	browser.set_page_load_timeout(10)
except FileNotFoundError as ex:
	log('Error in arguments: ' + ex.filename + ' - ' + ex.strerror)
	sys.exit()

imdb = Imdb()

mismatches_file = 'not_exact_match.txt'
skipped_films_file = 'skipped_films.txt'

table = soup.find('table')
rows = table.findAll('tr')
for row in rows[1:]:
	cols = row.findAll('td')
	title = cols[1].string
	title_rus = cols[0].string
	year = (cols[2].string)[0:4]
	rating = cols[7].string
	
	if rating == '-':
		log('Film has no rating, skipped')
		append_to_file(skipped_films_file, title + '|' + title_rus + '|' + year + '|' + rating + '\n')
		continue
	
	if not title:
		title = translit(title_rus, 'ru', reversed=True)
	
	search_res = imdb.search_for_title(title)
	
	log('\n==========================================================')
	log(str(title) + '\n' + str(title_rus) + '\nYear: ' + str(year) + '\nRating: ' + str(rating))
	
	for found_film in search_res:
		log('\nFound: ' + str(found_film['title']) + ' (' + str(found_film['year']) + ')')
		year_diff = abs(int(year) - int(found_film['year']))
		if year_diff <= 1:
			if title != found_film['title'] or year_diff != 0:
				log('Title is different or year doesn\'t exactly match')
				append_to_file(mismatches_file, title + '|' + title_rus + '|' + year + '|' + rating + '\n'
					+ found_film['title'] + ' (' + str(found_film['year']) + ') : '
					+ 'http://www.imdb.com/title/' + found_film['imdb_id'] + '\n\n')
			
			try:
				browser.get('http://www.imdb.com/title/' + found_film['imdb_id'])
			except TimeoutException:
				#seems like it's the only way to restrict 'get' by timer
				pass
			
			browser.find_element_by_xpath('//*[@data-reactid=".2.0"]').click()
			browser.find_element_by_xpath('//*[@data-reactid=".2.1.0.1.$' + rating + '"]').click()
			log('Rated')
			break
		else:
			log('Year does not match at all')
	else:
		log('\nFilm not found in the search results, skipped')
		append_to_file(skipped_films_file, title + '|' + title_rus + '|' + year + '|' + rating + '\n')

browser.quit()
log('Export finished: ' + str(datetime.now()))