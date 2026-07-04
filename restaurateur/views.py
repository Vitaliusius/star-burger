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
from foodcartapp.models import (
    Product,
    Restaurant,
    Order,
    RestaurantMenuItem,
    OrderElements
)
from locations.help_code_location import adds_address
from restaurateur.help_code import (
    get_restaurant_available_products,
    get_order_available_products,
    get_all_locations
)


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
    orders = Order.objects.select_related('restaurant').prefetch_related(
        Prefetch(
            'elements',
            queryset=OrderElements.objects.select_related('product')
        )
    ).price().order_status()

    restaurants = Restaurant.objects.prefetch_related(
        Prefetch(
            'menu_items',
            queryset=RestaurantMenuItem.objects.filter(
                availability=True
            ).select_related('product')
        )
    )

    restaurants = get_restaurant_available_products(restaurants)
    orders = get_order_available_products(orders, restaurants)
    locations = get_all_locations()

    for order in orders:
        manager_restaurant = []
        for restaurant in order.available_restaurants:
            distance_to_restaurant = "{:.3f}".format(distance.distance(
                locations.get(order.address),
                locations.get(restaurant.address),
            ).km)
            manager_restaurant.append(f'{restaurant.name}: {distance_to_restaurant} км')
            manager_restaurant = sorted(
                manager_restaurant,
                key=lambda x: int(re.search(r'\d+', x).group())
            )
            order.manager_restaurant = manager_restaurant
        if not adds_address(order.address):
            order.address = 'Такого адреса нет'

    return render(
        request,
        template_name='order_items.html',
        context={
            'orders': orders
        })
