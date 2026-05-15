from django.shortcuts import render, redirect
from django.db.models import Q
from .models import Purchase
from .forms import PurchaseForm

def purchase_list(request):
    
    purchases = Purchase.objects.all()
    query = request.GET.get('q')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    #búsqueda
    if query:
        purchases = purchases.filter(
            Q(invoice_numer__icontains = query) |
            Q(product__icontains = query) |
            Q(supplier__icontains = query)
        )
        
    #filtro DESDE - HASTA
    if start_date and end_date:
        purchases = purchases.filter(
            purchase_date__range = [start_date, end_date]
        )
        
    context = {
        'purchases': purchases
    }

    return render(
        request, 'purchases/purchase_list.html', context
    )
    
def purchase_create(request):
    form = PurchaseForm(request.POST or None)
    
    if form.is_valid():
        form.save()
        return redirect('purchase_list')

    context = {
        'form': form
    }

    return render(
        request, 'purchases/purchase_list.html', context
    )
    


