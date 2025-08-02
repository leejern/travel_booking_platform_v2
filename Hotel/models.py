import string 
import random
from decimal import Decimal
from datetime import date

from django.db import models
from django.utils.text import slugify
from django.utils.html import mark_safe
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django_ckeditor_5.fields import CKEditor5Field
from shortuuid.django_fields import ShortUUIDField
from taggit.managers import TaggableManager
from smart_selects.db_fields import ChainedForeignKey

from UserAuth.models import User

# Create your models here.
HOTEL_STATUS = (
    ("Draft", "Draft"),
    ("Disabled", "Disabled"),
    ("Rejected", "Rejected"),
    ("In Review", "In Review"),
    ("Live", "Live"),
)

ICON_TYPES = (
    ("Bootstrap icons", "Bootstrap icons"),
    ("fontawesome icons", "Font Awesome icons"),
)

PAYMENT_STATUS = (
    ("Paid", "Paid"),
    ("Pending", "Pending"),
    ("Processing", "Processing"),
    ("Cancelled", "Cancelled"),
    ("Initiated", "Initiated"),
    ("Refunded", "Refunded"),
    ("Unpaid", "Unpaid"),
    ("Expired", "Expired"),
)

NOTIFICATION_TYPE = (
    ("Booking Confirmed", "Booking Confirmed"),
    ("Booking Cancelled", "Booking Cancelled"),
    ("Payment Received", "Payment Received"),
    ("Check-in Reminder", "Check-in Reminder"),
)

RATING = (
    (1, "⭐"),
    (2, "⭐⭐"),
    (3, "⭐⭐⭐"),
    (4, "⭐⭐⭐⭐"),
    (5, "⭐⭐⭐⭐⭐"),
)

def generate_random_string(length=8):
    """Generate a random string of uppercase letters and digits excluding confusing characters."""
    exclude_chars = ['0', 'O', 'I', '1']
    valid_chars = [char for char in string.ascii_uppercase + string.digits if char not in exclude_chars]
    return ''.join(random.choices(valid_chars, k=length))


class Hotel(models.Model):
    user = models.ForeignKey(User, related_name="hotels", on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=255, db_index=True)
    description = CKEditor5Field(null=True, blank=True, config_name='extends')
    image = models.FileField(upload_to="hotel_gallery")
    address = models.CharField(max_length=255)
    email = models.EmailField(max_length=254)
    mobile = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=HOTEL_STATUS, default="Live", db_index=True)
    
    # Location fields for better search
    city = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    
    tags = TaggableManager(blank=True)
    views = models.IntegerField(default=0)
    featured = models.BooleanField(default=False, db_index=True)
    slug = models.SlugField(unique=True, max_length=300)
    date = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-featured', '-date']
        indexes = [
            models.Index(fields=['status', 'featured']),
            models.Index(fields=['city', 'status']),
        ]

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            
            while Hotel.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
            
        super().save(*args, **kwargs)

    def thumbnail(self):
        if self.image:
            return mark_safe(
                f"<img src='{self.image.url}' alt='{self.name}' "
                f"width='50' height='50' style='object-fit: cover; border-radius: 6px;' />"
            )
        return "No Image"
    
    def average_rating(self):
        """Calculate average rating from reviews"""
        from django.db.models import Avg
        return self.reviews.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
    
    def available_rooms_count(self, checkin_date=None, checkout_date=None):
        """Get count of available rooms for given dates"""
        if not checkin_date or not checkout_date:
            return self.rooms.filter(is_available=True).count()
        
        # Complex query to check room availability
        booked_rooms = Booking.objects.filter(
            hotel=self,
            checkin_date__lt=checkout_date,
            checkout_date__gt=checkin_date,
            payment_status__in=['Paid', 'Processing', 'Initiated']
        ).values_list('room', flat=True)
        
        return self.rooms.exclude(id__in=booked_rooms).filter(is_available=True).count()




