from django.db import models
from django.db.models import UniqueConstraint


# Create your models here.
class StockInfo(models.Model):
    date = models.DateField(db_index=True)
    stock_id = models.CharField(max_length=50, db_index=True)
    prediction1 = models.DecimalField(max_digits=10, decimal_places=2)
    prediction2 = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pred1_future = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pred2_future = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f'{self.stock_id}'

    class Meta:
        constraints = [
            UniqueConstraint(fields=['date', 'stock_id'], name='unique_stock_per_date')
        ]

    def get_pred1_percentage(self):
        if self.price:
            return round(((self.prediction1 - self.price) / self.price) * 100, 2)
        else:
            return None

    def get_pred2_percentage(self):
        if self.price:
            return round(((self.prediction2 - self.price) / self.price) * 100, 2)
        else:
            return None


class TypesInfo(models.Model):
    date = models.DateField()
    stock_id = models.CharField(max_length=50)
    prediction1 = models.DecimalField(max_digits=10, decimal_places=2)
    prediction2 = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pred1_future = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pred2_future = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f'{self.stock_id}'


class ACCStocks(models.Model):
    stock_id = models.CharField(max_length=50, db_index=True)
    model_name = models.CharField(max_length=50)
    count = models.IntegerField()
    high = models.IntegerField()
    wp = models.DecimalField(max_digits=10, decimal_places=0)
    low = models.IntegerField()
    pred_high = models.IntegerField()
    pwp = models.DecimalField(max_digits=10, decimal_places=0)
    pred_low = models.IntegerField()
    pred_high_correct = models.IntegerField()
    pred_low_correct = models.IntegerField()
    rmse = models.DecimalField(max_digits=10, decimal_places=2)
    percentage = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.stock_id

    def get_stock_name(self):
        stock = StocksType.objects.get(stock_id=self.stock_id)
        return stock.stock_name

    def get_close(self):
        stock = StockInfo.objects.filter(stock_id=self.stock_id).order_by('-date')[1]
        return stock.price

    def get_pred(self):
        stock = StockInfo.objects.filter(stock_id=self.stock_id).order_by('-date')[1]
        if self.model_name == 'pred5':
            pred = stock.prediction1
        else:
            pred = stock.prediction2
        return pred

    def get_lp(self):
        lp = round(self.low / self.count*100)
        return lp

    def get_plp(self):
        plp = round(self.pred_low_correct / self.pred_low*100)
        return plp


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

    rmse = models.DecimalField(max_digits=10, decimal_places=2)
    model_name = models.CharField(max_length=50)
    percentage = models.DecimalField(max_digits=10, decimal_places=2)
    pred_high = models.IntegerField()
    pwp = models.DecimalField(max_digits=10, decimal_places=0)
    wp = models.DecimalField(max_digits=10, decimal_places=0)

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
        return self.history.filter(sell_price__isnull=True).order_by('-buy_date')

    def get_sold(self):
        return self.history.filter(sell_price__isnull=False).order_by('-buy_date')

    def get_history(self, stock_id):
        return self.history.filter(stock_id=stock_id, sell_price__isnull=True)


class File(models.Model):
    file_name = models.CharField(max_length=50)
    file = models.FileField(upload_to='files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name
