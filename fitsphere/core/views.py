from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout as auth_logout
from django.core.mail import send_mail
from django.conf import settings
from .forms import RegisterForm, LoginForm
from django.contrib import messages
import requests
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import random
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from django.contrib.auth.decorators import login_required
from .models import Routine, Exercise, RoutineExercise, Meal, Food, FitnessTracker, BMIRecord, Streak, Achievement
from datetime import date, timedelta
from django.db.models import Q

@login_required
def dashboard(request):
    try:
        today = date.today()
        routines = Routine.objects.filter(user=request.user).order_by('-date')
        meals = Meal.objects.filter(user=request.user).order_by('-date')
        
        routine_streak = 0
        if routines.exists():
            last_date = routines[0].date
            if last_date == today or last_date == today - timedelta(days=1):
                routine_streak = 1
                for i in range(1, len(routines)):
                    if routines[i].date == last_date - timedelta(days=1):
                        routine_streak += 1
                        last_date = routines[i].date
                    else:
                        break
        
        meal_streak = 0
        if meals.exists():
            last_date = meals[0].date
            if last_date == today or last_date == today - timedelta(days=1):
                meal_streak = 1
                for i in range(1, len(meals)):
                    if meals[i].date == last_date - timedelta(days=1):
                        meal_streak += 1
                        last_date = meals[i].date
                    else:
                        break

        achievements = Achievement.objects.filter(user=request.user)
        if not achievements.filter(name="First Meal").exists() and meals.exists():
            Achievement.objects.create(user=request.user, name="First Meal", description="Logged your first meal!")
        if not achievements.filter(name="First Routine").exists() and routines.exists():
            Achievement.objects.create(user=request.user, name="First Routine", description="Planned your first workout!")
        if not achievements.filter(name="10k Steps").exists() and FitnessTracker.objects.filter(user=request.user, steps__gte=10000).exists():
            Achievement.objects.create(user=request.user, name="10k Steps", description="Hit 10,000 steps in a day!")
        if not achievements.filter(name="Week Streak").exists() and (routine_streak >= 7 or meal_streak >= 7):
            Achievement.objects.create(user=request.user, name="Week Streak", description="Maintained a 7-day streak!")
        if not achievements.filter(name="First BMI").exists() and BMIRecord.objects.filter(user=request.user).exists():
            Achievement.objects.create(user=request.user, name="First BMI", description="Tracked your first BMI!")

        context = {
            'routines': routines[:5],
            'routine_streak': routine_streak,
            'meal_streak': meal_streak,
            'meals': meals[:5],
            'fitness': FitnessTracker.objects.filter(user=request.user)[:5],
            'bmi': BMIRecord.objects.filter(user=request.user)[:5],
            'achievements': achievements[:5]
        }
        return render(request, 'dashboard.html', context)
    except Exception as e:
        return render(request, 'dashboard.html', {'error': str(e)})

@login_required
def logout_view(request):
    auth_logout(request)
    return redirect('landing')

def landing(request):
    return render(request, 'landing.html')

