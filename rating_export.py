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
from selenium.common.exceptions import WebDriverException

def to_string(*args):
	return ''.join(map(str, args))

def append_to_file(filename, message):
	with open(filename, 'ab') as file:
		file.write(to_string(message, '\n').encode('utf8'))

def log(message):
	print(message)
	append_to_file('log.txt', message)

def get_table_from_export_file(path_to_export_file):
	html = open(path_to_export_file).read()
	soup = BeautifulSoup(html, 'html.parser')
	return soup.find('table')

def init_browser_with_profile(path_to_profile):
	#cross-browser implementation sure'd be nice
	profile = webdriver.FirefoxProfile(path_to_profile)
	browser = webdriver.Firefox(profile)
	browser.set_page_load_timeout(10)
	return browser

def main():
	log(to_string('{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{{\n',
		'Export started: ', datetime.now()))

	try:
		films_table = get_table_from_export_file(sys.argv[1])
		browser = init_browser_with_profile(sys.argv[2])
	except FileNotFoundError as ex:
		log(to_string('Error on initialization: ', ex.filename, ' - ', ex.strerror))
		sys.exit()

	imdb = Imdb()

	mismatches_file = 'not_exact_match.txt'
	skipped_films_file = 'skipped_films.txt'

	rows = films_table.findAll('tr')
	try:
		for row in rows[1:]:
			cols = row.findAll('td')
			title = cols[1].string
			title_rus = cols[0].string
			year = (cols[2].string)[0:4]
			rating = cols[7].string
			
			if rating == '-':
				log('Film has no rating, skipped')
				append_to_file(skipped_films_file, to_string(title, '|', title_rus, '|', year, '|', rating, '\n'))
				continue
			
			if not title:
				title = translit(title_rus, 'ru', reversed=True)
			
			search_res = imdb.search_for_title(title)
			
			log(to_string('\n==========================================================\n',
				title, '\n', title_rus, '\nYear: ', year, '\nRating: ', rating))
			
			for found_film in search_res:
				log(to_string('\nFound: ', found_film['title'], ' (', found_film['year'], ')'))
				
				if found_film['year'] is None:
					found_film['year'] = '0'
				
				year_diff = abs(int(year) - int(found_film['year']))
				if year_diff <= 1:
					if title != found_film['title'] or year_diff != 0:
						log('Title is different or year doesn\'t exactly match')
						append_to_file(mismatches_file, to_string(title, '|', title_rus, '|', year, '|', rating, '\n',
							found_film['title'], ' (', str(found_film['year']), ') : ',
							'http://www.imdb.com/title/', found_film['imdb_id'], '\n\n'))
					
					try:
						browser.get('http://www.imdb.com/title/' + found_film['imdb_id'])
					except TimeoutException:
						#seems like it's the only way to restrict 'get' by timer
						pass
					
					browser.find_element_by_xpath('//*[@data-reactid=".2.0"]').click()
					browser.find_element_by_xpath(to_string('//*[@data-reactid=".2.1.0.1.$', rating, '"]')).click()
					log('Rated')
					break
				else:
					log('Year does not match at all')
			else:
				log('\nFilm not found in the search results, skipped')
				append_to_file(skipped_films_file, to_string(title, '|', title_rus, '|', year, '|', rating, '\n'))
		
		browser.quit()
	except WebDriverException as ex:
		log('Web driver error: ' + ex.msg)
	
	log(to_string('Export finished: ', datetime.now(),
		'\n}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}'))

if __name__ == "__main__":
	main()