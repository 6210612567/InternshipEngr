from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.template.defaultfilters import title
from django.urls import reverse
from django.contrib import messages


from account.models import Account
from .models import *
import datetime
from .forms import ThreadForm, MarkdownForm
# Create your views here.


def index(request):
    return render(request, "thread/index.html")


def search_page(request):
    thread_list = []
    check_search = False
    search = ""
    # use when user search Thread
    if request.method == "POST":
        search = request.POST["search"]
        thread_list = []
        check_search = True
        for x in Thread.objects.filter(status=True):
            if x.search(search):
                thread_list.append(x)
    return render(request, "thread/search_page.html", {"thread_list": thread_list[::-1], "check_search": check_search, "title": search})


def thread_page(request):
    thread_list = []
    check_search = False
    search = ""
    # use when user search Thread
    if request.method == "POST":
        search = request.POST["search"]
        thread_list = []
        check_search = True
        for x in Thread.objects.filter(status=True):
            account = Account.objects.get(user=x.author)
            if account.type == "Professor":
                if x.search(search):
                    thread_list.append(x)
    # use when user didnt search Thread so it will return all Thread
    else:
        for n in Thread.objects.filter(status=True):
            account = Account.objects.get(user=n.author)
            if account.type == "Professor":
                thread_list.append(n)
    return render(request, "thread/thread_page.html", {"thread_list": thread_list[::-1], "check_search": check_search, "title": search})


def create_thread(request):
    if not request.user.is_authenticated:
        messages.warning(request, "Login First to proceed")
        return HttpResponseRedirect(reverse("account:index"))

    if request.method == "POST":
        header = request.POST["header"]
        content = MarkdownForm(request.POST)
        icon = request.FILES['fileupload']
        desc = request.POST["desc"]
        if Thread.objects.filter(header=header).first():
            return render(request, 'thread/create_thread.html', {
                "fail_header": "This header is already taken",
                "form": content
            })
        if content.is_valid():
            content = content.cleaned_data['Content']
            new_thread = Thread.objects.create(header=header, content=content, icon=icon, author=request.user, desc=desc,
                                               date=datetime.datetime.now(datetime.timezone.utc))
            new_thread.save()

            if Account.objects.get(user=request.user).type == "Professor":
                return HttpResponseRedirect(reverse("thread:thread_page"))
            else:
                return HttpResponseRedirect(reverse("thread:annoucement_page"))
    else:
        content = MarkdownForm()
    return render(request, 'thread/create_thread.html', {'form': content})


def thread(request, thread_id):
    this_thread = get_object_or_404(Thread, id=thread_id)
    return render(request, "thread/thread.html", {
        "thread": this_thread,
    })


def delete_thread(request, thread_id):
    if not request.user.is_authenticated:
        messages.warning(request, "Login First to proceed")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    this_thread = Thread.objects.get(id=thread_id)

    if request.user.username != this_thread.author.username:
        return HttpResponseRedirect(reverse("thread:thread", args=(thread_id,)))

    this_thread.delete()
    return HttpResponseRedirect(reverse("thread:thread_page"))


def update_thread(request, thread_id):
    this_thread = get_object_or_404(Thread, id=thread_id)
    check_update = 1
    # Check user is own this Thread
    if request.user.username != this_thread.author.username:
        return HttpResponseRedirect(reverse("thread:thread", args=(this_thread.id,)))

    # If user submit update form
    if request.method == "POST":
        form = ThreadForm(request.POST)

        if form.is_valid():
            header = form.cleaned_data['header']
            content = form.cleaned_data['content']
            # desc = request.POST["desc"]
            # Update  This Thread
            this_thread.header = header
            this_thread.content = content
            # this_thread.desc = desc
            this_thread.save()

            return HttpResponseRedirect(reverse("thread:thread", args=(this_thread.id,)))
    else:
        content = ThreadForm(request.POST or None, instance=this_thread)

    return render(request, "thread/thread.html", {
        "thread": this_thread,
        "check_update": check_update,
        "form": content,
    })


def annoucement_page(request):
    annoucement_list = []
    check_search = False
    search = ""
    # use when user search Annoucement
    if request.method == "POST":
        search = request.POST["search"]
        check_search = True
        for x in Thread.objects.filter(status=True):
            account = Account.objects.get(user=x.author)
            if account.type == "Company":
                if x.search(search):
                    annoucement_list.append(x)
    # use when user didnt search Thread so it will return all Annoucement
    else:
        for n in Thread.objects.filter(status=True):
            account = Account.objects.get(user=n.author)
            if account.type == "Company":
                annoucement_list.append(n)
    return render(request, "thread/announcement_page.html", {"annoucement_list": annoucement_list[::-1], "check_search": check_search, "title": search})


def annoucement(request, annoucement_id):
    this_annoucement = get_object_or_404(Thread, id=annoucement_id)
    return render(request, "thread/annoucement.html", {
        "annoucement": this_annoucement,
    })


def admin(request):
    if not request.user.is_authenticated:
        messages.warning(request, "Login First to proceed")
        return HttpResponseRedirect(reverse("account:index"))

    if not request.user.is_superuser:
        messages.warning(request, "Permission needed")
        return HttpResponseRedirect(reverse("account:index"))

    annoucement = []
    thread = []
    for x in Thread.objects.all().order_by('-date'):
        account = Account.objects.get(user=x.author)
        if account.type == "Company":
            annoucement.append(x)
        if account.type == "Professor":
            thread.append(x)

    return render(request, "thread/admin.html", {
        "thread": thread,
        "annoucement": annoucement,
    })


def remove_thread(request, thread_id):

    if not request.user.is_authenticated:
        messages.warning(request, "Login First to proceed")
        return HttpResponseRedirect(reverse("account:index"))

    if not request.user.is_superuser:
        messages.warning(request, "Permission needed")
        return HttpResponseRedirect(reverse("account:index"))
    Thread.objects.get(id=thread_id).icon.delete(save=True)
    Thread.objects.get(id=thread_id).delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


def change_status_thread(request, thread_id):

    if not request.user.is_authenticated:
        messages.warning(request, "Login First to proceed")
        return HttpResponseRedirect(reverse("account:index"))

    if not request.user.is_superuser:
        messages.warning(request, "Permission needed")
        return HttpResponseRedirect(reverse("account:index"))

    this_dorm = get_object_or_404(Thread, id=thread_id)

    this_dorm.status = not(this_dorm.status)

    this_dorm.save()
    return HttpResponseRedirect(reverse("thread:admin"))
