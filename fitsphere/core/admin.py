from django.contrib import admin
from .models import User, Food, Meal, Exercise, Routine, FitnessTracker, BMIRecord, Streak, Achievement

admin.site.register(User)
admin.site.register(Food)
admin.site.register(Meal)
admin.site.register(Exercise)
admin.site.register(Routine)
admin.site.register(FitnessTracker)
admin.site.register(BMIRecord)
admin.site.register(Streak)
admin.site.register(Achievement)