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


class OrderElementsSerializer(ModelSerializer):
    class Meta:
        model = OrderElements
        fields = ['product', 'quantity']    


class OrderSerializer(ModelSerializer):
    products = OrderElementsSerializer(many=True)
    class Meta:
        model = Order
        fields = ['firstname', 'lastname', 'phonenumber', 'address', 'products']


def validate(order):
    try:
        errors = []
        if len(order['products']) == 0:
            errors.append(['Этот список не может быть пустым.'])
        if isinstance(order['products'], str):
            errors.append(['Ожидался list со значениями, но был получен "str".'])
        if not phonenumbers.is_valid_number(phonenumbers.parse(order['phonenumber'])):
            errors.append(['введен неверный номер телефона.'])
        for product in order['products']:
            if not product:
                errors.append(['products: Обязательное поле.'])
            if not isinstance(product, dict):
                errors.append(['products:Это поле не может быть пустым.'])
            Product.objects.get(id=product['product'])

    except Product.DoesNotExist:
        raise ValidationError([f'Недопустимый первичный ключ {product['product']}'])

    if errors:
        raise ValidationError(errors)

    return(order)


@api_view(['POST'])
def register_order(request):
    order = json.dumps(request.data, ensure_ascii=False)
    order = json.loads(order)

    serializer = OrderSerializer(data=order)
    serializer.is_valid(raise_exception=True)
    
    order = validate(order)
    new_order = Order.objects.get_or_create(
        firstname=serializer.validated_data['firstname'],
        lastname=serializer.validated_data['lastname'],
        phonenumber=serializer.validated_data['phonenumber'],
        address=serializer.validated_data['address'],
    )
    for product in serializer.validated_data['products']:
        OrderElements.objects.get_or_create(
            order_id=new_order[0].id,
            products_id=product['product'],
            quantity=product['quantity'],
        )

    return Response(order)

