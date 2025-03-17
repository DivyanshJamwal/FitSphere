from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import MinLengthValidator, MaxLengthValidator, RegexValidator

class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        if not username:
            raise ValueError("Username is required")
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, username, password, **extra_fields)

class User(AbstractUser):
    first_name = models.CharField(max_length=50)
    username = models.CharField(
        max_length=20,
        unique=True,
        validators=[
            MinLengthValidator(5),
            MaxLengthValidator(20),
            RegexValidator(r'^[a-zA-Z0-9]+$', "Only alphanumeric characters allowed")
        ]
    )
    email = models.EmailField(unique=True)
    weight = models.FloatField(null=True, blank=True, help_text="Weight in kg")
    goal = models.CharField(max_length=50, choices=[('lose weight', 'Lose Weight'), ('maintain', 'Maintain'), ('gain', 'Gain')], default='maintain')

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

class Exercise(models.Model):
    DIFFICULTY_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ]
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=50)
    is_home = models.BooleanField(default=True)
    difficulty = models.CharField(max_length=12, choices=DIFFICULTY_CHOICES, default='Beginner')

    def __str__(self):
        return self.name

class Routine(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    exercises = models.ManyToManyField(Exercise)
    date = models.DateField()
    duration = models.PositiveIntegerField(help_text="Duration in minutes")

    def __str__(self):
        return f"{self.name} - {self.user.username}"

class Food(models.Model):
    food_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    calories = models.FloatField(help_text="Calories per 100g")
    protein = models.FloatField(help_text="Protein per 100g")
    carbs = models.FloatField(help_text="Carbs per 100g")
    fat = models.FloatField(help_text="Fat per 100g")

    def __str__(self):
        return self.name

class Meal(models.Model):
    meal_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    quantity = models.FloatField(help_text="Quantity in grams")

    def __str__(self):
        return f"{self.user.username} - {self.food.name} on {self.date}"

class FitnessTracker(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    steps = models.PositiveIntegerField(default=0)
    distance = models.FloatField(default=0, help_text="Distance in km")
    time = models.PositiveIntegerField(default=0, help_text="Time in minutes")
    calories_burned = models.FloatField(default=0, help_text="Calories burned")

    def __str__(self):
        return f"{self.user.username} - {self.date}"

class BMIRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    height = models.FloatField(help_text="Height in meters")
    weight = models.FloatField(help_text="Weight in kg")
    bmi = models.FloatField(editable=False)

    def save(self, *args, **kwargs):
        self.bmi = self.weight / (self.height ** 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - BMI {self.bmi} on {self.date}"