from django.db import models
from django.core.validators import MinValueValidator
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models import F, Sum
from django.utils import timezone
from django.db.models import Case, Value, When


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class OrderQuerySet(models.QuerySet):
    def price(self):
        return self.annotate(
            price=Sum(F('elements__product__price')*F('elements__quantity'))
        )

    def order_status(self):
        return self.annotate(
            order_status=Case(
                When(status='new', then=Value(1)),
                When(status='assembly', then=Value(2)),
                When(status='delivery', then=Value(3)),
                When(status='completed', then=Value(4)),
            )
        ).order_by('order_status')


class Order(models.Model):
    STATUS_CHOICES = (
        ('new', 'Необработанный'),
        ('assembly', 'В сборке'),
        ('delivery', 'В пути'),
        ('completed', 'Доставлен'),
    )
    PAY_CHOICES = (
        ('online', 'Онлайн'),
        ('cash', 'Наличными'),
    )
    firstname = models.CharField(
        'Имя',
        max_length=50,
        db_index=True,
    )
    lastname = models.CharField(
        'Фамилия',
        max_length=50,
        db_index=True,
    )
    phonenumber = PhoneNumberField(
        region='RU',
        verbose_name='Номер телефона',
        db_index=True,)
    address = models.TextField(
        'Адрес',
        max_length=200,
        db_index=True,
    )
    objects = OrderQuerySet.as_manager()
    status = models.CharField(
        max_length=15,
        verbose_name='Статус заказа',
        db_index=True,
        choices=STATUS_CHOICES,
        default='new',
    )
    comment = models.TextField(
        verbose_name='Комментарий',
        blank=True,
    )
    registrated_at = models.DateTimeField(
        verbose_name='Заказ зарегистрирован',
        blank=True,
        null=True,
        db_index=True,
        default=timezone.now,
    )
    called_at = models.DateTimeField(
        verbose_name='Позвонить клиенту',
        blank=True,
        null=True,
        db_index=True,
    )
    delivered_at = models.DateTimeField(
        verbose_name='Передан в доставку',
        blank=True,
        null=True,
        db_index=True,
    )
    pay = models.CharField(
        max_length=20,
        verbose_name='Способ оплаты',
        db_index=True,
        choices=PAY_CHOICES,
        null=True,
        blank=True,
    )
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='orders',
        verbose_name="Ресторан",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f"{self.firstname} {self.lastname} {self.address}"


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'Название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='Категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'Цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'Картинка'
    )
    special_status = models.BooleanField(
        'Спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'Описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        return self.name


class OrderElements(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='elements',
        verbose_name='Продукт',
    )
    quantity = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(1)],
    )
    order = models.ForeignKey(
        Order,
        related_name='elements',
        verbose_name='Заказ',
        on_delete=models.CASCADE,
    )
    order_price = models.DecimalField(
        verbose_name='Cтоимость',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'

    def __str__(self):
        return f"{self.product.name} {self.order.firstname} {self.order.lastname} {self.order.address}"


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name='Ресторан',
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='Продукт',
    )
    availability = models.BooleanField(
        'В продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'Пункт меню ресторана'
        verbose_name_plural = 'Пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"
