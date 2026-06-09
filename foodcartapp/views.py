import json

from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Product, Order, OrderElements
from rest_framework import status
from rest_framework.serializers import ValidationError
from rest_framework.serializers import Serializer
from rest_framework.serializers import CharField


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


class ApplicationSerializer(Serializer):
    firstname = CharField()
    lastname = CharField()
    phonenumber = CharField(max_length=12)
    address = CharField()


@api_view(['GET', 'POST'])
def register_order(request):
    order = json.dumps(request.data, ensure_ascii=False)
    order = json.loads(order)
    serializer = ApplicationSerializer(data=order)
    serializer.is_valid(raise_exception=True)
    if not isinstance(order['products'], list):
        return Response(['Ожидался list со значениями, но был получен "str"'], status=200)      
    new_order = Order.objects.get_or_create(
    firstname=order['firstname'],
    lastname=order['lastname'],
    phonenumber=order['phonenumber'],
    address=order['address'],
    )

    for product in order['products']:
        OrderElements.objects.get_or_create(
            order_id=new_order[0].id,
            products_id=product['product'],
            quantity=product['quantity'],
        )

    return Response(serializer.is_valid(raise_exception=True))

