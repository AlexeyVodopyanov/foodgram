from django.db import models

from users.models import User


class Tag(models.Model):
    """Модель для тегов рецептов."""
    name = models.CharField(unique=True,
                            max_length=200,
                            verbose_name='Тег',
                            help_text='Назовите тега')

    slug = models.SlugField(max_length=200, null=True,
                            unique=True,
                            verbose_name='Аббревиатура',
                            help_text='Назовите аббревиатуру')

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель для ингредиентов рецептов."""
    name = models.CharField(max_length=200, unique=True,
                            verbose_name='Ингредиент',
                            help_text='Назовите ингредиента')
    measurement_unit = models.CharField(max_length=200,
                                        verbose_name='Единицы измерения',
                                        help_text='Укажите единицы измерения')

    class Meta:
        ordering = ('id', 'name')
        verbose_name = 'Ингредиент'
        verbose_name_plural = verbose_name
        constraints = [models.UniqueConstraint(
            fields=['name', 'measurement_unit'],
            name='unique_name_measurement_unit')]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель для рецептов."""
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='recipes',
                               verbose_name='Автор',
                               help_text='Назовите автора рецепта')
    tags = models.ManyToManyField(Tag, related_name='recipes',
                                  verbose_name='Тег',
                                  help_text='Назовите тега рецепта')
    ingredients = models.ManyToManyField(Ingredient,
                                         through='RecipeIngredient',
                                         related_name='recipes',
                                         verbose_name='Ингредиент',
                                         help_text=('Назовите ингредиента'
                                                    ' рецепта'))
    image = models.ImageField(upload_to='recipes_images',
                              verbose_name='Изображение',
                              help_text='Выложите изображение')
    name = models.CharField(max_length=200, verbose_name='Рецепт',
                            help_text='Назовите название рецепта')
    text = models.TextField(verbose_name='Описание',
                            help_text='Укажите описание рецепта')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        help_text='Укажите время приготовления от 1 мин')

    class Meta:
        ordering = ('name',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Модель для ингредиентов, используемых в рецепте."""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='recipeingredients',
                               verbose_name='Рецепт',
                               help_text='Назовите название рецепта')
    ingredients = models.ForeignKey(Ingredient, on_delete=models.CASCADE,
                                    related_name='recipeingredients',
                                    verbose_name='Ингредиент',
                                    help_text='Назовите ингредиента рецепта')
    amount = models.PositiveSmallIntegerField(
        verbose_name='Сколько ингредиента',
        help_text='Укажите сколько ингредиента, от 1 и более'
    )

    class Meta:
        ordering = ('recipe',)
        verbose_name = 'Ингредиент - рецепта'
        verbose_name_plural = verbose_name
        constraints = [models.UniqueConstraint(
            fields=['recipe', 'ingredients'],
            name='unique_recipe_ingredients')]

    def __str__(self):
        return (f'{self.recipe}: {self.ingredients} - {self.amount} '
                f'{self.ingredients.measurement_unit}')


class Favourites(models.Model):
    """Модель для избранных рецептов."""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='favoriterecipes',
                               verbose_name='Рецепт',
                               help_text='Назовите название рецепта')
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='favoriterecipes',
                             verbose_name='Пользователь',
                             help_text='Назовите пользователя')

    class Meta:
        ordering = ('recipe',)
        verbose_name = 'Рецепт - пользователь'
        verbose_name_plural = verbose_name
        constraints = [models.UniqueConstraint(
            fields=['user', 'recipe'],
            name='unique_recipe_user')]

    def __str__(self):
        return f"{self.user} - {self.recipe}"


class ShoppingCart(models.Model):
    """Модель для списка покупок."""
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='shoppingcarts',
                             verbose_name='Пользователь',
                             help_text='Назовите пользователя')

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='shoppingcarts',
                               verbose_name='Рецепт',
                               help_text='Назовите название рецепта')

    class Meta:
        ordering = ('recipe',)
        verbose_name = 'Список покупок'
        verbose_name_plural = verbose_name
        constraints = [models.UniqueConstraint(
            fields=['user', 'recipe'],
            name='unique_shoppingcart')]

    def __str__(self):
        return f"{self.user} - {self.recipe}"
