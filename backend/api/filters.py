from django_filters.rest_framework import FilterSet, filters

from recipes.models import Ingredient, Recipe, Tag
from users.models import User


class FilterIngredient(FilterSet):
    """Фильтр для ингредиентов."""
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='icontains',
        label='Ингредиенты')

    class Meta:
        model = Ingredient
        fields = ('name',)


class FilterRecipe(FilterSet):
    """Фильтр для рецептов."""
    author = filters.ModelChoiceFilter(
        field_name='author',
        queryset=User.objects.all(),
        label='Автор')
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug',
        label='Теги')
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited',
        label='В избранном')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart',
        label='В корзине')

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited',
                  'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if user.is_anonymous:
            return queryset
        if value:
            return queryset.filter(favoriterecipes__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if user.is_anonymous:
            return queryset
        if value:
            return queryset.filter(shoppingcarts__user=user)
        return queryset
