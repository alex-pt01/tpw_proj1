from datetime import datetime
from pyclbr import Class
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from app.serializers import *
from django.contrib import messages
from django.contrib.auth import authenticate, login as loginUser, logout as logoutUser
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from app.forms import *
from app.models import *
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.paginator import Paginator
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.authentication import SessionAuthentication
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate

"""
@authentication_classes((TokenAuthentication, ))
@permission_classes((IsAuthenticated, ))
"""


######################Users####################################
@api_view(['GET'])
def get_users(request):
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)

@api_view(['DELETE'])
def del_user(request, id):
    try:
        user = User.objects.get(id=id)
    except User.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    user.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['PUT'])
def update_user(request, id):
    try:
        user = User.objects.get(id=id)
    except User.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    serializer = UserSerializer(user, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def sign_up(request):
    username = request.data['username']
    email = request.data['email']
    password = request.data['password']
    user = User.objects.create(username=username, password=password, email=email)
    user.save()
    return Response(status=status.HTTP_201_CREATED)

@api_view(['POST'])
def log_in(request):
    username = request.data['username']
    password = request.data['password']
    try:
        user = User.objects.get(username=username)
    except UserModel.DoesNotExist:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    else:
        if user.password == (password):
            token, created = Token.objects.get_or_create(user=user)
            serializer = UserSerializer(user, context={'authToken': token})
            return Response({
                "user": serializer.data,
                "token": token.key
            })
        return Response(status=status.HTTP_400_BAD_REQUEST)



######################Products####################################
@api_view(['GET'])
def get_product(request, id):

    try:
        product = Product.objects.get(id=id)
    except Product.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    serializer = ProductSerializer(product,context={"request": request})
    return Response(serializer.data)

@api_view(['GET'])
def get_products(request):
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True, context={"request": request})
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def create_product(request):
    serializer = ProductSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes((IsAuthenticated,))
