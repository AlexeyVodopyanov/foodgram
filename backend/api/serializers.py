from django.contrib.auth.password_validation import validate_password
from drf_base64.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (Favourites, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscriber, User


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя с улучшенной валидацией"""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name',
                  'email', 'is_subscribed', 'avatar', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        """Создание пользователя с хэшированием пароля."""
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

    def get_is_subscribed(self, obj):
        """Проверка подписки на автора рецепта"""
        request = self.context.get('request')
        if request and not request.user.is_anonymous:
            return Subscriber.objects.filter(user=request.user,
                                             author=obj).exists()
        return False


class PasswordSerializer(serializers.Serializer):
    """Сериализатор для изменения пароля"""
    current_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True,
                                         validators=[validate_password])

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Текущий пароль введен неверно.')
        return value


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Вспомогательный сериализатор для рецептов"""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionsSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок текущего пользователя"""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name',
                  'email', 'is_subscribed', 'recipes', 'recipes_count',
                  'avatar')

    def get_is_subscribed(self, obj):
        """Проверка подписки"""
        request = self.context.get('request')
        if request and not request.user.is_anonymous:
            return Subscriber.objects.filter(user=request.user,
                                             author=obj).exists()
        return False

    def get_recipes(self, obj):
        """Возвращает ограниченный список рецептов автора"""
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        queryset = obj.recipes.all()
        if limit:
            queryset = queryset[:int(limit)]
        return ShortRecipeSerializer(queryset, many=True,
                                     context={'request': request}).data

    def get_recipes_count(self, obj):
        """Возвращает количество рецептов автора"""
        return obj.recipes.count()

    def validate_subscription(self, obj):
        """Запрещает подписку на самого себя"""
        if self.context['request'].user == obj:
            raise serializers.ValidationError('Нельзя подписаться на себя.')
        return obj


class SubscriberSerializer(serializers.ModelSerializer):
    """Сериализатор для модели подписок"""
    class Meta:
        model = Subscriber
        fields = ('user', 'author')

    def validate(self, data):
        """Валидация на подписку самого себя"""
        if data['user'] == data['author']:
            raise serializers.ValidationError('Нельзя подписаться на себя.')
        return data


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов"""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов"""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeInIngredientSerializer(serializers.ModelSerializer):
    """Вспомогательный сериализатор для отображения ингредиентов рецепта"""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all())
    name = serializers.ReadOnlyField(source='ingredients.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredients.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для метода GET рецептов"""
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeInIngredientSerializer(many=True,
                                               read_only=True,
                                               source='recipeingredients')
    author = UserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')

    def get_is_favorited(self, obj):
        """Проверка, является ли рецепт избранным"""
        user = self.context['request'].user
        return (Favourites.objects.filter(user=user,
                                          recipe=obj)
                .exists()) if user.is_authenticated else False

    def get_is_in_shopping_cart(self, obj):
        """Проверка, находится ли рецепт в списке покупок"""
        user = self.context['request'].user
        return (ShoppingCart.objects.filter(user=user,
                                            recipe=obj)
                .exists()) if user.is_authenticated else False


class RecipeWriteIngredientSerializer(serializers.ModelSerializer):
    """Вспомогательный сериализатор для добавления ингредиентов в рецепт"""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и редактирования рецептов"""
    author = UserSerializer(read_only=True)
    ingredients = RecipeWriteIngredientSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                              many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'ingredients', 'tags',
                  'image', 'text', 'cooking_time', 'author')

    def validate(self, data):
        """Валидация на наличие ингредиентов и уникальность"""
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                'Необходимо добавить хотя бы один ингредиент.')
        if (len(set([ingredient['id'] for ingredient in ingredients]))
                != len(ingredients)):
            raise serializers.ValidationError(
                'Ингредиенты должны быть уникальными.')
        return data

    def set_tags(self, recipe, tags):
        recipe.tags.set(tags)

    def set_ingredients(self, recipe, ingredients):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredients=ingredient_data['id'],
                amount=ingredient_data['amount']
            )
            for ingredient_data in ingredients
        ])

    def create(self, validated_data):
        """Создание нового рецепта"""
        request = self.context.get('request')
        author = request.user
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(author=author,
                                       **validated_data)
        self.set_ingredients(recipe, ingredients)
        self.set_tags(recipe, tags)
        return recipe

    def update(self, instance, validated_data):
        """Обновление существующего рецепта"""
        ingredients = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)

        instance = super().update(instance, validated_data)

        if ingredients is not None:
            instance.ingredients.clear()
            self.set_ingredients(instance, ingredients)

        if tags is not None:
            self.set_tags(instance, tags)

        return instance

    def to_representation(self, instance):
        """Корректное отображение созданного/обновленного рецепта"""
        return RecipeSerializer(instance, context=self.context).data


class ShoppingCartModelSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Списка покупок"""
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Избранных рецептов"""
    class Meta:
        model = Favourites
        fields = ('user', 'recipe')


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для аватара"""
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)
