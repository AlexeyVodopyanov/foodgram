from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from import_export.admin import ImportExportActionModelAdmin

from .models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import Subscriber, User


class AdminSubscribersInline(admin.TabularInline):
    """Модель для отображения подписчиков пользователя в админ интерфейсе."""
    model = Subscriber
    min_num = 1


class AdminUser(UserAdmin):
    """Админ модель для пользователей."""
    list_display = ('id', 'username', 'first_name', 'last_name',
                    'email', 'get_subscribers',)
    list_filter = ('username',)
    search_fields = ('username',)
    ordering = ('username',)

    @admin.display(description='Подписчики')
    def get_subscribers(self, obj):
        subscribers = (Subscriber.objects.filter(author_id=obj.id)
                       .values_list('user__username', flat=True))
        return ', '.join(subscribers)


class AdminRecipeIngredientInline(admin.TabularInline):
    """Модель для отображения ингредиентов рецепта в табличной форме."""
    model = RecipeIngredient
    min_num = 1


class AdminRecipe(admin.ModelAdmin):
    """Админ модель для рецептов."""
    inlines = (AdminRecipeIngredientInline,)
    list_display = ('id', 'name', 'author',
                    'get_tags', 'get_ingredients',)
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = 'Незадано'

    @admin.display(description='Теги')
    def get_tags(self, obj):
        tags = obj.tags.values_list('name', flat=True)
        return ', '.join(tags)

    @admin.display(description='Ингредиенты')
    def get_ingredients(self, obj):
        ingredients = obj.recipeingredients.values_list(
            'ingredients__name', 'amount', 'ingredients__measurement_unit')
        return ', '.join(
            [f'{ingredient[0]} - {ingredient[1]} {ingredient[2]}'
             for ingredient in ingredients])


class AdminIngredient(ImportExportActionModelAdmin, admin.ModelAdmin):
    """Админ модель для ингредиентов."""
    list_display = ('id', 'name', 'measurement_unit',)
    list_filter = ('name',)
    search_fields = ('name',)
    ordering = ('name',)


admin.site.register(User, AdminUser)
admin.site.register(Tag)
admin.site.register(Ingredient, AdminIngredient)
admin.site.register(Recipe, AdminRecipe)
