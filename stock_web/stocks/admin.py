from django.contrib import admin
from .models import StockInfo, ACCStocks, StocksType, StrategyMode, StocksHistory, File

# Register your models here.
admin.site.register(StockInfo)
admin.site.register(ACCStocks)
admin.site.register(StocksType)
admin.site.register(StrategyMode)
admin.site.register(StocksHistory)
admin.site.register(File)