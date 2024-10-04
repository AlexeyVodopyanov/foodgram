import random
import string
from io import StringIO

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
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
        serializer = PasswordSerializer(data=request.data,
                                        context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'detail': 'Пароль успешно изменён.'},
                        status=status.HTTP_200_OK)

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
            if self.check_subscription(user, author):
                return Response({'detail': 'Вы уже подписаны'},
                                status=status.HTTP_400_BAD_REQUEST)
            Subscriber.objects.create(user=user, author=author)
            serializer = SubscriptionsSerializer(author,
                                                 context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        subscription = self.get_subscription(user, author)
        if not subscription:
            return Response({'detail': 'Вы не подписаны'},
                            status=status.HTTP_400_BAD_REQUEST)
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def check_subscription(self, user, author):
        """Проверка подписки на автора."""
        return Subscriber.objects.filter(user=user, author=author).exists()

    def get_subscription(self, user, author):
        """Получение подписки."""
        return Subscriber.objects.filter(user=user, author=author).first()


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
        exists = obj.exists()
        if request.method == 'POST':
            if exists:
                return Response({'detail': 'Уже в списке'},
                                status=status.HTTP_400_BAD_REQUEST)
            model.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeSerializer(recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not exists:
                return Response({'detail': 'Не найдено'},
                                status=status.HTTP_400_BAD_REQUEST)
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        """Прямая ссылка на рецепт"""
        get_object_or_404(Recipe, pk=pk)
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
        shopping_cart = ShoppingCart.objects.filter(
            user=request.user).values(
            'recipe_id__ingredients__name',
            'recipe_id__recipeingredients__amount',
            'recipe_id__ingredients__measurement_unit'
        ).order_by('recipe_id__ingredients__name')
        ingredients = {}
        for ingredient in shopping_cart:
            name = ingredient['recipe_id__ingredients__name']
            amount = ingredient['recipe_id__recipeingredients__amount']
            measurement_unit = ingredient[
                'recipe_id__ingredients__measurement_unit']
            if name in ingredients:
                ingredients[name][0] += amount
            else:
                ingredients[name] = [amount, measurement_unit]

        output = StringIO()
        output.write('Ваш список покупок:\n')
        for name, (amount, unit) in ingredients.items():
            output.write(f'{name} - {amount} ({unit}).\n')

        response = HttpResponse(output.getvalue(), content_type='text/plain')
        response['Content-Disposition'] = ('attachment; '
                                           'filename="shopping_list.txt"')
        return response
