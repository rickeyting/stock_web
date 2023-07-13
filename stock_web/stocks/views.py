from django.shortcuts import render
import decimal
from datetime import datetime, date, timedelta
import pandas as pd
from .models import StockInfo, ACCStocks, StocksType, StrategyMode, StocksHistory, File, TypesInfo
from django.db.models import Max, Min, F
import math
import os
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
import time


class TimeCheck:
    def __init__(self):
        self.start_time = None

    def start(self):
        self.start_time = time.time()

    def end(self):
        if self.start_time is None:
            print("Please start the timer first.")
        else:
            end_time = time.time()
            execution_time = end_time - self.start_time
            print(f"Execution time: {execution_time} seconds")


# Create your views here.
def update_mode(mode_name, current_date):
    mode, created = StrategyMode.objects.get_or_create(mode_name=mode_name)
    if current_date > date(2023, 3, 1):
        exist_histories = mode.get_exist()
        for history in exist_histories:
            stock_info = StockInfo.objects.get(stock_id=history.stock_id, date=current_date)
            current_price = stock_info.price
            history.current_price = current_price
            target = history.target
            range = history.range
            stock_pred = stock_info.prediction2
            stock_close = stock_info.price
            stock_percentage = round(((stock_pred - stock_close) / stock_close) * 100, 2)
            if stock_percentage > 8 and stock_pred > target:
                range = round((stock_pred - stock_close) / 5)
                history.target = stock_pred
                history.target = range
            elif stock_percentage < -3:
                history.target -= range
            elif stock_percentage > 3:
                history.target += range
            if (stock_close > history.target) or (stock_close - history.buy_price)/history.buy_price < -0.1:
                history.sell_price = stock_close
                history.sell_date = current_date
            history.save()
        exist_histories = exist_histories.values_list('stock_id', flat=True)
        acc_stocks = ACCStocks.objects.filter(pred_high__gt=5, pwp__gt=80, model_name='pred10', percentage__gt=4, wp__lt=F('pwp')).order_by('-percentage')
        for stock_item in acc_stocks:
            stock_id = stock_item.stock_id
            if stock_id not in exist_histories:
                stock_info = StockInfo.objects.get(stock_id=stock_id, date=current_date)
                stock_close = stock_info.price
                stock_pred = stock_info.prediction2
                range = round((stock_pred - stock_close) / 5)
                stock_history = StocksHistory.objects.create(stock_id=stock_id, buy_price=stock_close, buy_date=current_date, current_price=stock_close, target=stock_pred, range=range)
                mode.history.add(stock_history)


