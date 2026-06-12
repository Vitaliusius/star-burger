import json
import phonenumbers

from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Product, Order, OrderElements
from rest_framework import status
from rest_framework.serializers import ValidationError
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer


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


class OrderSerializer(ModelSerializer):
    def create(self, validated_data):
        return Order.objects.create(**validated_data)
    class Meta:
        model = Order
        fields = ['id', 'firstname', 'lastname', 'phonenumber', 'address']


class OrderElementsSerializer(ModelSerializer):
    product = OrderSerializer(many=True)
    class Meta:
        model = OrderElements
        fields = ['product', 'quantity', 'order_id', 'order']


def validate(order):
    try:
        if isinstance(order['products'], list):
            if len(order['products']) == 0:
                raise ValidationError(['Этот список не может быть пустым.'])
        elif not order['products']:
            raise ValidationError(['products:Это поле не может быть пустым.'])
        elif isinstance(order['products'], str):
            raise ValidationError(['Ожидался list со значениями, но был получен "str".'])
        elif not phonenumbers.is_valid_number(phonenumbers.parse(order['phonenumber'])):
            raise ValidationError(['введен неверный номер телефона.'])
        for product in order['products']:
            if not product:
                raise ValidationError(['products: Обязательное поле.'])

            Product.objects.get(id=product['product'])
    except TypeError as e:
        raise ValidationError([f'{e}'])
    except Product.DoesNotExist:
        raise ValidationError([f'Недопустимый первичный ключ {product['product']}'])


@api_view(['POST'])
def register_order(request):
    order = json.dumps(request.data, ensure_ascii=False)
    order = json.loads(order)
    serializer = OrderSerializer(data=order)
    serializer.is_valid(raise_exception=True)   
    order = validate(order)
    serializer.validated_data
    serializer.save()

    return Response(serializer.data, status=201)

