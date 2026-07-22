from locations.models import Location
from locations.help_code_location import adds_address


def get_restaurant_available_products(restaurants):
    for restaurant in restaurants:
        restaurant.available_products = [menu_item.product for menu_item in restaurant.menu_items.all()]
    return restaurants


def get_order_available_products(orders, restaurants):
    for order in orders:
        order.available_products = [order_product.product for order_product in order.elements.all()]
    return get_order_available_restaurants(orders, restaurants)


def get_order_available_restaurants(orders, restaurants):
    for order in orders:
        available_restaurants = []
        for restaurant in restaurants:
            if set(order.available_products).issubset(set(restaurant.available_products)):
                available_restaurants.append(restaurant)
            order.available_restaurants = available_restaurants
    return orders


def get_locations(orders, restaurants):
    addresses = []
    for order in orders:
        addresses.append(order.address)
        for restaurant in restaurants:
            addresses.append(restaurant.address)

    locations = {address: (lat, lon) for address, lat, lon in Location.objects.filter(address__in=addresses).values_list('address', 'lat', 'lon')}

    for address in locations:
        if address not in addresses:
            adds_address(address)

    return locations
