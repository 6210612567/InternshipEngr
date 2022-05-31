import re
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from account.models import Account
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from thread.models import *
# Create your views here.


def index(request):
    thread_list = []
    annoucement_list = []
    num_thread = 0
    num_annoucement = 0
    for n in Thread.objects.filter(status=True):
        account = Account.objects.get(user=n.author)
        if account.type == "Professor" and num_thread < 4:
            thread_list.append(n)
            num_thread += 1
        if account.type == "Company" and num_annoucement < 4:
            annoucement_list.append(n)
            num_annoucement += 1
        if num_thread == 4 and num_annoucement == 4:
            break

    if request.user.is_authenticated:

        account = Account.objects.get(user=request.user)
        noti_count = 0

        data_notread = []
        data_read = []

        for o in account.receive_box.all():
            if o not in account.read_box.all():
                noti_count += 1
                data_notread.append(o)
            else:
                data_read.append(o)
        return render(request, "account/index.html", {'annoucement_list': annoucement_list, 'thread_list': thread_list, 'noti_count': noti_count, 'data_notread': data_notread, 'data_read': data_read})
    return render(request, "account/index.html", {'annoucement_list': annoucement_list, 'thread_list': thread_list})


def read_notification(request):
    pass


def register_page(request):
    return render(request, "account/register.html")


def login_page(request):
    return render(request, "account/login.html")


def logout(request):
    auth_logout(request)
    messages.warning(request, "Logged out")
    return redirect("account:index")


def login(request):
    # Check user is already login
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("account:index"))
    # Check this view use when submit login or not if not return to index
    if request.method == "POST":
        # login process
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        else:
            messages.warning(request, "Invalid credential")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    return render(request, "account/index.html")


def register(request):
    # Check this view use when call register page or use when submit register form
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        re_password = request.POST["re_password"]
        email = request.POST["email"]
        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]

        tel = request.POST["tel"]
        type = request.POST["type"]
        address = request.POST["address"]
        year = request.POST["year"]
        major = request.POST["major"]

        icon = "12312321"
        #icon = request.FILES['fileupload']

        # Check username is already taken
        if User.objects.filter(username=username).first():
            return render(request, "account/register.html", {"fail_username": "This username is already taken"})
        # Check the validity of a Password
        if (len(password) < 8):
            return render(request, "account/register.html", {"fail_password": "Password must have at least 8"})
        elif not re.search("[a-z]", password):
            return render(request, "account/register.html", {"fail_password": "Password must have at least 1 of a-z"})
        elif not re.search("[A-Z]", password):
            return render(request, "account/register.html", {"fail_password": "Password must have at least 1 of A-Z"})
        elif not re.search("[0-9]", password):
            return render(request, "account/register.html", {"fail_password": "Password must have at least 1 of 0-9"})
        # Check re-password is same as password
        if password != re_password:
            return render(request, "account/register.html", {"fail_re_password": "Invalid password confirm"})
        # Check email is already taken
        if User.objects.filter(email=email).first():
            return render(request, "account/register.html", {"fail_email": "This email is already taken"})
        # Add Object User
        add_user = User(username=username, email=email,
                        first_name=first_name, last_name=last_name)
        add_user.set_password(password)
        add_user.save()

        Account.objects.create(user=add_user, tel=tel, type=type,
                               address=address, year=year, major=major, icon=icon)
        return redirect("account:index")
    return render(request, "account/register.html")


def profile(request, username):
    if request.method == "POST":
        email = request.POST["email"]
        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]

        tel = request.POST["tel"]
        address = request.POST["address"]
        year = request.POST["year"]
        major = request.POST["major"]

        icon = "12312321"

        myuser = Account.objects.get(username=username)
        myuser.user.first_name = first_name
        myuser.user.last_name = last_name
        myuser.user.email = email
        myuser.tel = tel
        myuser.address = address
        myuser.year = year
        myuser.major = major
        myuser.icon = icon
        myuser.save()
        messages.success(request, "Your account has been updated successfully")
        return redirect('account:profile')
    return render(request, "account/profile.html")


def observe(request):
    student = Account.objects.all().filter(type="Student")
    return render(request, "account/observe.html", {
        "students": student,
    })