class HotelGallery(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="gallery_images")
    image = models.FileField(upload_to="hotel_gallery")
    caption = models.CharField(max_length=200, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "Hotel Gallery"
        ordering = ['-is_primary', 'order']

    def __str__(self):
        return f"{self.hotel.name} - Image {self.id}"


class HotelFeatures(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="features")
    icon_type = models.CharField(max_length=100, choices=ICON_TYPES, blank=True, null=True)
    icon = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Hotel Features"
        unique_together = ['hotel', 'name']

    def __str__(self):
        return f"{self.hotel.name} - {self.name}"


class HotelFaqs(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="faqs")
    question = models.CharField(max_length=1000)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Hotel FAQs"
        ordering = ['order', 'date']

    def __str__(self):
        return f"{self.hotel.name} - {self.question[:50]}..."



class RoomType(models.Model):
    hotel = models.ForeignKey(Hotel, related_name="room_types", on_delete=models.CASCADE)
    type = models.CharField(max_length=50)
    price = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    number_of_beds = models.PositiveIntegerField(default=1)
    max_occupancy = models.PositiveIntegerField(default=2)
    image = models.FileField(upload_to="hotel_gallery/room_types", blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    amenities = models.TextField(blank=True, null=True, help_text="Comma-separated amenities")
    slug = models.SlugField(unique=True, max_length=300)

    class Meta:
        verbose_name_plural = "Room Types"
        unique_together = ['hotel', 'type']

    def __str__(self):
        return f"{self.type} - {self.hotel.name} - ${self.price}"
    
    def rooms_count(self):
        return self.room_types.count()
    
    def available_rooms_count(self, checkin_date=None, checkout_date=None):
        """Get count of available rooms of this type for given dates"""
        rooms = self.room_types.filter(is_available=True)
        
        if checkin_date and checkout_date:
            booked_rooms = Booking.objects.filter(
                room_type=self,
                checkin_date__lt=checkout_date,
                checkout_date__gt=checkin_date,
                payment_status__in=['Paid', 'Processing', 'Initiated']
            ).values_list('room', flat=True)
            
            rooms = rooms.exclude(id__in=booked_rooms)
        
        return rooms.count()

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.hotel.name}-{self.type}")
            slug = base_slug
            counter = 1
            
            while RoomType.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
            
        super().save(*args, **kwargs)


class Room(models.Model):
    hotel = models.ForeignKey(Hotel, related_name='rooms', on_delete=models.CASCADE)
    room_type = ChainedForeignKey(
        RoomType,
        chained_field="hotel",
        chained_model_field="hotel",
        auto_choose=True,
        sort=True,
        related_name='rooms',
        on_delete=models.CASCADE
    )
    # room_type = models.ForeignKey(RoomType, related_name='room_types', on_delete=models.CASCADE)
    room_number = models.CharField(max_length=30)
    floor = models.PositiveIntegerField(blank=True, null=True)
    is_available = models.BooleanField(default=True)
    maintenance_mode = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Rooms"
        unique_together = ['hotel', 'room_number']

    def __str__(self):
        return f"Room {self.room_number} - {self.hotel.name}"
    
    def price(self):
        return self.room_type.price
    
    def number_of_beds(self):
        return self.room_type.number_of_beds
    
    def is_booked(self, checkin_date, checkout_date):
        """Check if room is booked for given dates"""
        return Booking.objects.filter(
            room=self,
            checkin_date__lt=checkout_date,
            checkout_date__gt=checkin_date,
            payment_status__in=['Paid', 'Processing', 'Initiated']
        ).exists()
    

class Booking(models.Model):
    # Booking identifiers
    booking_id = ShortUUIDField(
        length=10, 
        max_length=10, 
        alphabet='0123456789ABCDEFGHJKLMNPQRST',
        unique=True
    )
    success_id = ShortUUIDField(
        length=10, 
        max_length=10, 
        alphabet='abcdefghijklmnopqrstuvwxyz',
        blank=True, 
        null=True
    )
    
    # User information
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fullname = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Booking details
    hotel = models.ForeignKey(Hotel, on_delete=models.SET_NULL, null=True, blank=True)
    room_type = models.ForeignKey(RoomType, on_delete=models.SET_NULL, null=True, blank=True)
    room = models.ManyToManyField(Room)
    
    # Dates
    checkin_date = models.DateField()
    checkout_date = models.DateField()
    booking_date = models.DateTimeField(auto_now_add=True)
    
    # Guest information
    num_adults = models.PositiveIntegerField(default=1)
    num_children = models.PositiveIntegerField(default=0)
    total_days = models.PositiveIntegerField(default=1)
    
    # Pricing
    before_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    saved = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Payment
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default="Pending")
    stripe_payment_intent = models.CharField(max_length=100, blank=True, null=True)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Status tracking
    check_in = models.BooleanField(default=False)
    check_out = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    check_in_tracker = models.BooleanField(default=False)
    check_out_tracker = models.BooleanField(default=False)
    
    # Relationships
    coupons = models.ManyToManyField("Hotel.Coupon", blank=True)

    class Meta:
        ordering = ['-booking_date']
        indexes = [
            models.Index(fields=['booking_date', 'payment_status']),
            models.Index(fields=['checkin_date', 'checkout_date']),
            models.Index(fields=['user', 'payment_status']),
        ]

    def __str__(self):
        return f"Booking {self.booking_id}"

    def clean(self):
        if self.checkin_date and self.checkout_date:
            if self.checkout_date <= self.checkin_date:
                raise ValidationError("Checkout date must be after checkin date")
            
            if self.checkin_date < date.today():
                raise ValidationError("Checkin date cannot be in the past")

    def save(self, *args, **kwargs):
        if self.checkin_date and self.checkout_date:
            self.total_days = (self.checkout_date - self.checkin_date).days
        
        self.full_clean()
        super().save(*args, **kwargs)

    def rooms_count(self):
        return self.room.count()
    
    def can_cancel(self):
        """Check if booking can be cancelled"""
        return (
            self.payment_status not in ['Cancelled', 'Refunded'] and
            self.checkin_date > date.today() and
            not self.check_in
        )


