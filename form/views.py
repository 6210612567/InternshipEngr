from concurrent.futures import process
from tokenize import String
from django.dispatch import receiver
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.template.defaultfilters import title
from django.urls import reverse
from django.contrib import messages

from account.models import Account
from .models import *
import datetime
from .forms import FormForm, MarkdownForm
import mimetypes
# use default_storage
from django.core.files.storage import default_storage
# Create your views here.


def index(request):
    form = Init_form.objects.all()
    return render(request, "form/index.html", {'form': form})


def generate_filename(file):

    filetype = file.name.split(".")[-1]
    time_now = datetime.datetime.now(datetime.timezone.utc)
    new_name = time_now.strftime(
        "%d%m%y, %H%M%S") + "_" + str(len(Transmit_file.objects.all())) + "." + filetype
    file.name = new_name

    return file


def create_initform(request):
    if not request.user.is_authenticated:
        messages.warning(request, "Login First to proceed")
        return HttpResponseRedirect(reverse("account:index"))

    if request.method == "POST":
        name = request.POST["name"]
        desc = request.POST["desc"]
        file = request.FILES['form_file']
        content = MarkdownForm(request.POST)
        user = Account.objects.get(user=request.user)
        # Check name is already taken or not
        if Init_form.objects.filter(name=name).first():
            return render(request, 'form/create_initform.html', {
                "fail_name": "This name is already taken",
                "content": content
            })
        if content.is_valid():
            content = content.cleaned_data['Content']

            count = 0
            for x in Init_form.objects.all():
                count += 1
                filetype = file.name.split(".")[-1]
                time_now = datetime.datetime.now(datetime.timezone.utc)
                new_name = time_now.strftime(
                    "%d%m%y, %H%M%S") + "_" + str(count) + "." + filetype
                file.name = new_name

            new_form = Init_form.objects.create(
                name=name, content=content, file=file, author=user, desc=desc, date=datetime.datetime.now(datetime.timezone.utc))
            new_form.save()
            return HttpResponseRedirect(reverse("form:index"))
    else:
        content = MarkdownForm()
    return render(request, 'form/create_initform.html', {'content': content})


def download_file(request, file_id):
    form_field = Init_form.objects.get(id=file_id)
    # Set the return value of the HttpResponse
    response = HttpResponse(form_field.file)
    # Set the HTTP header for sending to browser
    response['Content-Disposition'] = "attachment; filename=%s" % form_field.filename()
    # Return the response value
    return response


def form(request, id):
    form = Init_form.objects.get(id=id)
    return render(request, "form/form.html", {'form': form})


def delete_form(request, form_id):
    if not request.user.is_authenticated:
        messages.warning(request, "Login First to proceed")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    this_form = Init_form.objects.get(id=form_id)

    if request.user != this_form.author.user:
        return HttpResponseRedirect(reverse("form:form", args=(form_id,)))

    this_form.delete()
    return HttpResponseRedirect(reverse("form:index"))


def update_form(request, form_id):
    this_form = Init_form.objects.get(id=form_id)
    check_update = 1
    # Check user is own this form
    if request.user != this_form.author.user:
        return HttpResponseRedirect(reverse("form:form", args=(this_form.id,)))

    # If user submit update form
    if request.method == "POST":
        form = FormForm(request.POST)

        if form.is_valid():
            name = form.cleaned_data['name']
            content = form.cleaned_data['content']
            desc = request.POST["desc"]
            # Update  This form
            this_form.name = name
            this_form.content = content
            this_form.desc = desc
            this_form.save()

            return HttpResponseRedirect(reverse("form:form", args=(this_form.id,)))
    else:
        content = FormForm(request.POST or None, instance=this_form)

    return render(request, "form/form.html", {
        "form": this_form,
        "check_update": check_update,
        "form_update": content,
    })


def internship(request):

    if not request.user.is_authenticated:
        messages.warning(request, "Login First to proceed")
        return HttpResponseRedirect(reverse("account:index"))

    receiver = "admin"

    account = Account.objects.get(user=request.user)
    step = account.current_state

    if step == 0:
        init_internship_form = Init_form.objects.get(name="init")

        # student upload file then do
        if request.method == "POST":
            # need to create post to upload feedback
            file = request.FILES['form_file']
            desc = request.POST['desc']
            processed_file = generate_filename(file)
            new_form = Transmit_file.objects.create(
                file=processed_file, desc=desc, sender=account.user.username, receiver=receiver, date=datetime.datetime.now(datetime.timezone.utc))
            new_form.save()

            account.current_state += 1
            account.sent_box.add(new_form)
            account.save()

            # notify staff to sent file
            for staff in Account.objects.filter(type="Staff"):
                staff.receive_box.add(new_form)
                staff.save()

            # recursive to proceed next step
            return HttpResponseRedirect(reverse("form:internship"))

        return render(request, "form/internship.html", {
            "step": step,
            "init_form": init_internship_form
        })

    elif step == 1:

        # get form uploaded from staff
        received_file = account.receive_box

        # student upload file then do
        if request.method == "POST":

            # need to create post to upload feedback
            file = request.FILES['form_file']
            desc = request.POST['desc']
            processed_file = generate_filename(file)
            new_form = Transmit_file.objects.create(
                file=processed_file, desc=desc, sender=account.user.username, receiver=receiver, date=datetime.datetime.now(datetime.timezone.utc))
            new_form.save()

            account.current_state += 1
            account.sent_box.add(new_form)
            account.save()

            # notify staff to sent file
            for staff in Account.objects.filter(type="Staff"):
                staff.receive_box.add(new_form)
                staff.save()

            # recursive to proceed next step
            return HttpResponseRedirect(reverse("form:internship"))

        return render(request, "form/internship.html", {
            "step": step,
            "forms": received_file.all()
        })

    # uploaded all response wait for final form
    elif step == 2:

        # get form uploaded from staff
        received_file = account.receive_box

        # need reset button to reset step to 0

        return render(request, "form/internship.html", {
            "step": step,
            "forms": received_file.all()
        })

    return render(request, "form/internship.html", {
        "step": step
    })


def restart_internship(request):

    if not request.user.is_authenticated:
        messages.warning(request, "Login First to proceed")
        return HttpResponseRedirect(reverse("account:index"))

    account = Account.objects.get(user=request.user)

    account.current_state = 0

    for o in account.sent_box.all():
        o.delete()
    account.sent_box.clear()

    account.read_box.clear()

    for o in account.receive_box.all():
        o.delete()
    account.receive_box.clear()
    account.save()

    return HttpResponseRedirect(reverse("form:internship"))


def response_form(request, trans_id):

    if not request.user.is_authenticated:
        messages.warning(request, "Login First to proceed")
        return HttpResponseRedirect(reverse("account:index"))

    account = Account.objects.get(user=request.user)

    transmit_file = Transmit_file.objects.get(id=trans_id)

    receiver_acc = Account.objects.get(
        user=User.objects.get(username=transmit_file.sender))

    if request.method == "POST":
        # need to create post to upload feedback
        file = request.FILES['form_file']
        desc = request.POST['desc']
        processed_file = generate_filename(file)
        new_form = Transmit_file.objects.create(
            file=processed_file, desc=desc, sender=account.user.username, receiver=receiver_acc.user.username, date=datetime.datetime.now(datetime.timezone.utc))
        new_form.save()

        account.sent_box.add(new_form)
        account.save()

        receiver_acc.receive_box.add(new_form)
        receiver_acc.save()

        return HttpResponseRedirect(reverse("account:index"))

    return render(request, "form/response.html", {
        "this_file": transmit_file,
        "done": 0
    })
