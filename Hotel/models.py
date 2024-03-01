import string 
import random

from django.db import models
from django.utils.text import slugify
from django.utils.html import mark_safe
from django_ckeditor_5.fields import CKEditor5Field
from shortuuid.django_fields import ShortUUIDField
from taggit.managers import TaggableManager

from UserAuth.models import User

# Create your models here.
Hotel_status=(
    ("Draft","Draft"),
    ("Disabled","Disabled"),
    ("Rejected","Rejected"),
    ("In Review","In Review"),
    ("Live","Live"),
)
Icon_types=(
    ("Bootstrap icons","Bootstrap icons"),
    ("fontawsome icons","fontawsome icons"),
)

Payment_status= (
    ("Paid","Paid"),
    ("Pending","Pending"),
    ("Processing","Processing"),
    ("cancelled","cancelled"),
    ("Initiated","Initiated"),
    ("Refunded","Refunded"),
    ("Unpaid","Unpaid"),
    ("Expired","Expired"),
)

def generate_random_string(length=8):
    """Generate a random string of uppercase letters and digits excluding certain characters."""
    exclude_chars = ['0', 'O','I']
    valid_chars = [char for char in string.ascii_uppercase + string.digits if char not in exclude_chars]
    return ''.join(random.choices(valid_chars, k=length))


class Hotel(models.Model):
    user= models.ForeignKey(User, related_name="Hotel_users",on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = CKEditor5Field(null=True, blank=True,config_name='extends')
    image = models.FileField(upload_to="hotel_gallery")
    address = models.CharField(max_length=255)
    email = models.EmailField( max_length=254)
    mobile = models.CharField(max_length=255)
    status = models.CharField(max_length=255, choices=Hotel_status,default="Live")

    tags = TaggableManager(blank=True)
    views = models.IntegerField(default=0)
    featured = models.BooleanField(default=False)
    slug = models.SlugField(unique=True)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        slug_query = Hotel.objects.filter(slug=self.slug)
        if slug_query:
            uniqueid = "".join(random.choice(string.ascii_letters) for _ in range(2))
            self.slug = slugify(self.name)+'-'+uniqueid.lower()

        if self.slug =="" or self.slug == None:
            uniqueid = "".join(random.choice(string.ascii_letters) for _ in range(4))
            self.slug = slugify(self.name)+'-'+uniqueid.lower()
            
        super(Hotel,self).save(*args, **kwargs)

    def thumbnail(self):
        return mark_safe("<img src='%s' alt='' width='50' height='50' border-radius='6px'style='object-fit' />" % (self.image.url))
    
    


class HotelGallery(models.Model):
    hotel = models.ForeignKey(Hotel,on_delete=models.CASCADE,related_name="hotel_images")
    image = models.FileField(upload_to="hotel_galley")

    def __str__(self):
        return str(self.hotel.name)
    
    class Meta:
        verbose_name_plural = "Hotel Gallery"


class HotelFeatures(models.Model):
    hotel = models.ForeignKey(Hotel,on_delete=models.CASCADE,related_name="hotel_features")
    icon_type = models.CharField(max_length=100, blank=True,null=True,choices=Icon_types)
    icon = models.CharField(max_length=100, blank=True,null=True)
    name = models.CharField(max_length=100, blank=True,null=True)

    def __str__(self):
        return str(self.name)
    
    class Meta:
        verbose_name_plural = "Hotel Features"


class HotelFaqs(models.Model):
    Hotel = models.ForeignKey(Hotel,on_delete=models.CASCADE)
    question = models.CharField(max_length=1000)
    answer = models.CharField(max_length=1000)
    date = models.DateField(auto_now_add=True)


    def __str__(self):
        return str(self.question)
    
    class Meta:
        verbose_name_plural = "Hotel FAQs"



class RoomType(models.Model):
    hotel = models.ForeignKey(Hotel,related_name="roomtypes", on_delete=models.CASCADE)
    type = models.CharField(max_length=20)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    number_of_beds = models.PositiveIntegerField(default=1)
    image = models.FileField(upload_to="hotel_gallery/roomType",blank=True,null=True)
    slug = models.SlugField(unique=True)


    def __str__(self):
        return f"{self.type} - {self.hotel.name} - {self.price}"
    
    class Meta:
        verbose_name_plural = "Room Type"

    def rooms_count(self):
        Room.objects.filter(roomtype=self).count()

    def save(self, *args, **kwargs):
        if self.slug =="" or self.slug == None:
            uniqueid = "".join(random.choice(string.ascii_letters) for _ in range(4))
            self.slug = slugify(self.name)+'-'+uniqueid.lower()
            
        super(RoomType,self).save(*args, **kwargs)


class Room(models.Model):
    hotel = models.ForeignKey(Hotel, related_name='rooms',on_delete=models.CASCADE)
    room_type = models.ForeignKey(RoomType, related_name='room_types',on_delete=models.CASCADE)
    room_number = models.CharField(max_length=30)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.room_number} - {self.hotel.name} "
    
    class Meta:
        verbose_name_plural = "Rooms"

    def price(self):
        return self.room_type.price
    
    def number_of_beds(self):
        return self.room_type.number_of_beds
    
