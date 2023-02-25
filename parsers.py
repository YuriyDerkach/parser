import requests
from bs4 import BeautifulSoup
from data import Flat
import re
from datetime import datetime
import db_client
import asyncio
import aiohttp
from tqdm import tqdm


class Parser:
    def __init__(self):
        self.flats = []
        self.links = []
        self.parser_name = None
        self.parser_link = None
        self.a_class = None
        self.a_filter = None
        self.start_page = 0
        self.finish_page = 5

    async def get_all_last_flats_links(self, session, page):
        flat_links = []
        async with session.get(f'{self.parser_link}{page}') as resp:
            html = BeautifulSoup(await resp.text(), 'html.parser')
            for a in html.find_all('a', href=True, class_=self.a_class):
                flat_links.append(a['href'])
            # if self.start_page == 0:
            #     print(f'Обработана {page + 1} страница')
            # else:
            #     print(f'Обработана {page} страница')
        self.links.extend(list(filter(lambda el: self.a_filter in el, flat_links)))

    async def enrich_links_to_flats(self, session, link):
        pass

    async def save_flats(self, flat):
        db_client.insert_flat(flat)
        # print(f'Загружено в базу {flat.title}')

    async def get_last_flats(self):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for page in range(self.start_page, self.finish_page):
                task = asyncio.create_task(self.get_all_last_flats_links(session, page))
                tasks.append(task)
            await asyncio.gather(*[f for f in tqdm(asyncio.as_completed(tasks), total=len(tasks),
                                                   desc='Обработано страниц...')])
        async with aiohttp.ClientSession() as session:
            tasks = []
            for link in tqdm(self.links, desc='Спаршено ссылок...'):
                task = asyncio.create_task(self.enrich_links_to_flats(session, link))
                tasks.append(task)
            await asyncio.gather(*tasks)
        db_client.create_flats_table()
        for flat in tqdm(self.flats, desc='Сохранено в базу...'):
            task = asyncio.create_task(self.save_flats(flat))
            tasks.append(task)
        await asyncio.gather(*tasks)


class RealtParser(Parser):
    def __init__(self):
        super().__init__()
        self.parser_name = 'realt'
        self.parser_link = 'https://realt.by/sale/flats/' \
                           '?search=eJyLL04tKS1QNXUqzi8qiU%2BqVDV1AXIMgJRtSmJJanxRallmc' \
                           'WZ%2Bnlo8TGFRanJ8QWpRfEFieipImakBAC0FF04%3D&page='
        self.a_class = 'teaser-title'
        self.a_filter = 'object'

    async def enrich_links_to_flats(self, session, link):
        async with session.get(link) as resp:
            if resp.status == 200:
                html = BeautifulSoup(await resp.text(), 'html.parser')
                title = html.find('h1', class_='order-1')
                if title is not None:
                    title = title.text.strip()
                else:
                    title = '-'
                raw_price = html.find('h2', class_='w-full')
                if raw_price is not None:
                    price = int(re.sub('[^0-9]', '', raw_price.text.strip()))
                else:
                    price = 0
                descriptions = html.find_all('section', class_='bg-white flex flex-wrap md:p-6 my-4 rounded-md')
                description = '-'
                if descriptions is not None:
                    for descr in descriptions:
                        if descr.text.startswith('Описание'):
                            description = descr.text.replace('Описание', '').strip()
                try:
                    date = datetime.strptime(html.find('span', class_='mr-1.5').text.strip(), '%d.%m.%Y')
                except Exception as e:
                    date = datetime.today()
                image_links = []
                for img in html.find_all('img', alt='Изображение слайдера'):
                    if img['src'].startswith('https://static.realt.by/thumb/c/160x160/'):
                        image_links.append(img['src'])
                stats = html.find_all('li', class_='relative py-1')
                address = ''
                for stat in stats:
                    if stat.text.startswith('Количество комнат'):
                        rooms = int(re.sub('[^0-9]', '', stat.text.strip()))
                    elif stat.text.startswith('Площадь общая'):
                        area = float(re.sub('[^0-9,.]', '', stat.text.replace('м2', '').strip()))
                    elif stat.text.startswith('Населенный пункт'):
                        city = stat.text.replace('Населенный пункт', '').strip()
                    elif stat.text.startswith('Улица'):
                        address += stat.text.replace('Улица', '').strip()
                    elif stat.text.startswith('Номер дома'):
                        address += ', ' + stat.text.replace('Номер дома', '').strip()
                seller_phone = '-'
                # for a in html.find_all('a', href=True, class_='focus:outline-none'):
                #     if a['href'].startswith('tel:+'):
                #         seller_phone = a['href'].replace('tel:', '').strip()
                #         if seller_phone == '+375293064455':
                #             continue
                #         print(seller_phone)
                #         break
                self.flats.append(Flat(
                    link=link,
                    title=title,
                    price=price,
                    description=description,
                    date=date,
                    reference=self.parser_name,
                    image_links=image_links,
                    rooms=rooms,
                    area=area,
                    city=city,
                    address=address,
                    seller_phone=seller_phone
                ))
                # print(f'Спаршен {link}')
            else:
                # print(f'Не удалось спарсить {link} ({resp.status})')
                await self.enrich_links_to_flats(session, link)


