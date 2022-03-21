from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.template.defaultfilters import title
from django.urls import reverse
from django.contrib import messages
from .models import *
import datetime
from .forms import ThreadForm, MarkdownForm
# Create your views here.


def index(request):
    thread_list = []
    check_search = False
    search = ""
    # use when user search Dormitory
    if request.method == "POST":
        search = request.POST["search"]
        thread_list = []
        check_search = True
        for x in Thread.objects.all():
            if x.search(search):
                thread_list.append(x)
    # use when user didnt search Thread so it will return all Thread
    else:
        for n in Thread.objects.all():
            thread_list.append(n)
    return render(request, "thread/index.html", {"thread_list": thread_list[::-1], "check_search": check_search, "title": search})


def create_thread(request):
    if not request.user.is_authenticated:
        messages.warning(request, "Login First to proceed")
        return HttpResponseRedirect(reverse("dormitory:index"))

    if request.method == "POST":
        header = request.POST["header"]

        content = MarkdownForm(request.POST)

        if Thread.objects.filter(header=header).first():
            return render(request, 'thread/create_thread.html', {
                "fail_header": "This header is already taken",
                "form": content
            })
        if content.is_valid():
            content = content.cleaned_data['Content']
            new_thread = Thread.objects.create(header=header, content=content, author=request.user,
                                               date=datetime.datetime.now(datetime.timezone.utc))
            new_thread.save()

            return HttpResponseRedirect(reverse("thread:index"))
    else:
        content = MarkdownForm()
    return render(request, 'thread/create_thread.html', {'form': content})


def thread(request, thread_id):
    this_thread = get_object_or_404(Thread, id=thread_id)
    check_my_thread = 0
    if request.user.username == this_thread.author.username:
        check_my_thread += 1
    return render(request, "thread/thread.html", {
        "thread": this_thread,
        "check_my_thread": check_my_thread,
    })


def delete_thread(request, thread_id):
    if not request.user.is_authenticated:
        messages.warning(request, "Login First to proceed")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    this_thread = Thread.objects.get(id=thread_id)

    if request.user.username != this_thread.author.username:
        return HttpResponseRedirect(reverse("thread:thread", args=(thread_id,)))

    this_thread.delete()
    return HttpResponseRedirect(reverse("thread:testmd"))


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
            # Update  This Thread
            this_thread.header = header
            this_thread.content = content
            this_thread.save()

            return HttpResponseRedirect(reverse("thread:thread", args=(this_thread.id,)))
    else:
        content = ThreadForm(request.POST or None, instance=this_thread)

    return render(request, "thread/thread.html", {
        "thread": this_thread,
        "check_update": check_update,
        "form": content,
    })