def classification(request):
    try:
        latest_date = StockInfo.objects.latest('date').date
    except:
        latest_date = '2023-01-01'

    for model_name in ['pred5', 'pred10', 'voting']:
        pred_all = ACCStocks.objects.filter(model_name=model_name)
        count = 0
        high = 0
        low = 0
        pred_high = 0
        pred_low = 0
        pred_low_correct = 0
        pred_high_correct = 0
        rmse = 0
        for acc in pred_all:
            count += acc.count
            high += acc.high
            low += acc.low
            pred_high += acc.pred_high
            pred_low += acc.pred_low
            pred_high_correct += acc.pred_high_correct
            pred_low_correct += acc.pred_low_correct
            rmse += acc.rmse
        total = round(high/count*100, 2)
        pred = round(pred_high_correct/pred_high*100,2)
        print(count, high, low, pred_high, pred_low, pred_high_correct, pred_low_correct, rmse, total, pred)

    stock_types = StocksType.objects.all()
    stock_type_all = {}
    for stock in stock_types:
        try:
            stock_pred5 = ACCStocks.objects.filter(stock_id=stock.stock_id, model_name='pred5').first()
            stock_pred10 = ACCStocks.objects.filter(stock_id=stock.stock_id, model_name='pred10').first()
            stock_voting = ACCStocks.objects.filter(stock_id=stock.stock_id, model_name='voting').first()
            if stock.stock_type not in stock_type_all:
                stock_type_all[stock.stock_type] = {
                    'stock_pred5': {'all': stock_pred5.count, 'high': stock_pred5.high,
                                    'low': stock_pred5.low, 'pred_high': stock_pred5.pred_high,
                                    'pred_low': stock_pred5.pred_low, 'pred_high_correct': stock_pred5.pred_high_correct,
                                    'pred_low_correct': stock_pred5.pred_low_correct, 'rmse': stock_pred5.rmse},
                    'stock_pred10': {'all': stock_pred10.count, 'high': stock_pred10.high,
                                    'low': stock_pred10.low, 'pred_high': stock_pred10.pred_high,
                                    'pred_low': stock_pred10.pred_low, 'pred_high_correct': stock_pred10.pred_high_correct,
                                    'pred_low_correct': stock_pred10.pred_low_correct, 'rmse': stock_pred10.rmse},
                    'stock_voting': {'all': stock_voting.count, 'high': stock_voting.high,
                                    'low': stock_voting.low, 'pred_high': stock_voting.pred_high,
                                    'pred_low': stock_voting.pred_low, 'pred_high_correct': stock_voting.pred_high_correct,
                                    'pred_low_correct': stock_voting.pred_low_correct, 'rmse': stock_voting.rmse},
                }
            else:
                stock_type_all[stock.stock_type]['stock_pred5']['all'] += stock_pred5.count
                stock_type_all[stock.stock_type]['stock_pred5']['high'] += stock_pred5.high
                stock_type_all[stock.stock_type]['stock_pred5']['low'] += stock_pred5.low
                stock_type_all[stock.stock_type]['stock_pred5']['pred_high'] += stock_pred5.pred_high
                stock_type_all[stock.stock_type]['stock_pred5']['pred_low'] += stock_pred5.pred_low
                stock_type_all[stock.stock_type]['stock_pred5']['pred_high_correct'] += stock_pred5.pred_high_correct
                stock_type_all[stock.stock_type]['stock_pred5']['pred_low_correct'] += stock_pred5.pred_low_correct
                stock_type_all[stock.stock_type]['stock_pred5']['rmse'] += stock_pred5.rmse

                stock_type_all[stock.stock_type]['stock_pred10']['all'] += stock_pred10.count
                stock_type_all[stock.stock_type]['stock_pred10']['high'] += stock_pred10.high
                stock_type_all[stock.stock_type]['stock_pred10']['low'] += stock_pred10.low
                stock_type_all[stock.stock_type]['stock_pred10']['pred_high'] += stock_pred10.pred_high
                stock_type_all[stock.stock_type]['stock_pred10']['pred_low'] += stock_pred10.pred_low
                stock_type_all[stock.stock_type]['stock_pred10']['pred_high_correct'] += stock_pred10.pred_high_correct
                stock_type_all[stock.stock_type]['stock_pred10']['pred_low_correct'] += stock_pred10.pred_low_correct
                stock_type_all[stock.stock_type]['stock_pred10']['rmse'] += stock_pred10.rmse

                stock_type_all[stock.stock_type]['stock_voting']['all'] += stock_voting.count
                stock_type_all[stock.stock_type]['stock_voting']['high'] += stock_voting.high
                stock_type_all[stock.stock_type]['stock_voting']['low'] += stock_voting.low
                stock_type_all[stock.stock_type]['stock_voting']['pred_high'] += stock_voting.pred_high
                stock_type_all[stock.stock_type]['stock_voting']['pred_low'] += stock_voting.pred_low
                stock_type_all[stock.stock_type]['stock_voting']['pred_high_correct'] += stock_voting.pred_high_correct
                stock_type_all[stock.stock_type]['stock_voting']['pred_low_correct'] += stock_voting.pred_low_correct
                stock_type_all[stock.stock_type]['stock_voting']['rmse'] += stock_voting.rmse
        except:
            pass
    for stock in stock_type_all:
        for model_name in ['stock_pred5', 'stock_pred10', 'stock_voting']:
            if stock_type_all[stock][model_name]['pred_high'] == 0:
                stock_type_all[stock][model_name]['rmse'] = 0
            else:
                stock_type_all[stock][model_name]['rmse'] = round(stock_type_all[stock][model_name]['rmse'] / stock_type_all[stock][model_name]['pred_high'],2)

    if latest_date != '2023-01-01':
        latest_data = StockInfo.objects.filter(date=latest_date)
        for stock_data in latest_data:
            stock_close = stock_data.price
            stock_pred5 = stock_data.prediction1
            stock_pred10 = stock_data.prediction2
            stock_voting = stock_data.voting
            stock_type_object = StocksType.objects.get(stock_id=stock_data.stock_id)
            stock_type = stock_type_object.stock_type
            if 'stock_close' not in stock_type_all[stock_type]:
                stock_type_all[stock_type]['stock_close'] = stock_close
            else:
                stock_type_all[stock_type]['stock_close'] += stock_close
            if 'stock_close_pred5' not in stock_type_all[stock_type]:
                stock_type_all[stock_type]['stock_close_pred5'] = stock_pred5
            else:
                stock_type_all[stock_type]['stock_close_pred5'] += stock_pred5
            if 'stock_close_pred10' not in stock_type_all[stock_type]:
                stock_type_all[stock_type]['stock_close_pred10'] = stock_pred10
            else:
                stock_type_all[stock_type]['stock_close_pred10'] += stock_pred10
            if 'stock_close_voting' not in stock_type_all[stock_type]:
                stock_type_all[stock_type]['stock_close_voting'] = stock_voting
            else:
                stock_type_all[stock_type]['stock_close_voting'] += stock_voting
        for i in stock_type_all:
            stock_type_all[i]['stock_close_pred5'] = round(
                (stock_type_all[i]['stock_close_pred5'] - stock_type_all[i]['stock_close']) / stock_type_all[i]['stock_close'] * 100, 2)
            stock_type_all[i]['stock_close_pred10'] = round(
                (stock_type_all[i]['stock_close_pred10'] - stock_type_all[i]['stock_close']) / stock_type_all[i]['stock_close'] * 100, 2)
            stock_type_all[i]['stock_close_voting'] = round(
                (stock_type_all[i]['stock_close_voting'] - stock_type_all[i]['stock_close']) / stock_type_all[i]['stock_close'] * 100, 2)
    return render(request, 'classification.html',
                  {'latest_date': latest_date, 'stock_type_all': stock_type_all})