class DomovitaParser(Parser):
    def __init__(self):
        super().__init__()
        self.parser_name = 'domovita'
        self.parser_link = 'https://domovita.by/minsk/flats-new-offers/sale?page='
        self.a_class = 'mb-5'
        self.a_filter = 'flats'
        self.start_page = 1
        self.finish_page = 6

    async def enrich_links_to_flats(self, session, link):
        async with session.get(link) as resp:
            if resp.status == 200:
                html = BeautifulSoup(await resp.text(), 'html.parser')
                title = html.find('div', class_='object-head__name').text.strip()
                raw_price = html.find('div', class_='dropdown-pricechange_price-block')
                if raw_price is not None:
                    if len(raw_price.text) > 10:
                        raw_price = raw_price.text[:raw_price.text.find('р')]
                        price = int(re.sub('[^0-9]', '', raw_price.strip()))
                    else:
                        price = int(re.sub('[^0-9]', '', raw_price.text.strip()))
                else:
                    price = 0
                description = html.find('div', class_='white-space--pre-l')
                if description is not None:
                    description = description.text.strip()
                else:
                    description = '-'
                try:
                    date = datetime.strptime(html.find('span', class_='publication-info__publication-date').
                                             text.replace('Опубликовано:', '').strip(), '%d.%m.%Y')
                except Exception as e:
                    date = datetime.today()
                image_links = []
                for img in html.find_all('img', alt=title):
                    if img['src'].startswith('https://s.domovita.by/images/'):
                        image_links.append(img['src'])
                stats = html.find_all('div', class_='object-info__parametr')
                address = ''
                rooms = 0
                area = 0
                for stat in stats:
                    if 'Комнат' in stat.text and 'раздельных' not in stat.text:
                        rooms = int(re.sub('[^0-9]', '', stat.text.strip()))
                    elif 'Общая площадь' in stat.text:
                        area = float(re.sub('[^0-9,.]', '', stat.text.strip()))
                    elif 'Адрес' in stat.text:
                        address = stat.text.replace('Адрес', '').strip()
                city = html.find('span', id='city').text.strip()
                seller_phone = '-'
                self.flats.append(Flat(
                    link=link,
                    title=title,
                    price=price,
                    description=description,
                    date=date,
                    reference=self.parser_name,
                    image_links=image_links,
                    rooms=rooms,
                    area=area,
                    city=city,
                    address=address,
                    seller_phone=seller_phone
                ))
                # print(f'Спаршен {link}')
            else:
                # print(f'Не удалось спарсить {link} ({resp.status})')
                await self.enrich_links_to_flats(session, link)
