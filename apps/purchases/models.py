from django.db import models

class Purchase(models.Model):
    invoice_number = models.CharField(max_length = 100, verbose_name = 'Número de factura')
    
    purchase_date = models.DateField(verbose_name = 'Fecha')
    product = models.CharField(max_length = 255, verbose_name = 'Productos')
    supplier = models.CharField(max_length = 255, verbose_name = 'Proveedor')
    amount = models.DecimalField(max_digits = 12, decimal_places = 2, verbose_name = 'Monto')
    created_at = models.DateTimeField(auto_now_add = True)
    
    class Meta:
        ordering = ['-purchase_date']
        
    def __str__(self):
        return f"{self.invoice_number} - {self.product}"
    
