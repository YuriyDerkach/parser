class Flat:
    def __init__(self, link, reference=None, price=None, title=None, description=None,
                 date=None, image_links=None, rooms=None, area=None, city=None, address=None, seller_phone=None):
        self.link = link
        self.reference = reference
        self.price = price
        self.title = title
        self.description = description
        self.date = date
        self.image_links = image_links
        self.rooms = rooms
        self.area = area
        self.city = city
        self.address = address
        self.seller_phone = seller_phone