def update_product(request, id):

    try:
        product = Product.objects.get(id=id)
    except Product.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    serializer = ProductSerializer(product, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def del_product(request, id):
    try:
        product = Product.objects.get(id=id)
    except Product.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if product.seller == request.user or request.user.is_superuser:
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(status=status.HTTP_400_BAD_REQUEST)

######################Promotions####################################
@api_view(['GET'])
def get_promotions(request):
    promotions = Promotion.objects.all()
    serializer = PromotionSerializer(promotions, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def create_promotion(request):
    serializer = PromotionSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
def update_promotion(request, id):
    try:
        promotion = Promotion.objects.get(id=id)
    except Promotion.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    serializer = PromotionSerializer(promotion, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def del_promotion(request, id):
    try:
        promotion = Promotion.objects.get(id=id)
    except Promotion.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    promotion.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

######################Search####################################
@api_view(['POST'])
def search_products(request):
    customQuery = request.data['query'] #"TV SAMSUNG"
    brands = request.data['brands'] #[brand1, brand2]
    price = request.data['price']  #[0,150]
    category = request.data['categories'] #[Cat1, Cat2]
    sellers = request.data['sellers'] #[Seller1, Seller2]
    condition = request.data['condition'] #New Or Used
    inStock = request.data['inStock'] #True or False
    inPromotion = request.data['inPromotion'] #True or False

    allProducts = Product.objects.filter(price__range = (price[0], price[1]))
    if len(inPromotion)!=0:
        if inPromotion == "True":
            allProducts = Product.objects.filter(promotion__isnull=False)
            productsIds = []
            for product in allProducts:
                pr_price = product.price - product.price*product.promotion.discount
                if price[0] <= pr_price <= price[1]:
                    productsIds.append(product.id)
            allProducts = allProducts.filter(id__in=productsIds)

        else:
            allProducts = allProducts.filter(promotion__isnull=True)

    if len(customQuery) != 0:
        allProducts = allProducts.filter(name__icontains = customQuery)

    if len(brands)!=0:
        allProducts = allProducts.filter(brand__iregex=r'(' + '|'.join(brands) + ')')

    if len(category)!=0:
        allProducts = allProducts.filter(category__iregex=r'(' + '|'.join(category) + ')')

    if len(sellers)!=0:
        allProducts = allProducts.filter(seller__iregex=r'(' + '|'.join(sellers) + ')')

    if len(condition)!= 0:
        allProducts = allProducts.filter(condition=condition)

    if len(inStock)!=0:
        allProducts = allProducts.filter(stock = inStock)

    serializer = ProductSerializer(allProducts, many=True,context={"request": request})
    return Response(serializer.data)

######################Comemnts####################################

@api_view(['GET'])
def get_comments(request):
    coms = Comment.objects.all()
    serializer = CommentSerializer(coms, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_commentById(request, id):
    coms = Comment.objects.filter(id=id)
    if not coms:
        return Response(status.HTTP_404_NOT_FOUND)
    serializer = CommentSerializer(coms)
    return Response(serializer.data)

@api_view(['GET'])
def get_commentByProductId(request, productId):
    coms = Comment.objects.filter(product=productId)
    serializer = CommentSerializer(coms, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def create_comment(request):
    request.data['commentDate'] = datetime.now().date()
    serializer = CommentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def del_comment(request, id):
    try:
        comment = Comment.objects.get(id=id)
    except Product.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    comment.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def sold_products(request):
    sold_products = Sold.objects.all()
    serializer = SoldSerializer(sold_products, many=True)
    return Response(serializer.data)













"""
@api_view(['GET'])
@authentication_classes((TokenAuthentication, ))
@permission_classes((IsAuthenticated, ))
def current_user(request):
    username = request.data['utilizador']

    if request.user.is_authenticated:
        shoppingCarts = ShoppingCart.objects.filter(user_id=request.user.id)
        creds = getCredits(request)

        if shoppingCarts:
            assoc = []
            for scs in shoppingCarts:
                scis = ShoppingCartItem.objects.filter(cart_id=scs.id)
                payment = Payment.objects.filter(shopping_cart=scs)[0]
                assoc.append((scis, payment))
            tparams = {'carts': assoc, 'credits': creds}

        else:
            tparams = {'cart': [], 'credits': creds}
        return render(request, 'account.html', tparams)

"""

"""


def account(request):
    if request.user.is_authenticated:
        shoppingCarts = ShoppingCart.objects.filter(user_id=request.user.id)
        creds = getCredits(request)

        if shoppingCarts:
            assoc = []
            for scs in shoppingCarts:
                scis = ShoppingCartItem.objects.filter(cart_id=scs.id)
                payment = Payment.objects.filter(shopping_cart=scs)[0]
                assoc.append((scis, payment))
            tparams = {'carts': assoc, 'credits': creds}

        else:
            tparams = {'cart': [], 'credits': creds}
        return render(request, 'account.html', tparams)
    return redirect('login')


def getCredits(request):
    if request.user.is_superuser:
        userProducts = Product.objects.filter(seller='TechOn')
        buyer = 'TechOn'
    else:
        username = request.user.get_username()
        userProducts = Product.objects.filter(seller=username)
        buyer = username

    credits = 0
    for pr in userProducts:
        sold = Sold.objects.filter(product=pr)
        for s in sold:
            credits += s.total

    payments = Payment.objects.filter(username=buyer)

    creditDiscount = 0
    for p in payments:
        creditDiscount += p.usedCredits

    return round(credits - creditDiscount, 2)


def checkout(request):
    if request.user.is_authenticated:
        tparams = getShoppingCart(request)

        if request.method == 'POST':
            form = paymentForm(request.POST)

            if form.is_valid():
                if request.user.is_superuser:
                    buyer = 'TechOn'
                else:
                    username = request.user.get_username()
                    buyer = username
                data = form.cleaned_data
                type = data['type']
                card_no = data['card_no']
                useCredits = data['useCredits']

                address = data['address']
                pm = PaymentMethod(type=type, card_no=card_no)
                pm.save()
                sp = ShoppingCart(user_id=request.user.id)
                sp.save()
                payment = Payment()
                payment.address = address
                payment.total = round(tparams['total'], 2)
                payment.method = pm
                payment.shopping_cart = sp
                payment.username = buyer
                if useCredits:
                    creds = getCredits(request)
                    if creds <= payment.total:
                        payment.usedCredits = creds
                    else:
                        payment.usedCredits = payment.total
                payment.save()

                for item, quantity in tparams['cart']:
                    spi = ShoppingCartItem()
                    spi.product = item
                    item.quantity = item.quantity - quantity
                    item.save()

                    # Saving Sell Record
                    s = Sold()
                    s.product = item
                    s.total = round(item.price * quantity, 2)
                    if item.promotion:
                        s.total -= round(s.total * item.promotion.discount, 2)
                    s.promotion = item.promotion
                    s.quantity = quantity
                    s.buyer = request.user.get_username()
                    s.save()

                    if item.quantity == 0:
                        item.stock = False
                    item.save()
                    spi.quantity = quantity
                    spi.cart_id = sp.id
                    spi.save()
                carts[request.user.id] = []
                return redirect('account')
        else:
            try:

                if request.user.is_superuser:
                    username = 'TechOn'
                else:
                    username = request.user.get_username()
                payment = Payment.objects.filter(username=username).order_by('-id')[0]
                form = paymentForm(initial={
                    'type': payment.method.type,
                    'card_no': payment.method.card_no
                })

            except:
                form = paymentForm()
        tparams['form'] = form

        return render(request, 'checkout.html', tparams)
    return redirect('login')


def getShoppingCart(request):
    userCart = []
    if request.user.id in carts:
        userCart = carts[request.user.id]
    currentCart = []
    total = 0
    totalDiscount = 0
    userCart.sort(key=lambda a: a[0])
    for item in userCart:
        product = Product.objects.get(id=item[0])
        currentCart.append((product, item[1]))
        total += product.price * item[1]

        if item[1] >= product.quantity:
            item[1] = product.quantity
        if product.promotion:
            totalDiscount += product.price * product.promotion.discount * item[1]
    tparams = {
        'cart': currentCart,
        'subtotal': round(total, 2),
        'discount': round(totalDiscount, 2),
        'total': round(total - totalDiscount, 2),
    }
    return tparams


def addToCart(request, id):
    if request.user.is_authenticated:
        if request.user.id in carts:
            products = [p for p in carts[request.user.id] if str(p[0]) != id]
            curProduct = [p for p in carts[request.user.id] if p not in products]
            if curProduct:
                prod = curProduct[0]
                prod = [id, prod[1] + 1]
                products.append(prod)
                carts[request.user.id] = products
            else:
                carts[request.user.id].append([id, 1])
        else:
            carts[request.user.id] = [[id, 1]]

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    return redirect('login')


def removeFromCart(request, id):
    if request.user.is_authenticated:
        if request.user.id in carts:
            products = [p for p in carts[request.user.id] if str(p[0]) != id]
            carts[request.user.id] = products
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    return redirect('login')


def increaseQuantity(request, id):
    if request.user.is_authenticated:
        products = [p for p in carts[request.user.id] if str(p[0]) != id]
        prod = [p for p in carts[request.user.id] if p not in products][0]
        prod = [id, prod[1] + 1]
        products.append(prod)
        carts[request.user.id] = products
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    return redirect('login')


def decreaseQuantity(request, id):
    if request.user.is_authenticated:
        products = [p for p in carts[request.user.id] if str(p[0]) != id]
        prod = [p for p in carts[request.user.id] if p not in products][0]
        prod = [id, prod[1] - 1]
        products.append(prod)
        carts[request.user.id] = products

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    return redirect('login')


def cart(request):
    if request.user.is_authenticated:
        tparams = getShoppingCart(request)
        return render(request, 'cart.html', tparams)
    return redirect('login')



"""
