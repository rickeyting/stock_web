from .forms import SignUpForm, InfoEdit, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views import View
from django.views.generic.edit import FormView
from django.contrib import messages
from django.contrib.auth.forms import PasswordResetForm
import random
import string
import smtplib
from email.mime.text import MIMEText
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, get_user_model, logout, update_session_auth_hash
# Create your views here.
User = get_user_model()


def generate_random_password():
    password_length = 8
    letters = string.ascii_letters
    digits = string.digits
    password = ''.join(random.choice(letters + digits) for i in range(password_length))
    return password


class PersonalInfo(View):
    template_name = 'personal_info.html'
    form_class = InfoEdit

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return render(request, self.template_name, {})
        else:
            return redirect('apps')

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            form = self.form_class(request.POST, request.FILES, user=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, '資料已更新')
                return redirect('personal_info')
            else:
                messages.error(request, '更新失敗。請檢查輸入的資料。')
                return render(request, self.template_name, {})
        else:
            return redirect('apps')


def logout_view(request):
    logout(request)
    messages.success(request, '成功登出')
    return redirect('home')


def login_function(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user_exists = User.objects.filter(email=email).exists()
        if user_exists:
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, '成功登入')
            else:
                messages.error(request, '密碼錯誤')
        else:
            messages.error(request, '此Email不存在')
        next_url = request.POST.get('next', 'home')
        return redirect(next_url)
    return render(request, 'home.html', {})


class MyPasswordResetView(FormView):
    form_class = PasswordResetForm
    success_url = reverse_lazy('home')
    template_name = 'home.html'

    def form_valid(self, form):
        # Check if email exists in the database
        email = form.cleaned_data['email']
        user_model = get_user_model()
        try:
            user = user_model.objects.get(email=email)
        except user_model.DoesNotExist:
            # Return an error message or redirect to a page that says the email was not found
            # For example:
            messages.error(self.request, '此Email不存在')
            return redirect('home')

        # Generate a new password and reset user's password
        new_password = generate_random_password()  # Change the length to fit your needs
        user.set_password(new_password)
        user.save()
        # Send the new password to the user's email address
        try:
            # Set up the SMTP connection using TLS
            smtpObj = smtplib.SMTP('smtp.gmail.com', 587)
            smtpObj.starttls()
            smtpObj.login('cureflite@gmail.com', 'qxgiiziaenayzoyy')

            # Create the message
            message = f'Your new password is: {new_password}'
            msg = MIMEText(message)
            msg['Subject'] = 'New Password'
            msg['From'] = 'cureflite@gmail.com'
            msg['To'] = email

            # Send the message
            smtpObj.sendmail('cureflite@gmail.com', email, msg.as_string())

            # Close the connection
            smtpObj.quit()
            messages.success(self.request, '新密碼已寄至您的信箱')
        except smtplib.SMTPException as e:
            # Handle the exception here
            print(f'Error: {e}')

        return redirect('home')


class SignUpFunction(View):
    template_name = 'signup.html'
    form_class = SignUpForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            # Process the form data and create a new user
            user = form.save(commit=False)
            user.save()

            # Log in the user
            email = form.cleaned_data['email']
            password = form.cleaned_data['password1']
            user = authenticate(request, email=email, password=password)
            login(request, user)

            messages.success(request, '註冊成功！')
            return redirect('login')
        else:
            messages.error(request, '註冊失敗。請檢查輸入的資料。')
            return render(request, self.template_name, {})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.user
            old_password = form.cleaned_data.get('old_password')
            if user.check_password(old_password):
                new_password = form.cleaned_data.get('new_password1')
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)  # Keep the user logged in
                messages.success(request, '密碼更新成功')
                return redirect('personal_info')  # Update with the URL of the personal info page
            else:
                messages.error(request, '密碼錯誤')
        else:
            messages.error(request, '密碼錯誤')
    return render(request, 'personal_info.html', {})


@login_required
def access_control_view(request):
    if request.method == 'GET':
        if request.user.staff_status or request.user.is_superuser:
            users = User.objects.all().order_by('-date_joined')
            return render(request, 'access_control.html', {'users': users})
        else:
            messages.error(request, '權限不足')
            return redirect('apps')
    return render(request, 'apps.html', {})


def remove_staff_permission(request, user_id):
    User = get_user_model()
    user = get_object_or_404(User, id=user_id)

    if user.is_superuser:
        # Prevent removing staff permission from superuser
        return redirect('access_control')

    user.is_staff = False
    user.save()
    return redirect('access_control')


def grant_staff_permission(request, user_id):
    User = get_user_model()
    user = get_object_or_404(User, id=user_id)
    print(user_id)
    user.is_staff = True
    user.staff_status = False
    user.save()
    return redirect('access_control')