class Booking(models.Model):   
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    payment_status = models.CharField(max_length=100,choices=Payment_status)

    fullname = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    phone = models.CharField(max_length=100,null=True, blank=True)

    hotel = models.ForeignKey(Hotel, on_delete=models.SET_NULL,null=True, blank=True)
    room_type = models.ForeignKey(RoomType, on_delete=models.SET_NULL,null=True, blank=True)
    room = models.ManyToManyField(Room)
    before_discount = models.DecimalField(max_digits=12,decimal_places=2,default=0.00)
    total = models.DecimalField(max_digits=12,decimal_places=2,default=0.00)
    saved = models.DecimalField(max_digits=12,decimal_places=2,default=0.00)
    coupons = models.ManyToManyField("Hotel.Coupon",blank=True)
    checkin_date = models.DateField()
    checkout_date = models.DateField()

    total_days = models.PositiveIntegerField(default=1)
    num_adults = models.PositiveIntegerField(default=1)
    num_children = models.PositiveIntegerField(default=0)

    check_in = models.BooleanField(default=False)
    check_out = models.BooleanField(default=False)
     
    is_availabe = models.BooleanField(default=False)

    check_in_tracker = models.BooleanField(default=False)
    check_out_tracker = models.BooleanField(default=False)

    booking_id = models.CharField(max_length=10, unique=True, editable=True, default=generate_random_string)
    success_id = ShortUUIDField(length=10,max_length=10,alphabet='abcdefghijklmnopqrstuvwxyz',null=True,blank=True)
    stripe_payment_intent = models.CharField(max_length=100,blank=True,null=True)
    payment_id = models.CharField(max_length=100,blank=True,null=True)

    def generate_random_string(length=8):
        """Generate a random string of uppercase letters and digits excluding certain characters."""
        exclude_chars = ['0', 'o', '1', 'i']
        valid_chars = [char for char in string.ascii_uppercase + string.digits if char not in exclude_chars]
        return ''.join(random.choices(valid_chars, k=length))


    def save(self, *args, **kwargs):
        # Generate the booking ID if it doesn't exist
        if not self.booking_id:
            self.booking_id = generate_random_string(8)

        # Ensure the generated booking_id is unique
        while Booking.objects.filter(booking_id=self.booking_id).exists():
            self.booking_id = generate_random_string(8)

        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.booking_id)
    

    def rooms(self):
        return self.room.all.count()



class GuestActivityLog(models.Model):
    booking= models.ForeignKey(Booking,on_delete=models.CASCADE)
    guest_out = models.DateTimeField()
    guest_in = models.DateTimeField()
    description = models.TextField(blank=True,null=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.booking.fullname
    

class StaffOnDuty(models.Model):
    Booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    staff_id = models.CharField(max_length=100,blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.staff_id
    
    class Meta:
        verbose_name_plural = "Staff on Duties"


class Coupon(models.Model):
    code=models.CharField( max_length=50)
    type=models.CharField( max_length=50,default='Percentage')
    discount = models.IntegerField(default=1)
    redemptions = models.IntegerField(default=0)
    date = models.DateField(auto_now_add=True)
    active = models.BooleanField(default=True)
    valid_from = models.DateField()
    valid_to = models.DateField()
    cid = ShortUUIDField(unique=True,length=10,max_length=10)

    def __str__(self):
        return f"{self.code}"