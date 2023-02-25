import psycopg2
from db_configs import Configs


DBNAME = Configs.DBNAME
USER = Configs.USER
PASSWORD = Configs.PASSWORD
HOST = Configs.HOST


def create_flats_table():
    with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST) as conn:
        with conn.cursor() as cur:
            cur.execute('''
            CREATE TABLE IF NOT EXISTS flats(
                id serial PRIMARY KEY,
                link CHARACTER VARYING(300) UNIQUE NOT NULL,
                reference CHARACTER VARYING(30),
                price BIGINT,
                title CHARACTER VARYING(1000),
                description CHARACTER VARYING(10000),
                date TIMESTAMP WITH TIME ZONE,
                image_links CHARACTER VARYING(10000),
                rooms BIGINT,
                area REAL,
                city CHARACTER VARYING(100),
                address CHARACTER VARYING(1000),
                seller_phone CHARACTER VARYING(20)
                )''')


def insert_flat(flat):
    with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST) as conn:
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO flats (link, reference, price, title, description, date, image_links, 
                rooms, area, city, address, seller_phone) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
                ON CONFLICT (link) DO UPDATE 
                SET 
                link = EXCLUDED.link, 
                reference = EXCLUDED.reference,
                price = EXCLUDED.price, 
                title = EXCLUDED.title, 
                description = EXCLUDED.description, 
                date = EXCLUDED.date,
                image_links = EXCLUDED.image_links,
                rooms = EXCLUDED.rooms,
                area = EXCLUDED.area,
                city = EXCLUDED.city,
                address = EXCLUDED.address,
                seller_phone = EXCLUDED.seller_phone
                 ''', (flat.link, flat.reference, flat.price, flat.title, flat.description,
                       flat.date, flat.image_links, flat.rooms, flat.area, flat.city, flat.address, flat.seller_phone)
                        )