@login_required
def workout_planner(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        date = request.POST.get('date')
        duration = request.POST.get('duration')
        exercise_ids = request.POST.getlist('exercises')
        sets = request.POST.getlist('sets')
        reps = request.POST.getlist('reps')
        dropsets = request.POST.getlist('dropsets')
        supersets = request.POST.getlist('supersets')
        
        routine = Routine.objects.create(name=name, user=request.user, date=date, duration=duration)
        for i, ex_id in enumerate(exercise_ids):
            RoutineExercise.objects.create(
                routine=routine,
                exercise_id=ex_id,
                sets=int(sets[i]) if sets[i] else 1,
                reps=int(reps[i]) if reps[i] else 1,
                is_dropset=bool(dropsets[i] if i < len(dropsets) else False),
                is_superset=bool(supersets[i] if i < len(supersets) else False)
            )
        return redirect('dashboard')
    exercises = Exercise.objects.all()
    return render(request, 'workout_planner.html', {'exercises': exercises})

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            login_field = form.cleaned_data['login']
            password = form.cleaned_data['password']
            user = authenticate(request, email=login_field, password=password)
            if user is None:  # Try username if email fails
                user = authenticate(request, username=login_field, password=password)
            if user is not None:
                auth_login(request, user)  # Use auth_login to avoid conflict
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid login credentials')
        else:
            messages.error(request, 'Invalid form submission')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            otp = str(random.randint(100000, 999999))
            request.session['otp'] = otp
            request.session['reset_email'] = email
            send_mail(
                'FitSphere Password Reset OTP',
                f'Your OTP is: {otp}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            return redirect('reset_password')
        except User.DoesNotExist:
            return render(request, 'forgot_password.html', {'error': 'Email not found'})
    return render(request, 'forgot_password.html')

def reset_password(request):
    if request.method == 'POST':
        otp = request.POST.get('otp')
        new_password = request.POST.get('new_password')
        if otp == request.session.get('otp'):
            user = User.objects.get(email=request.session.get('reset_email'))
            user.set_password(new_password)
            user.save()
            del request.session['otp']
            del request.session['reset_email']
            return redirect('login')
        return render(request, 'reset_password.html', {'error': 'Invalid OTP'})
    return render(request, 'reset_password.html')


@login_required
def chatbot(request):
    chat_history = request.session.get('chat_history', [])
    return render(request, 'chatbot.html', {'chat_history': chat_history})


@login_required
def diet_planner(request):
    if request.method == 'POST':
        date = request.POST.get('date')
        food_ids = request.POST.getlist('foods')
        quantities = request.POST.getlist('quantities')
        for food_id, qty in zip(food_ids, quantities):
            Meal.objects.create(user=request.user, date=date, food_id=food_id, quantity=float(qty))
        return redirect('dashboard')
    foods = Food.objects.all()
    if 'search' in request.GET:
        foods = foods.filter(name__icontains=request.GET['search'])
    if 'veg' in request.GET:
        foods = foods.filter(is_veg=(request.GET['veg'] == 'true'))
    if 'restriction' in request.GET:
        foods = foods.filter(restrictions__icontains=request.GET['restriction'])
    meals = Meal.objects.filter(user=request.user)
    return render(request, 'diet_planner.html', {'foods': foods, 'meals': meals})

@login_required
def fitness_tracker(request):
    if request.method == 'POST':
        date = request.POST.get('date')
        steps = int(request.POST.get('steps', 0))
        distance = float(request.POST.get('distance', 0))
        time = int(request.POST.get('time', 0))
        # Auto-calculate calories (simplified MET-based formula)
        weight = request.user.weight or 70  # Default 70kg if not set
        mets = 4.0  # Moderate walking MET value
        calories_burned = mets * weight * (time / 60)  # kcal = MET * kg * hours
        
        FitnessTracker.objects.create(
            user=request.user, date=date, steps=steps, distance=distance, time=time, calories_burned=calories_burned
        )
        # Google Fit Sync Placeholder
        # Requires: pip install google-auth-oauthlib google-api-python-client
        # flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        #     'client_secrets.json', scopes=['https://www.googleapis.com/auth/fitness.activity.write']
        # )
        # creds = flow.run_local_server(port=0)
        # service = build('fitness', 'v1', credentials=creds)
        return redirect('dashboard')
    tracker = FitnessTracker.objects.filter(user=request.user)
    return render(request, 'fitness_tracker.html', {'tracker': tracker})

@login_required
def bmi_tracker(request):
    if request.method == 'POST':
        date = request.POST.get('date')
        height = request.POST.get('height')
        weight = request.POST.get('weight')
        BMIRecord.objects.create(user=request.user, date=date, height=height, weight=weight)
        return redirect('dashboard')
    records = BMIRecord.objects.filter(user=request.user)
    return render(request, 'bmi_tracker.html', {'records': records})

@login_required
@require_POST
def chatbot_clear(request):
    if 'chat_history' in request.session:
        del request.session['chat_history']
    return JsonResponse({'status': 'cleared'})

@login_required
@require_POST
def chatbot_message(request):
    message = request.POST.get('message').lower()
    api_key = ""  # Replace with your real key NOW
    
    # Fitness/diet tips logic
    if 'workout' in message or 'exercise' in message:
        response = "Try a 20-min HIIT session: 10 burpees, 15 squats, 20 jumping jacks—repeat 3x for a killer burn!"
    elif 'diet' in message or 'food' in message:
        response = "Fuel up with 100g chicken breast (31g protein, 165 cal) and 200g broccoli (7g carbs, 70 cal)—lean and mean!"
    elif 'motivation' in message or 'inspire' in message:
        response = "You’re a titan carving your legacy—every rep, every bite bends the world to your will. Keep ruling!"
    else:
        # Real Gemini API call
        try:
            resp = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
                json={"contents": [{"parts": [{"text": message}]}]},
                headers={"Content-Type": "application/json"},
                params={"key": api_key}
            )
            resp.raise_for_status()
            response = resp.json()['candidates'][0]['content']['parts'][0]['text']
        except requests.exceptions.RequestException as e:
            response = f"Error: {str(e)}"

    chat_history = request.session.get('chat_history', [])
    chat_history.append({"user": message, "bot": response})
    request.session['chat_history'] = chat_history[-5:]
    return JsonResponse({'user': message, 'bot': response})

