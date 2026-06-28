import requests
import re
from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Prefetch
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from geopy import distance
from django.conf import settings
from foodcartapp.models import (
    Product,
    Restaurant,
    Order,
    RestaurantMenuItem
)


def fetch_coordinates(address):
    try:
        base_url = "https://geocode-maps.yandex.ru/1.x"
        response = requests.get(base_url, params={
            "geocode": address,
            "apikey": settings.YANDEX_API,
            "format": "json",
        })
        response.raise_for_status()
        found_places = response.json()['response']['GeoObjectCollection']['featureMember']

        if not found_places:
            return None

        most_relevant = found_places[0]
        lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    except requests.exceptions.HTTPError:
        return None

    return lat, lon


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


@user_passes_test(is_manager, login_url='restaurateur:login')



def view_orders(request):
    orders = Order.objects.all().price().order_status()
    restaurants = Restaurant.objects.prefetch_related(
        Prefetch(
            'menu_items',
            queryset=RestaurantMenuItem.objects.filter(
                availability=True
            ).select_related('product')
        )
    )
    for restaurant in restaurants:
        available_products = []
        for menu_item in restaurant.menu_items.all():
            available_products.append(menu_item.product)
        restaurant.available_products = available_products

    for order in orders:
        available_products = []
        for order_element in order.elements.all():
            available_products.append(order_element.product)
        order.available_products = available_products

    for order in orders:
        available_restaurants = []
        for restaurant in restaurants:
            if set(order.available_products).issubset(set(restaurant.available_products)):
                available_restaurants.append(restaurant)
            order.available_restaurants = available_restaurants 

    for order in orders:
        manager_restaurant = [] 
        for restaurant in order.available_restaurants:            
            order.manager_restaurant = manager_restaurant
            order_coordinates = fetch_coordinates(order.address)
            restaurant_cooredinates = fetch_coordinates(restaurant.address)
            distance_to_restaurant = "{:.3f}".format(distance.distance(
                restaurant_cooredinates,
                order_coordinates
            ).km)

            manager_restaurant.append(f'{restaurant.name}: {distance_to_restaurant} км')
            manager_restaurant = sorted(
                manager_restaurant,
                key=lambda x: int(re.search(r'\d+', x).group())
            )
            order.manager_restaurant = manager_restaurant


    return render(
        request,
        template_name='order_items.html',
        context={
            'orders': orders
        })

