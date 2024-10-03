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
    @admin.display(description='Подписчики')
    def get_subscribers(self, obj):
        subscribers = Subscriber.objects.filter(author_id=obj.id)
        return [i.user for i in subscribers]
    list_display = ('id', 'username', 'first_name', 'last_name',
                    'email', 'get_subscribers',)
    list_filter = ('username',)
    search_fields = ('username',)
    ordering = ('username',)


class AdminRecipeIngredientInline(admin.TabularInline):
    """Модель для отображения ингредиентов рецепта в табличной форме."""
    model = RecipeIngredient
    min_num = 1


class AdminRecipe(admin.ModelAdmin):
    """Админ модель для рецептов."""
    @admin.display(description='Теги')
    def get_tags(self, obj):
        return ', '.join([tag.name for tag in obj.tags.all()])

    @admin.display(description='Ингредиенты')
    def get_ingredients(self, obj):
        ingredients = obj.recipeingredients.all()
        return (', '.join(
                [f'{ingredient.ingredients} - {ingredient.amount} '
                 f'{ingredient.ingredients.measurement_unit}'
                 for ingredient in ingredients]))
    inlines = (AdminRecipeIngredientInline,)
    list_display = ('id', 'name', 'author',
                    'get_tags', 'get_ingredients',)
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = 'Незадано'


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
