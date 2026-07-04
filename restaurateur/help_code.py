from locations.models import Location


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


def get_all_locations():
    locations = {}
    for address, lon, lat in Location.objects.values_list('address', 'lon', 'lat'):
        locations.update({address: (lat, lon)})
    return locations
