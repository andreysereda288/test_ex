from bs4 import BeautifulSoup
import csv
import re
import requests

URL = 'https://www.italska8.cz/byty'
HEADERS = {
    'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
                  AppleWebKit/537.36 (KHTML, like Gecko) \
                  Chrome/85.0.4183.121 Safari/537.36",
    'accept': "text/html,application/xhtml+xml,application/xml;\
               q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,\
               application/signed-exchange;v=b3;q=0.9"}

# Get list of ads.
def get_ads(url=URL, headers=HEADERS):
    site = requests.get(url, headers=headers)
    soup = BeautifulSoup(site.text, 'lxml')
    items = soup.find_all('tr', class_='clickable-row')
    apartments = []
    for item in items:
        floor_plan = item.find('td').find_next('td').text
        if floor_plan:
            if floor_plan == 'přízemí+galerie':
                floor_plan = 'ground floor + gallery'
        else:
            floor_plan = 'Unknown'

        floor = item.find('td').find_next('td').find_next('td').text
        floor = floor.replace('.', '') # Transform czech floor to standard.
        if floor[-2] + floor[-1] == 'PP': # 'PP' is under ground.
            floor = '-' + floor
        floor = floor[0:len(floor) - 2]

        area = item.find('td').find_next('td').find_next('td').find_next(
               'td').find_next('td').text
        area = area.replace('m2', '').strip() # Cut only digits from string.

        status = item.find('td').find_next('td').find_next('td').find_next(
                 'td').find_next('td').find_next('td').text
        if status == 'rezervováno':
            status = 'reserved'
        elif status == 'volný':
            status = 'available'
        elif status == 'připravujeme':
            status = 'sold'

        price = item.find('td').find_next('td').find_next('td').find_next(
                'td').find_next('td').find_next('td').find_next('td').text
        if price:
            price = int(price.replace(' ', '')) # Remove spaces between digits.
        else:
            price = 'Not available'

        type = item.find('td').find_next('td').find_next('td').find_next(
               'td').text
        if type == 'nebytový prostor':
            type = 'commercial space'
        elif type == 'byt':
            type = 'apartment'
        elif type == 'ateliér':
            type = 'atelier'

        link = item.get('data-href')

        # Get terace if exists from item's link.
        site_terace = requests.get(link, headers=headers)
        soup_terace = BeautifulSoup(site_terace.text, 'lxml')
        desc = soup_terace.find('div', class_='col col-1-12 grid-5-12').find(
               'strong').text
        desc_list = desc.split("\n")
        terace = '-' # Native value if terace is not exists.
        for line in desc_list:
            if re.search(r'Terasa', line):
                terace = line.strip().replace('\xa0', ' ').split(' ')[1] # Get square of terace from line.

        apartments.append({'id': item.find('td').text, 'floor_plan': floor_plan,
                           'floor': floor, 'area': area, 'status': status,
                           'price': price, 'type': type, 'terace': terace,
                           'link': link})
        print(f'Parsing {link}')
    return apartments

# Save data in csv-file.
def save_csv(apartments):
    with open('apartments.csv', 'w', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['ID', 'Планировка', 'Этаж', 'Площадь', 'Доступность',
                         'Цена', 'Тип', 'Терраса', 'Ссылка'])
        for app in apartments:
            writer.writerow([app['id'], app['floor_plan'], app['floor'],
                             app['area'], app['status'], app['price'],
                             app['type'], app['terace'], app['link']])

# If this script is a main program.
if __name__ == '__main__':
    ads_list = get_ads()
    save_csv(ads_list)
