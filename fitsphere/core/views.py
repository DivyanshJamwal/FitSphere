from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.core.mail import send_mail
from django.conf import settings
from .forms import RegisterForm, LoginForm
import requests
import random
from django.contrib.auth.decorators import login_required
from .models import Routine, Exercise

@login_required
def dashboard(request):
    routines = Routine.objects.filter(user=request.user)[:5]  # Last 5 routines
    streak = Routine.objects.filter(user=request.user).count()  # Simple streak proxy
    return render(request, 'dashboard.html', {'routines': routines, 'streak': streak})

def landing(request):
    return render(request, 'landing.html')

@login_required
def workout_planner(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        date = request.POST.get('date')
        duration = request.POST.get('duration')
        exercise_ids = request.POST.getlist('exercises')
        routine = Routine.objects.create(
            name=name, user=request.user, date=date, duration=duration
        )
        routine.exercises.set(exercise_ids)
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
                login(request, user)  # Fixed: Pass request and user
                return redirect('dashboard')
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
    if request.method == 'POST':
        message = request.POST.get('message')
        # Mock Gemini API response (replace with real key later)
        response = f"FitSphere Bot: I hear you say '{message}'. Try asking for a workout tip, motivation, or plan help!"
        # Real Gemini API call (uncomment with key):
        # api_key = "YOUR_GEMINI_API_KEY_HERE"
        # try:
        #     resp = requests.post(
        #         "https://api.gemini.com/v1/chat",  # Placeholder URL; adjust to actual Gemini endpoint
        #         json={"message": message, "model": "gemini-1.0"},
        #         headers={"Authorization": f"Bearer {api_key}"}
        #     )
        #     response = resp.json().get('reply', 'Error: No response from Gemini')
        # except requests.exceptions.RequestException as e:
        #     response = f"Error: {str(e)}"
        
        # Store chat history in session
        chat_history = request.session.get('chat_history', [])
        chat_history.append({"user": message, "bot": response})
        request.session['chat_history'] = chat_history[-5:]  # Keep last 5 messages
        return render(request, 'core/chatbot.html', {'chat_history': chat_history})
    chat_history = request.session.get('chat_history', [])
    return render(request, 'core/chatbot.html', {'chat_history': chat_history})