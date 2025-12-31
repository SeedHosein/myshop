from .models import ShopInformation

def shop_information(request):
    shop_information_objects = ShopInformation.objects.all()
    return {
        "ShopInformation": {shop_information_object.name: shop_information_object.value for shop_information_object in shop_information_objects},
    }