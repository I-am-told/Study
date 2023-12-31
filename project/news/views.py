from django.contrib.auth.models import Group
from django.shortcuts import redirect
from django.views.generic import ListView, DetailView, CreateView, DeleteView, UpdateView
from .models import *
from .forms import *
from .filters import PostFilter
from pprint import pprint
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required


class PostList(ListView):
    model = Post
    ordering = '-create'
    template_name = 'posts.html'
    context_object_name = 'posts'
    paginate_by = 3

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = PostFilter(self.request.GET, queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filterset'] = self.filterset
        return context


class PostSearch(PostList):
    template_name = 'search.html'


class PostDetail(DetailView):
    model = Post
    template_name = 'post.html'
    context_object_name = 'post'


class PostCreate(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    raise_exception = True
    permission_required = ('news.add_post')
    model = Post
    template_name = 'post_edit.html'

    def get_form_class(self):
        if self.request.user.groups.filter(name='authors').exists():
            self.form_class = PostForm
            return self.form_class
        else:
            self.form_class = PostFormForStaff
            return self.form_class

    def form_valid(self, form):
        news = form.save(commit=False)
        if self.form_class == PostForm:
            news.author = Author.objects.get(authorUser=self.request.user)
        return super().form_valid(form)


class NewsCreate(PostCreate):

    def form_valid(self, form):
        news = form.save(commit=False)
        news.type = 'NW'
        return super().form_valid(form)


class ArticlesCreate(PostCreate):

    def form_valid(self, form):
        news = form.save(commit=False)
        news.type = 'AR'
        return super().form_valid(form)


class NewsList(PostList):

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(type='NW')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['from'] = 'news'
        return context


class ArticlesList(PostList):

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(type='AR')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['from'] = 'articles'
        return context


class PostUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = ('news.change_post')
    form_class = PostForm
    model = Post
    template_name = 'post_edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['from'] = 'update'
        return context


class PostDelete(PermissionRequiredMixin, DeleteView):
    permission_required = ('news.delete_post')
    model = Post
    template_name = 'post_delete.html'
    success_url = reverse_lazy('post_list')


@login_required
def upgrade_user(request):
    user = request.user
    group = Group.objects.get(name='authors')
    if not user.groups.filter(name='authors').exists():
        group.user_set.add(user)
        Author.objects.create(authorUser=user)
    return redirect('/posts')
