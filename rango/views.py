from django.shortcuts import render

from rango.models import Category, Page

from rango.forms import CategoryForm, PageForm, UserForm, UserProfileForm

from django.http import HttpResponse, HttpResponseRedirect

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

def index(request):
    category_list = Category.objects.order_by('-likes')[:5]
    category_list_views = Category.objects.order_by('-views')[:5]
    context_dict = {'categories':category_list,'categories_views':category_list_views}
    return render(request, 'rango/index.html', context_dict)

def about(request):
    context_dict = {'boldmessage': "This is the about page!"}
    return render(request, 'rango/about.html', context_dict)

def category(request, category_name_slug):
    context_dict = {'category_name_slug':category_name_slug}

    try:
        #can we find a category name slug with the given name?
        #If we can't, the get() method raises a DoesNotExist exception
        #So the .get() method returns one model instance or raises an exception.
        category = Category.objects.get(slug=category_name_slug)
        context_dict['category_name']=category.name
        context_dict['category_name_slug']=category_name_slug


        #Get all associated pages
        #note that filter returns >=1 model instances
        pages = Page.objects.filter(category=category)

        #Adds results list to the template context under name pages.
        context_dict['pages'] = pages
        #Also add category object from the database to the cont dict
        #this is to verify it exists
        context_dict['category'] = category
        
    except Category.DoesNotExist:
        #Don't do anything, the template displays the "no category" message
        pass
        
    return render(request, 'rango/category.html', context_dict)

def add_category(request):
    # A HTTP POST?
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        # Have we been provided with a valid form?
        if form.is_valid():
            # Save the new category to the database.
            form.save(commit=True)

            # Now call the index() view.
            # The user will be shown the homepage.
            return index(request)
        else:
            # The supplied form contained errors - just print them to the terminal.
            print form.errors
    else:
        # If the request was not a POST, display the form to enter details.
        form = CategoryForm()

    # Bad form (or form details), no form supplied...
    # Render the form with error messages (if any).
    return render(request, 'rango/add_category.html', {'form': form})

def add_page(request, category_name_slug):

    # need some category to exist for this page
    try:
        cat = Category.objects.get(slug=category_name_slug)
    except Category.DoesNotExist:
        cat = None

    #an http post? if so need to process it
    #if not, we're going to be filling out a blank form
    if request.method == 'POST':
        form = PageForm(request.POST)
        #check to see if form was filled out properly
        #if so, send to db and return to index
        #if not, print the errors
        if form.is_valid():
            if cat:
                page = form.save(commit=False)
                page.category = cat
                page.views = 0
                page.save()
                return category(request, category_name_slug)
        else:
            print form.errors
    #if it wasn't a post request, give the blank form
    else:
        form = PageForm()
    context_dict = {'form':form, 'category':cat, 'category_name_slug':category_name_slug}
    return render(request, 'rango/add_page.html', context_dict)

def register(request):

    # A boolean value for telling whethert the reg. was successful
    # Set to false initially. Change to true upon completion.
    registered = False

    #If http post, we need to process the form
    if request.method == 'POST':
        # attempt to grab info from raw form info
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data = request.POST)

        #if forms are valid...
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user

            #did they supply picture?
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']
                
            #now we save the user profile instance
            profile.save()

            #update the variable to indicate success
            registered = True
        
        else:
            print user_form.errors, profile_form.errors

    else:
        user_form = UserForm()
        profile_form =  UserProfileForm()
    return render(request, 'rango/register.html',
                  {'user_form':user_form, 'profile_form':profile_form, 'registered':registered})

def user_login(request):
    
    #if the request is an http request, pull relevant info
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        #try to validate given userinfo
        user = authenticate(username=username, password=password)
        # if we have a user object the details are correct
        # otherwise we will get None
        if user:
            # is the account active (e.g. not disabled)
            if user.is_active:
                #now we can try to log them in
                login(request, user)
                return HttpResponseRedirect('/rango/')
            else:
                #an inactive user
                return HttpResponse("Your Rango account is disabled")
        else:
            #bad login info was given
            print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponse("Invalid login details supplied.")

    else:
        #else this user hasn't attempted to login yet, i.e. the 
        #request method was a "GET"
        return render(request, 'rango/login.html', {})

@login_required
def user_logout(request):
    #makes use of imported logout. since decorator
    #will insist that the user is logged in, this makes sense.
    logout(request)
    return HttpResponseRedirect('/rango/')


@login_required
def restricted(request):
    return HttpResponse("Since you're not logged in, you can see this text")

