import json

import phonenumbers

from django.http import JsonResponse
from django.templatetags.static import static
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from rest_framework.serializers import ListField
from .models import Product, Order, OrderElements


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
    products = OrderElementsSerializer(many=True, allow_empty=False, write_only=True)
    def create(self, validated_data):
        instance = validated_data.pop('products')
        new_order = Order.objects.create(
            firstname=validated_data['firstname'],
            lastname=validated_data['lastname'],
            phonenumber=validated_data['phonenumber'],
            address=validated_data['address'],            
            )
        for element in instance:
            OrderElements.objects.create(
                product=element.get('product'),
                quantity=element.get('quantity'),
                order=new_order,
                order_price=element.get("quantity")*element.get('product').price
            )
            
        return new_order 

    class Meta:       
        model = Order
        fields = '__all__'


@api_view(['POST'])
@transaction.atomic
def register_order(request):
    order = json.dumps(request.data, ensure_ascii=False)
    order = json.loads(order)
    serializer_order = OrderSerializer(data=order)
    serializer_order.is_valid(raise_exception=True)
    serializer_order.save()

    return Response(serializer_order.data, status=201)

