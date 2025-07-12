from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import AbstractUser


# from shortuuid.dango_fields import shortUUIDField

# Create your models here.
GENDER = (
    ('Male',"Male"),
    ('Female',"Female"),
)
IDENTITY_TYPE = (
    ("National Identity Card Number","National Identity Card Number"),
    ("Driver's License","Driver's License"),
    ("Passport Number","Passport Number"),
) 


def user_directory_path(instance,filename):
    ext = filename.split(".")[-1]
    filename = "%s.%s" % (instance.user.id,filename)
    return "user_{0}/{1}".format(instance.user.id,filename)

class User(AbstractUser):
    full_name = models.CharField(max_length=225,null=True,blank=True)
    username = models.CharField(max_length=225, unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=255,null=True, blank=True)
    gender = models.CharField(max_length=255,choices=GENDER,default='male')

    otp = models.CharField(max_length=20,null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username
    


class Profile(models.Model):
    # pid = models.UUIDField(length=7, max_length=15,alphabets="abcdefghijklmnopqrstuvwxyz12345",unique=True)
    image = models.FileField(upload_to=user_directory_path,default='default.jpg',blank=True, null=True)
    user = models.OneToOneField(User, blank=True,on_delete=models.CASCADE)
    full_name = models.CharField(max_length=225,null=True,blank=True)
    phone = models.CharField(max_length=255,null=True, blank=True)
    gender = models.CharField(max_length=255,choices=GENDER,default='male')
    
    country = models.CharField(max_length=255,null=True, blank=True)
    identity_type = models.CharField(max_length=255,choices=IDENTITY_TYPE,null=True, blank=True)
    id_image = models.FileField(upload_to=user_directory_path,default='default.jpg',blank=True, null=True)

    
    Facebook = models.URLField(null=True, blank=True)
    Twitter = models.URLField(null=True, blank=True)
    Instagram = models.URLField(null=True, blank=True)

    wallet = models.DecimalField(max_digits=12, decimal_places=2,default=0.00)
    verified = models.BooleanField(default=False)
    date = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        if self.full_name:
            return self.full_name
        else:
            return self.user.username
        



# to create a user profile once user is created
def create_user_profile(sender,instance,created,**kwargs):
    if created:
        Profile.objects.create(user=instance)


# to save the creted user profile
def save_user_profile(sender,instance,**kwargs):
    instance.profile.save()


post_save.connect(create_user_profile, sender=User)
post_save.connect(save_user_profile, sender=User)