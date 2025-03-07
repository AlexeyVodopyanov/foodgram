# Generated by Django 3.2.3 on 2024-10-06 23:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Favourites',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name': 'Рецепт - пользователь',
                'verbose_name_plural': 'Рецепт - пользователь',
                'ordering': ('recipe',),
            },
        ),
        migrations.CreateModel(
            name='Ingredient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Назовите ингредиента', max_length=200, unique=True, verbose_name='Ингредиент')),
                ('measurement_unit', models.CharField(help_text='Укажите единицы измерения', max_length=200, verbose_name='Единицы измерения')),
            ],
            options={
                'verbose_name': 'Ингредиент',
                'verbose_name_plural': 'Ингредиент',
                'ordering': ('id', 'name'),
            },
        ),
        migrations.CreateModel(
            name='Recipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(help_text='Выложите изображение', upload_to='recipes_images', verbose_name='Изображение')),
                ('name', models.CharField(help_text='Назовите название рецепта', max_length=200, verbose_name='Рецепт')),
                ('text', models.TextField(help_text='Укажите описание рецепта', verbose_name='Описание')),
                ('cooking_time', models.PositiveSmallIntegerField(help_text='Укажите время приготовления от 1 мин', verbose_name='Время приготовления')),
            ],
            options={
                'verbose_name': 'Рецепт',
                'verbose_name_plural': 'Рецепты',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='RecipeIngredient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.PositiveSmallIntegerField(help_text='Укажите сколько ингредиента, от 1 и более', verbose_name='Сколько ингредиента')),
            ],
            options={
                'verbose_name': 'Ингредиент - рецепта',
                'verbose_name_plural': 'Ингредиент - рецепта',
                'ordering': ('recipe',),
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Назовите тега', max_length=200, unique=True, verbose_name='Тег')),
                ('slug', models.SlugField(help_text='Назовите аббревиатуру', max_length=200, null=True, unique=True, verbose_name='Аббревиатура')),
            ],
            options={
                'verbose_name': 'Тег',
                'verbose_name_plural': 'Теги',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='ShoppingCart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recipe', models.ForeignKey(help_text='Назовите название рецепта', on_delete=django.db.models.deletion.CASCADE, related_name='shoppingcarts', to='recipes.recipe', verbose_name='Рецепт')),
            ],
            options={
                'verbose_name': 'Список покупок',
                'verbose_name_plural': 'Список покупок',
                'ordering': ('recipe',),
            },
        ),
    ]