def strategy(request):
    try:
        latest_date = StockInfo.objects.latest('date').date - timedelta(days=1)
    except:
        latest_date = '2023-01-01'
    mode, created = StrategyMode.objects.get_or_create(mode_name='low_risk')
    mode_info = {}
    total_earnings, avg_earnings = mode.earn
    mode_info['total_earnings'] = total_earnings
    mode_info['avg_earnings'] = avg_earnings
    mode_info['exist'] = mode.get_exist()
    sold = mode.history.all()
    sold = sorted(sold, key=lambda item: item.sell_date if item.sell_date else datetime.min.date())
    mode_earn = {'data':{}}
    mode_count = {'data':{}, 'total': len(sold), 'chance': 0}
    mode_days = {'data':{}}
    last_date = None
    values = []
    for item in sold:
        if item.sell_price:
            sell_price = item.sell_price
        else:
            sell_price = item.current_price
        if item.sell_date:
            range = (item.sell_date - item.buy_date).days
            if range in mode_days['data']:
                mode_days['data'][range] += 1
            else:
                mode_days['data'][range] = 1
            if item.sell_date != last_date and last_date:
                mode_earn['data'][item.sell_date] = mode_earn['data'][last_date]
            if not item.sell_date in mode_earn['data']:
                mode_earn['data'][item.sell_date] = round(((sell_price - item.buy_price) / item.buy_price) * 100, 2)
            else:
                mode_earn['data'][item.sell_date] += round(((sell_price - item.buy_price) / item.buy_price) * 100, 2)
            last_date = item.sell_date
        percentage = ((sell_price - item.buy_price) / item.buy_price) * 100
        values.append(percentage)
        if percentage > 0:
            mode_count['chance'] += 1
        percentage = round(percentage, 0)
        if not percentage in mode_count['data']:
            mode_count['data'][percentage] = 1
        else:
            mode_count['data'][percentage] += 1
    mode_days['data'] = sorted(mode_days['data'].items(), key=lambda x: x[0])

    sorted_data = sorted(mode_count['data'].items(), key=lambda x: x[0])
    mode_count['data'] = sorted_data
    # Calculate the middle value
    sorted_values = sorted(values)

    # Calculate the median value
    n = len(sorted_values)
    if n % 2 == 0:
        median_index = n // 2
        median_value = (sorted_values[median_index - 1] + sorted_values[median_index]) / 2
    else:
        median_index = (n - 1) // 2
        median_value = sorted_values[median_index]

    # Calculate the mean value
    mean_value = round(sum(values) / len(values), 2)

    mode_count['mid'] = round(median_value, 2)
    mode_count['mean'] = mean_value
    mode_count['chance'] = round(mode_count['chance']/mode_count['total']*100, 2)

    mode_info['sold'] = mode.get_sold()
    mode_info['count'] = mode_count
    mode_info['days'] = mode_days
    mode_info['earn_sum'] = mode_earn
    return render(request, 'strategy.html', {'latest_date': latest_date, 'mode_info': mode_info})

