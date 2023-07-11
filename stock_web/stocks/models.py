from django.db import models


# Create your models here.
class StockInfo(models.Model):
    date = models.DateField()
    stock_id = models.CharField(max_length=50)
    prediction1 = models.FloatField()
    prediction2 = models.FloatField()
    voting = models.FloatField()
    price = models.FloatField()

    def __str__(self):
        return f'{self.date} - {self.stock_id}'


class ACCStocks(models.Model):
    stock_id = models.CharField(max_length=50)
    model_name = models.CharField(max_length=50)
    count = models.IntegerField()
    high = models.IntegerField()
    low = models.IntegerField()
    pred_high = models.IntegerField()
    pred_low = models.IntegerField()
    pred_high_correct = models.IntegerField()
    pred_low_correct = models.IntegerField()
    rmse = models.FloatField()

    def __str__(self):
        return self.stock_id


class StocksType(models.Model):
    stock_id = models.CharField(max_length=50)
    stock_type = models.CharField(max_length=50)
    stock_name = models.CharField(max_length=50)
    def __str__(self):
        return self.stock_id


class StocksHistory(models.Model):
    stock_id = models.CharField(max_length=50)
    buy_date = models.DateField()
    buy_price = models.DecimalField(max_digits=10, decimal_places=2)
    target = models.DecimalField(max_digits=10, decimal_places=2)
    range = models.DecimalField(max_digits=10, decimal_places=2)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sell_date = models.DateField(null=True, blank=True)
    sell_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def calculate_percentage(self):
        if self.sell_price is not None:
            return round((self.sell_price - self.buy_price) / self.buy_price * 100, 2)
        elif self.current_price is not None:
            return round((self.current_price - self.buy_price) / self.buy_price * 100, 2)
        else:
            return None

    def get_stock_name(self):
        try:
            stock = StocksType.objects.get(stock_id=self.stock_id)
            return stock.stock_name
        except StocksType.DoesNotExist:
            return "Unknown"

    def __str__(self):
        percentage = self.calculate_percentage()
        return f"{percentage}%"

class StrategyMode(models.Model):
    mode_name = models.CharField(max_length=50)
    history = models.ManyToManyField(StocksHistory)

    @property
    def earn(self):
        total_earnings = 0
        count = 0
        for history_entry in self.history.all():
            if history_entry.sell_price is not None:
                buy_price = history_entry.buy_price
                sell_price = history_entry.sell_price
                earnings = ((sell_price - buy_price) / buy_price) * 100
                total_earnings += earnings
                count += 1
            else:
                buy_price = history_entry.buy_price
                sell_price = history_entry.current_price
                earnings = ((sell_price - buy_price) / buy_price) * 100
                total_earnings += earnings
                count += 1
        if count == 0:
            return 0, 0
        avg_earnings = total_earnings / count
        return round(total_earnings, 2), round(avg_earnings, 2)

    def get_exist(self):
        return self.history.filter(sell_price__isnull=True)

    def get_sold(self):
        return self.history.filter(sell_price__isnull=False)

    def get_history(self, stock_id):
        return self.history.filter(stock_id=stock_id, sell_price__isnull=True)


class File(models.Model):
    file_name = models.CharField(max_length=50)
    file = models.FileField(upload_to='files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name
