from django.db import models
from django.utils import timezone
from driver.models import DriverProfile
from admin_panel.models import AdminProfile


class Warehouse(models.Model):
    """
    Model to store warehouse information
    """
    name = models.CharField(max_length=100)
    address = models.TextField()
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    location_lat = models.FloatField()
    location_lng = models.FloatField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.city}"


class Vehicle(models.Model):
    """
    Model to store vehicle information
    """
    VEHICLE_TYPES = [
        ('truck', 'Truck'),
        ('mini_truck', 'Mini Truck'),
        ('container', 'Container'),
        ('tanker', 'Tanker'),
        ('other', 'Other'),
    ]
    
    registration_number = models.CharField(max_length=20, unique=True)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.PositiveIntegerField()
    capacity = models.CharField(max_length=50)
    current_driver = models.ForeignKey(
        DriverProfile, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='current_vehicle'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.registration_number} - {self.vehicle_type}"


class Ride(models.Model):
    """
    Model to store ride information (full journey from source to destination)
    """
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    source_warehouse = models.ForeignKey(
        Warehouse, 
        on_delete=models.PROTECT, 
        related_name='source_rides'
    )
    destination_warehouse = models.ForeignKey(
        Warehouse, 
        on_delete=models.PROTECT, 
        related_name='destination_rides'
    )
    planned_start_time = models.DateTimeField()
    planned_end_time = models.DateTimeField()
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='planned'
    )
    total_distance = models.FloatField(help_text="Distance in kilometers")
    created_by = models.ForeignKey(
        AdminProfile, 
        on_delete=models.PROTECT, 
        related_name='created_rides'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return (
            f"{self.title} - {self.source_warehouse.city} to "
            f"{self.destination_warehouse.city}"
        )


class Trip(models.Model):
    """
    Model to store trip information (segments of a ride)
    """
    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('started', 'Started'),
        ('in_transit', 'In Transit'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    ride = models.ForeignKey(
        Ride, 
        on_delete=models.CASCADE, 
        related_name='trips'
    )
    driver = models.ForeignKey(
        DriverProfile, 
        on_delete=models.PROTECT, 
        related_name='trips'
    )
    vehicle = models.ForeignKey(
        Vehicle, 
        on_delete=models.PROTECT, 
        related_name='trips'
    )
    source_warehouse = models.ForeignKey(
        Warehouse, 
        on_delete=models.PROTECT, 
        related_name='source_trips'
    )
    destination_warehouse = models.ForeignKey(
        Warehouse, 
        on_delete=models.PROTECT, 
        related_name='destination_trips'
    )
    planned_start_time = models.DateTimeField()
    planned_end_time = models.DateTimeField()
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='assigned'
    )
    distance = models.FloatField(help_text="Distance in kilometers")
    buffer_hours = models.PositiveIntegerField(
        default=1, 
        help_text="Buffer hours allowed"
    )
    rest_hours = models.PositiveIntegerField(
        default=8, 
        help_text="Allowed rest hours"
    )
    remaining_rest_hours = models.PositiveIntegerField(default=8)
    created_by = models.ForeignKey(
        AdminProfile, 
        on_delete=models.PROTECT, 
        related_name='created_trips'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return (
            f"{self.ride.title} - {self.source_warehouse.city} to "
            f"{self.destination_warehouse.city}"
        )
    
    def start_trip(self):
        self.status = 'started'
        self.actual_start_time = timezone.now()
        self.save()
    
    def complete_trip(self):
        self.status = 'completed'
        self.actual_end_time = timezone.now()
        self.save()
    
    def cancel_trip(self):
        self.status = 'cancelled'
        self.save()


class LocationUpdate(models.Model):
    """
    Model to store real-time location updates of trips
    """
    trip = models.ForeignKey(
        Trip, 
        on_delete=models.CASCADE, 
        related_name='location_updates'
    )
    driver = models.ForeignKey(
        DriverProfile, 
        on_delete=models.CASCADE, 
        related_name='location_updates'
    )
    latitude = models.FloatField()
    longitude = models.FloatField()
    speed = models.FloatField(null=True, blank=True)
    heading = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.driver.user.username} - {self.timestamp}"
    
    class Meta:
        ordering = ['-timestamp']


class DriverLoyaltyTransaction(models.Model):
    """
    Model to track driver loyalty points transactions
    """
    TRANSACTION_TYPES = [
        ('earned', 'Points Earned'),
        ('redeemed', 'Points Redeemed'),
        ('expired', 'Points Expired'),
        ('bonus', 'Bonus Points'),
    ]
    
    driver = models.ForeignKey(
        DriverProfile, 
        on_delete=models.CASCADE, 
        related_name='loyalty_transactions'
    )
    trip = models.ForeignKey(
        Trip, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='loyalty_transactions'
    )
    points = models.IntegerField()
    transaction_type = models.CharField(
        max_length=20, 
        choices=TRANSACTION_TYPES
    )
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        AdminProfile, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='loyalty_transactions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return (
            f"{self.driver.user.username} - {self.transaction_type} - "
            f"{self.points} pts"
        )
    
    def save(self, *args, **kwargs):
        """Update driver's loyalty points on save"""
        super().save(*args, **kwargs)
        
        # Update driver's total loyalty points
        driver = self.driver
        driver.loyalty_points += self.points
        driver.save()
