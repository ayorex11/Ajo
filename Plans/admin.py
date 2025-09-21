from django.contrib import admin
from .models import SavingsPlan, Transaction

admin.site.register(SavingsPlan)
admin.site.register(Transaction)