import random
import string

from django.conf import settings
from django.db.models import F
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .filters import FilterIngredient, FilterRecipe
from .paginations import Pagination
from .permissions import OnlyReadAuthorAdmin
from .serializers import (AvatarSerializer, IngredientSerializer,
                          PasswordSerializer, RecipeSerializer,
                          RecipeWriteSerializer, SubscriptionsSerializer,
                          TagSerializer, UserSerializer)
from recipes.models import Favourites, Ingredient, Recipe, ShoppingCart, Tag
from users.models import Subscriber, User

short_links = {}


class UserViewSet(viewsets.ModelViewSet):
    """Управление пользователями"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = Pagination
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def me(self, request):
        """Возвращает текущего пользователя."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar',
            permission_classes=[IsAuthenticated], parser_classes=[JSONParser])
    def avatar(self, request):
        """Аватара пользователя."""
        user = request.user
        if request.method == 'DELETE':
            user.avatar.delete()
            user.avatar = None
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = AvatarSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=['post'],
            permission_classes=[IsAuthenticated])
    def set_password(self, request):
        """Изменение пароля пользователя."""
        user = request.user
        serializer = PasswordSerializer(data=request.data,
                                        context={'request': request})
        if serializer.is_valid():
            if not user.check_password(
                    serializer.validated_data['current_password']):
                return Response({'detail': 'Текущий пароль неверен.'},
                                status=status.HTTP_400_BAD_REQUEST)
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'detail': 'Пароль успешно изменен.'},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """Возвращает список подписан пользователя."""
        user = request.user
        subscriptions = User.objects.filter(authors__user=user)
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = SubscriptionsSerializer(page, many=True,
                                                 context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = SubscriptionsSerializer(subscriptions, many=True,
                                             context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        """Подписка и отписка от пользователя."""
        user = request.user
        author = get_object_or_404(User, id=pk)
        if request.method == 'POST':
            if Subscriber.objects.filter(user=user, author=author).exists():
                return Response({'detail': 'Вы уже подписаны'},
                                status=status.HTTP_400_BAD_REQUEST)
            Subscriber.objects.create(user=user, author=author)
            serializer = SubscriptionsSerializer(author,
                                                 context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        subscription = Subscriber.objects.filter(user=user,
                                                 author=author).first()
        if not subscription:
            return Response({'detail': 'Вы не подписаны'},
                            status=status.HTTP_400_BAD_REQUEST)
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                 viewsets.GenericViewSet):
    """Управление тегами"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class IngredientViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    """Управление ингредиентами"""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = FilterIngredient
    permission_classes = [AllowAny]
    search_fields = ['name']
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Управление рецептами"""
    queryset = Recipe.objects.all()
    pagination_class = Pagination
    permission_classes = [OnlyReadAuthorAdmin]
    filterset_class = FilterRecipe

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeSerializer
        return RecipeWriteSerializer

    def toggle_recipe_status(self, request, model, pk=None):
        """Добавление или удаление рецепта в избранное или список покупок."""
        recipe = get_object_or_404(Recipe, id=pk)
        obj = model.objects.filter(user=request.user, recipe=recipe)
        if request.method == 'POST':
            if obj.exists():
                return Response({'detail': 'Уже в списке'},
                                status=status.HTTP_400_BAD_REQUEST)
            model.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeSerializer(recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not obj.exists():
                return Response({'detail': 'Не найдено'},
                                status=status.HTTP_400_BAD_REQUEST)
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        """Прямая ссылка на рецепт"""
        recipe = get_object_or_404(Recipe, pk=pk)
        request.build_absolute_uri(reverse('api:recipe-detail',
                                           kwargs={'pk': recipe.pk}))
        short_link = self.generate_short_url()
        full_short_url = f"{settings.DOMAIN_NAME}s/{short_link}"
        return Response({'short-link': full_short_url},
                        status=status.HTTP_200_OK)

    def generate_short_url(self, length=6):
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """Добавление/удаление рецепта в избранное."""
        return self.toggle_recipe_status(request, Favourites, pk)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        """Добавление/удаление рецепта в список покупок."""
        return self.toggle_recipe_status(request, ShoppingCart, pk)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """Скачать список покупок в виде текстового файла."""
        shoppingcart = ShoppingCart.objects.filter(
            user=request.user).values('recipe_id__ingredients__name').annotate(
            amount=F('recipe_id__recipeingredients__amount'),
            measurement_unit=F('recipe_id__ingredients__measurement_unit')
        ).order_by('recipe_id__ingredients__name')
        ingredients = {}
        for ingredient in shoppingcart:
            ingredient_name = ingredient['recipe_id__ingredients__name']
            amount = ingredient['amount']
            measurement_unit = ingredient['measurement_unit']
            if ingredient_name not in ingredients:
                ingredients[ingredient_name] = (amount, measurement_unit)
            else:
                ingredients[ingredient_name] = (
                    ingredients[ingredient_name][0] + amount,
                    measurement_unit)
        with open("shopping_list.txt", "w") as file:
            file.write('Ваш список покупок:' + '\n')
            for ingredient, amount in ingredients.items():
                file.write(f'{ingredient} - {amount[0]}({amount[1]}).' + '\n')
            file.close()
        return FileResponse(open('shopping_list.txt', 'rb'))
