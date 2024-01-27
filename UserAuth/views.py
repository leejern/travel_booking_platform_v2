from django.shortcuts import render,redirect
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages

from .models import User,Profile
from .forms import UserRegisterForm
# Create your views here.
def registerView(request):
    form = UserRegisterForm(request.POST or None)
    if form.is_valid():
        form.save()
        full_name = form.cleaned_data['full_name']
        phone = form.cleaned_data['phone']
        email = form.cleaned_data['email']
        password = form.cleaned_data['password1']


        # to login the new user created
        user = authenticate(email=email, password=password)
        login(request,user)
        messages.success(request, f"Hey {full_name}, your account has been created successfully")

        # to create a profile for the new user
        profile = Profile.objects.get(user=request.user)
        profile.full_name = full_name
        profile.phone = phone
        profile.save()

        return redirect('Hotel:home')
    context = {
        'form': form,
    }
    return render(request, 'userauths/sign-up.html', context)


def loginViewTemp(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user_query = User.objects.get(email=email)
            user_auth = authenticate(request, email=email, password=password)
            if user_query:
                login(request,user_auth)
                messages.success(request,"login successful")
                #  to redirect the user to the page they were b4 login successful
                next_url = request.GET.get('next',"Hotel:home")
                return redirect(next_url)  
            else:
                messages.error(request,"invalid login")
        except:
            messages.error(request,"No account found for this email address")
            return redirect("UserAuth:sign-in")
            

    return render(request, 'userauths/sign-in.html',)
    

def logoutView(request):
    logout(request)
    messages.success(request, "You have been logged out")
    return redirect("UserAuth:sign-in")