class Review(models.Model):
    """Hotel review model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='reviews')
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, blank=True, null=True)
    rating = models.IntegerField(choices=RATING)
    title = models.CharField(max_length=200)
    comment = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        unique_together = ['user', 'hotel']
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.hotel.name} - {self.rating} stars"


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
    code = models.CharField(max_length=50, unique=True, db_index=True)
    type = models.CharField(max_length=20, default='Percentage')
    discount = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    minimum_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    maximum_discount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    redemptions = models.IntegerField(default=0)
    max_redemptions = models.IntegerField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    valid_from = models.DateField()
    valid_to = models.DateField()
    cid = ShortUUIDField(unique=True, length=10, max_length=10)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.code} - {self.discount}% off"
    
    def is_valid(self):
        """Check if coupon is currently valid"""
        today = date.today()
        return (
            self.active and
            self.valid_from <= today <= self.valid_to and
            (self.max_redemptions is None or self.redemptions < self.max_redemptions)
        )
    
    def clean(self):
        if self.valid_to <= self.valid_from:
            raise ValidationError("Valid to date must be after valid from date")
    

class Notifications(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, blank=True, null=True)
    type = models.CharField(max_length=50, choices=NOTIFICATION_TYPE)
    title = models.CharField(max_length=200)
    message = models.TextField()
    seen = models.BooleanField(default=False, db_index=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user', 'seen']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.type}"
    

class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    bid = ShortUUIDField(unique=True, length=10, max_length=20, alphabet="abcdefghijklmnopqrstuvwxyz")
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'hotel']
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} bookmarked {self.hotel.name}"