def home(request):
    try:
        latest_date = StockInfo.objects.latest('date').date - timedelta(days=1)
    except:
        latest_date = '2023-01-01'

    trace_data_info = {}
    # Query the first 50 records ordered by pwp in descending order
    pred5_stock_infos = ACCStocks.objects.filter(pred_high__gt=5, pwp__gt=80, model_name='pred5', wp__lt=F('pwp')).order_by('-percentage')[:10]
    pred10_stock_infos = ACCStocks.objects.filter(pred_high__gt=5, pwp__gt=80, model_name='pred10', wp__lt=F('pwp')).order_by('-percentage')[:10]



    # Get all StockInfo objects
    if request.method == 'POST':
        try:
            trace_data = StockInfo.objects.filter(stock_id=request.POST.get('stock_code'))
            trace_data_info['title'] = request.POST.get('stock_code')
            trace_data_info['title_name'] = StocksType.objects.get(stock_id=request.POST.get('stock_code')).stock_name
            trace_data_info['pred5'] = ACCStocks.objects.get(stock_id=request.POST.get('stock_code'), model_name='pred5')
            trace_data_info['pred10'] = ACCStocks.objects.get(stock_id=request.POST.get('stock_code'),
                                                             model_name='pred10')
        except:
            return render(request, 'home.html', {'latest_date': latest_date, 'pred5_stock_infos': pred5_stock_infos,
                                                 'pred10_stock_infos': pred10_stock_infos,
                                                 'trace_data_info': trace_data_info})
    else:
        trace_data = TypesInfo.objects.filter(stock_id='0000')
        trace_data_info['title'] = 'Overview'
        trace_data_info['title_name'] = '上市總攬'
    return render(request, 'home.html', {'latest_date': latest_date, 'pred5_stock_infos': pred5_stock_infos, 'pred10_stock_infos': pred10_stock_infos, 'trace_data': trace_data, 'trace_data_info':trace_data_info})


@user_passes_test(lambda user: user.is_superuser)
def clean_all_data(request):
    ACCStocks.objects.all().delete()
    StockInfo.objects.all().delete()
    StocksType.objects.all().delete()
    StrategyMode.objects.all().delete()
    StocksHistory.objects.all().delete()
    return render(request, 'home.html', {})


@user_passes_test(lambda user: user.is_superuser)
def update_stock_types(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        file = request.FILES['csv_file']
        if file.name.endswith('.csv'):
            StocksType.objects.all().delete()
            df = pd.read_csv(file)
            for index, row in df.iterrows():
                stock_id = row['stock_id']
                stock_type = row['產業類別']
                stock_name = row['公司簡稱']
                stock_type_info, _ = StocksType.objects.get_or_create(stock_id=stock_id, stock_type=stock_type, stock_name=stock_name)
    return render(request, 'home.html', {})


def update_overall(date, data=None):
    try:
        latest_date = TypesInfo.objects.latest('date').date
    except:
        latest_date = date
    if not data:
        past_overall = TypesInfo.objects.get(stock_id='0000', date=latest_date)
        future_date = date + timedelta(days=1)
        overall, created = TypesInfo.objects.get_or_create(stock_id='0000', date=future_date, defaults={
            'prediction1': 0,
            'prediction2': 0,
        })
        overall.pred1_future = past_overall.prediction1
        overall.pred2_future = past_overall.prediction2
        overall.save()
    else:
        overall, created = TypesInfo.objects.get_or_create(stock_id='0000', date=latest_date, defaults={
            'prediction1': data[0],
            'prediction2': data[1],
            'price': data[2],
        })
        if not overall.price:
            overall.price = 0
        if latest_date != date:
            overall.date = date
        overall.prediction1 = data[0]
        overall.prediction2 = data[1]
        overall.price = data[2]
        overall.save()





def update_data(file, date=None):
    df = pd.read_csv(file)
    df['pred5'] = (df['close'] * (1 + df['pred5']))
    df['pred10'] = (df['close'] * (1 + df['pred10']))
    df['close'] = df['close'].apply(decimal.Decimal)
    df['pred5'] = df['pred5'].apply(decimal.Decimal)
    df['pred10'] = df['pred10'].apply(decimal.Decimal)
    df.dropna(inplace=True)
    # Extract the date from the filename
    if not date:
        filename = file.name
        date_str = filename.split('_')[1].split('.')[0]
        date = pd.to_datetime(date_str).date()
    overall_data = [0, 0, 0]
    for index, row in df.iterrows():
        stock_id = row['stock_id'][:4]
        pred5 = row['pred5']
        pred10 = row['pred10']
        close = row['close']
        try:
            latest_date = StockInfo.objects.filter(stock_id=stock_id).latest('date').date
            stock_info = StockInfo.objects.get(date=latest_date, stock_id=stock_id)
            if latest_date != date:
                stock_info.date = date
            elif latest_date > date:
                break
            stock_info.prediction1 = pred5
            stock_info.prediction2 = pred10
            stock_info.price = close
            stock_info.save()
        except:
            new_stock_info = StockInfo.objects.get_or_create(
                date=date,
                stock_id=stock_id,
                defaults={'prediction1': pred5, 'prediction2': pred10, 'price': close}
            )
        overall_data[0] += pred5
        overall_data[1] += pred10
        overall_data[2] += close

        future_date = date + timedelta(days=1)
        new_stock_info = StockInfo.objects.get_or_create(
            date=future_date,
            stock_id=stock_id,
            prediction1=pred5,
            prediction2=pred10,
            pred1_future=pred5,
            pred2_future=pred10
        )
        # Retrieve the StockInfo objects for the specified stock_id, ordered by date from newest to oldest
        stock_info_list = StockInfo.objects.filter(stock_id=stock_id).order_by('-date')[:7]
        # Check if the list has at least 5 elements
        if len(stock_info_list) >= 7:
            # Retrieve the StockInfo object at the 5th row (index 4)
            stock_info = stock_info_list[6]
            #print(stock_info, stock_info.price, stock_info.date)
            past_pred5 = stock_info.prediction1
            past_pred10 = stock_info.prediction2
            past_close = stock_info.price
            max_close = StockInfo.objects.filter(stock_id=stock_id).order_by('-date')[1:5].aggregate(Max('price'))[
                'price__max']
            min_close = StockInfo.objects.filter(stock_id=stock_id).order_by('-date')[1:5].aggregate(Min('price'))[
                'price__min']
            mean_price = (max_close + min_close) / 2
            for model_name in ['pred5', 'pred10']:
                if model_name == 'pred5':
                    past_pred = past_pred5
                    percentage = round((pred5 - close) / close * 100)
                else:
                    past_pred = past_pred10
                    percentage = round((pred10 - close) / close * 100)
                acc_stock, _ = ACCStocks.objects.get_or_create(stock_id=stock_id, model_name=model_name, defaults={
                    'count': 0, 'high': 0, 'low': 0, 'pred_high': 0, 'pred_low': 0, 'pred_high_correct': 0,
                    'pred_low_correct': 0, 'rmse': 0, 'wp': 0, 'pwp': 0, 'percentage': 0
                })
                acc_stock.percentage = percentage
                acc_stock.count += 1
                acc_stock.rmse += ((mean_price - past_pred) / past_pred) ** 2
                if mean_price > past_close:
                    acc_stock.high += 1
                if mean_price < past_close:
                    acc_stock.low += 1
                if (past_pred - past_close) / past_close * 100 > 1:
                    acc_stock.pred_high += 1
                    if mean_price > past_close:
                        acc_stock.pred_high_correct += 1
                if (past_pred - past_close) / past_close * 100 < 1:
                    acc_stock.pred_low += 1
                    if mean_price < past_close:
                        acc_stock.pred_low_correct += 1
                acc_stock.wp = acc_stock.high / acc_stock.count * 100
                if acc_stock.pred_high > 0:
                    acc_stock.pwp = acc_stock.pred_high_correct / acc_stock.pred_high * 100
                acc_stock.save()

    # Redirect back to the page or render a success message
    update_overall(date, overall_data)
    update_overall(date)
    update_mode('low_risk', date)
    print(date)
    return(date)


@user_passes_test(lambda user: user.is_superuser)
def update_daily_data(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        file = request.FILES['csv_file']
        if file.name.endswith('.csv'):
            # Read the CSV file using pandas
            latest_date = update_data(file)
            try:
                existing_file = File.objects.get(file_name=file.name)
                existing_file.file.delete(save=False)  # Delete the associated file from the storage
                existing_file.delete()
            except:
                File.objects.create(file=file, file_name=file.name)

            return render(request, 'home.html', {'latest_date': latest_date})

    return render(request, 'home.html', {})


def create_files_from_upload_directory():
    upload_directory = os.path.join(settings.MEDIA_ROOT, 'files')

    # Get the list of files in the upload directory
    file_names = os.listdir(upload_directory)

    for file_name in file_names:
        file_path = os.path.join(upload_directory, file_name)

        # Create a File object
        file_obj, created = File.objects.get_or_create(file='files/{}'.format(file_name), file_name=file_name)

        # Perform any additional operations or save the file object as needed
        # For example, you can set other attributes of the file object or save it to the database
        # file_obj.attribute = value
        # file_obj.save()


@user_passes_test(lambda user: user.is_superuser)
def refresh(request):
    create_files_from_upload_directory()
    ACCStocks.objects.all().delete()
    StockInfo.objects.all().delete()
    TypesInfo.objects.all().delete()
    StrategyMode.objects.all().delete()
    StocksHistory.objects.all().delete()
    existing_files = File.objects.filter(file__icontains='pred_').order_by('-uploaded_at')

    # Extract the dates from the file names
    file_dates = []
    for file in existing_files:
        date_str = file.file.name.split('_')[1].split('.')[0]
        file_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        file_dates.append((file, file_date))

    # Sort the file dates in ascending order
    file_dates = sorted(file_dates, key=lambda x: x[1])

    for file, current_date in file_dates:
        file_path = file.file.path
        update_data(file_path, current_date)

    return render(request, 'home.html', {})