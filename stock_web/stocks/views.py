from django.shortcuts import render
from datetime import datetime, date, timedelta
import pandas as pd
from .models import StockInfo, ACCStocks, StocksType, StrategyMode, StocksHistory, File
from django.db.models import Max, Min
import math
import os
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test



# Create your views here.
def update_mode(mode_name):
    mode, created = StrategyMode.objects.get_or_create(mode_name=mode_name)

    try:
        latest_date = StockInfo.objects.latest('date').date
    except StockInfo.DoesNotExist:
        latest_date = '2023-01-01'
    if latest_date > date(2023, 3, 1):
        exist_histories = mode.get_exist()
        for history in exist_histories:
            stock_info = StockInfo.objects.get(stock_id=history.stock_id, date=latest_date)
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
            if (history.buy_price > history.target) or (stock_close - float(history.buy_price))/float(history.buy_price) < -0.1:
                history.sell_price = stock_close
                history.sell_date = latest_date
            history.save()
        exist_histories = exist_histories.values_list('stock_id', flat=True)
        all_acc_stocks = ACCStocks.objects.filter(model_name='pred10')
        results = []
        for acc_stock in all_acc_stocks:
            if acc_stock.pred_high > 5:
                value = acc_stock.pred_high_correct / acc_stock.pred_high
                overall = acc_stock.high / acc_stock.count
                rounded_value = round(value, 2)
                if (overall < rounded_value) and (rounded_value > 0.8):
                    results.append((acc_stock, rounded_value))
        sorted_results = sorted(results, key=lambda x: x[1])
        smallest_50 = sorted_results[:100]
        for stock_item in smallest_50:
            stock_id = stock_item[0].stock_id
            stock_info = StockInfo.objects.get(stock_id=stock_id, date=latest_date)
            stock_pred = stock_info.prediction2
            stock_close = float(stock_info.price)
            stock_percentage = round(((stock_pred - stock_close) / stock_close) * 100, 2)
            range = round((stock_pred - stock_close)/5, 2)
            if stock_id not in exist_histories and stock_percentage > 5:
                stock_history = StocksHistory.objects.create(stock_id=stock_id, buy_price=stock_close, buy_date=latest_date, current_price=stock_close, target=stock_pred, range=range)
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
        latest_date = StockInfo.objects.latest('date').date
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
        latest_date = StockInfo.objects.latest('date').date
    except:
        latest_date = '2023-01-01'

    trace_data_info = {'title': 'Overview', 'title_name': '上市總攬'}
    pred5_stock_infos = []
    pred10_stock_infos = []
    if latest_date != '2023-01-01':
        # Retrieve all ACCStocks objects
        all_acc_stocks = ACCStocks.objects.filter(model_name='pred5')

        # Calculate and round the square root of RMSE/count for each object
        results = []
        for acc_stock in all_acc_stocks:
            if acc_stock.pred_high > 5:
                value = acc_stock.pred_high_correct / acc_stock.pred_high
                overall = acc_stock.high / acc_stock.count
                rounded_value = round(value, 2)
                if (request.method == 'POST') and (acc_stock.stock_id == str(request.POST.get('stock_code'))):
                    trace_data_info['pred1_rmse'] = rounded_value
                    trace_data_info['pred1_count'] = acc_stock.count
                    trace_data_info['pred1_pred_count'] = acc_stock.pred_high
                    trace_data_info['pred1_high_rate'] = round((acc_stock.high / acc_stock.count)*100)
                    trace_data_info['pred1_low_rate'] = round((acc_stock.low / acc_stock.count)*100)
                    trace_data_info['pred1_pred_high_rate'] = round((acc_stock.pred_high_correct / acc_stock.pred_high)*100)
                    trace_data_info['pred1_pred_low_rate'] = round((acc_stock.pred_low_correct / acc_stock.pred_low)*100)

                if (overall < rounded_value) and (rounded_value > 0.8):
                    results.append((acc_stock, rounded_value))

        # Sort the results based on the rounded value in ascending order
        sorted_results = sorted(results, key=lambda x: x[1], reverse=True)

        # Retrieve the ten objects with the smallest rounded values
        smallest_10 = sorted_results[:50]
        for stock_item in smallest_10:
            stock_id = stock_item[0].stock_id
            stock_rmse = stock_item[1]
            stock_name = StocksType.objects.get(stock_id=stock_id).stock_name
            stock_info = StockInfo.objects.get(stock_id=stock_id, date=latest_date)
            stock_pred = stock_info.prediction1
            stock_close = float(stock_info.price)
            stock_percentage = round(((stock_pred - stock_close)/stock_close)*100, 2)
            pred5_stock_infos.append({
                'stock_name': stock_name,
                'stock_id': stock_id,
                'stock_rmse': stock_rmse,
                'count': stock_item[0].count,
                'pred_count': stock_item[0].pred_high,
                'high_rate': round((stock_item[0].high / stock_item[0].count)*100),
                'low_rate': round((stock_item[0].low / stock_item[0].count)*100),
                'pred_high_rate': round((stock_item[0].pred_high_correct / stock_item[0].pred_high)*100),
                'pred_low_rate': round((stock_item[0].pred_low_correct / stock_item[0].pred_low)*100),
                'stock_close': stock_close,
                'stock_percent': stock_percentage
            })
        pred5_stock_infos = sorted(pred5_stock_infos, key=lambda x: x['stock_percent'], reverse=True)
        pred5_stock_infos = pred5_stock_infos[:10]

        # Retrieve all ACCStocks objects
        all_acc_stocks = ACCStocks.objects.filter(model_name='pred10')

        # Calculate and round the square root of RMSE/count for each object
        results = []
        for acc_stock in all_acc_stocks:
            if acc_stock.pred_high > 5:
                value = acc_stock.pred_high_correct / acc_stock.pred_high
                overall = acc_stock.high / acc_stock.count
                rounded_value = round(value, 2)
                if (request.method == 'POST') and (acc_stock.stock_id == str(request.POST.get('stock_code'))):
                    trace_data_info['pred2_rmse'] = rounded_value
                    trace_data_info['pred2_count'] = acc_stock.count
                    trace_data_info['pred2_pred_count'] = acc_stock.pred_high
                    trace_data_info['pred2_high_rate'] = round((acc_stock.high / acc_stock.count) * 100)
                    trace_data_info['pred2_low_rate'] = round((acc_stock.low / acc_stock.count) * 100)
                    trace_data_info['pred2_pred_high_rate'] = round(
                        (acc_stock.pred_high_correct / acc_stock.pred_high) * 100)
                    trace_data_info['pred2_pred_low_rate'] = round(
                        (acc_stock.pred_low_correct / acc_stock.pred_low) * 100)

                if (overall < rounded_value) and (rounded_value > 0.8):
                    results.append((acc_stock, rounded_value))

        # Sort the results based on the rounded value in ascending order
        sorted_results = sorted(results, key=lambda x: x[1], reverse=True)

        # Retrieve the ten objects with the smallest rounded values
        smallest_10 = sorted_results[:50]
        for stock_item in smallest_10:
            stock_id = stock_item[0].stock_id
            stock_rmse = stock_item[1]
            stock_name = StocksType.objects.get(stock_id=stock_id).stock_name
            stock_info = StockInfo.objects.get(stock_id=stock_id, date=latest_date)
            stock_pred = stock_info.prediction2
            stock_close = float(stock_info.price)
            stock_percentage = round(((stock_pred - stock_close) / stock_close) * 100, 2)
            pred10_stock_infos.append({
                'stock_name': stock_name,
                'stock_id': stock_id,
                'stock_rmse': stock_rmse,
                'count': stock_item[0].count,
                'pred_count': stock_item[0].pred_high,
                'high_rate': round((stock_item[0].high / stock_item[0].count)*100),
                'low_rate': round((stock_item[0].low / stock_item[0].count)*100),
                'pred_high_rate': round((stock_item[0].pred_high_correct / stock_item[0].pred_high)*100),
                'pred_low_rate': round((stock_item[0].pred_low_correct / stock_item[0].pred_low)*100),
                'stock_close': stock_close,
                'stock_percent': stock_percentage
            })
        pred10_stock_infos = sorted(pred10_stock_infos, key=lambda x: x['stock_percent'], reverse=True)
        pred10_stock_infos = pred10_stock_infos[:10]
    # Get all StockInfo objects
    if request.method == 'POST':
        try:
            stock_infos = StockInfo.objects.filter(stock_id=request.POST.get('stock_code'))
            trace_data_info['title'] = request.POST.get('stock_code')
            trace_data_info['title_name'] = StocksType.objects.get(stock_id=request.POST.get('stock_code')).stock_name
        except:
            return render(request, 'home.html', {'latest_date': latest_date, 'pred5_stock_infos': pred5_stock_infos,
                                                 'pred10_stock_infos': pred10_stock_infos,
                                                 'trace_data_info': trace_data_info})
    else:
        stock_infos = StockInfo.objects.all()

    # Create a dictionary to store the summed values
    trace_data_sum = {}
    trace_data = {}

    # Iterate over each StockInfo object and sum the values by date
    for stock_info in stock_infos:
        date = stock_info.date
        prediction1 = stock_info.prediction1
        prediction2 = stock_info.prediction2
        price = stock_info.price

        if date in trace_data_sum:
            trace_data_sum[date]['prediction1'] += prediction1
            trace_data_sum[date]['prediction2'] += prediction2
            trace_data_sum[date]['price'] += price
        else:
            trace_data_sum[date] = {
                'prediction1': prediction1,
                'prediction2': prediction2,
                'price': price
            }

    # Round the summed values to 2 decimal places
    for date in trace_data_sum:
        trace_data_sum[date]['prediction1'] = round(trace_data_sum[date]['prediction1'], 2)
        trace_data_sum[date]['prediction2'] = round(trace_data_sum[date]['prediction2'], 2)
        trace_data_sum[date]['price'] = round(float(trace_data_sum[date]['price']), 2)

    trace_data_sum = list(trace_data_sum.items())

    for i in range(1, len(trace_data_sum)+1):
        past_key, past_content = trace_data_sum[i - 1]
        if i == 1:
            prediction1 = 'null'
            prediction2 = 'null'
            price = past_content['price']
        else:
            new_key, new_content = trace_data_sum[i - 2]
            prediction1 = new_content['prediction1']
            prediction2 = new_content['prediction2']
            price = past_content['price']

        trace_data[past_key] = {
            'prediction1': prediction1,
            'prediction2': prediction2,
            'price': price
        }
        if i == len(trace_data_sum):
            past_key = past_key + timedelta(days=1)
            prediction1 = past_content['prediction1']
            prediction2 = past_content['prediction2']
            trace_data_info['close'] = price
            trace_data_info['pred1_percentage'] = round(((prediction1 - price) / price) * 100, 2)
            trace_data_info['pred2_percentage'] = round(((prediction2 - price) / price) * 100, 2)
            price = 'null'
            trace_data[past_key] = {
                'prediction1': prediction1,
                'prediction2': prediction2,
                'price': price
            }
            trace_data_info['pred1'] = prediction1
            trace_data_info['pred2'] = prediction2


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


def update_data(file, date=None):
    df = pd.read_csv(file)
    df['voting'] = (df['pred5'] + df['pred10']) / 2
    df['pred5'] = df['close'] * (1 + df['pred5'])
    df['pred10'] = df['close'] * (1 + df['pred10'])
    df['voting'] = df['close'] * (1 + df['voting'])
    df.dropna(inplace=True)
    # Extract the date from the filename
    if not date:
        filename = file.name
        date_str = filename.split('_')[1].split('.')[0]
        date = pd.to_datetime(date_str).date()

    try:
        latest_date = StockInfo.objects.latest('date').date
        new_date = date  # Set the desired new date

        # Retrieve all the StockInfo objects with the latest date
        latest_stock_info_list = StockInfo.objects.filter(date=latest_date)
        if len(StockInfo.objects.filter(date=new_date)) != 0:
            return latest_date
        # Create new StockInfo objects with the new date based on the latest objects
        for latest_stock_info in latest_stock_info_list:
            new_stock_info = StockInfo.objects.get_or_create(
                date=new_date,
                stock_id=latest_stock_info.stock_id,
                prediction1=latest_stock_info.price,
                prediction2=latest_stock_info.price,
                voting=latest_stock_info.price,
                price=latest_stock_info.price
            )

            # Optionally, you can also save the newly created object

        # Use the new_stock_info objects as needed
        # For example, you can access the date using new_stock_info.date
    except StockInfo.DoesNotExist:
        # Handle the case when no StockInfo objects exist
        pass

    # Process the data and update the StockInfo model
    for index, row in df.iterrows():
        stock_id = row['stock_id'][:4]
        pred5 = row['pred5']
        pred10 = row['pred10']
        voting = row['voting']
        close = row['close']

        # Update the StockInfo model or perform any other necessary actions
        try:
            stock_info, created = StockInfo.objects.get_or_create(date=date, stock_id=stock_id, defaults={
                'prediction1': pred5, 'prediction2': pred10, 'voting': voting, 'price': close
            })
            if not created:
                stock_info.prediction1 = pred5
                stock_info.prediction2 = pred10
                stock_info.voting = voting
                stock_info.price = close
                stock_info.save()

            # Update the ACCStocks model with pred correctness

            # Retrieve the StockInfo objects for the specified stock_id, ordered by date from newest to oldest
            stock_info_list = StockInfo.objects.filter(stock_id=stock_id).order_by('-date')
            # Check if the list has at least 5 elements
            if len(stock_info_list) >= 6:
                # Retrieve the StockInfo object at the 5th row (index 4)
                stock_info = stock_info_list[5]
                past_pred5 = stock_info.prediction1
                past_pred10 = stock_info.prediction2
                past_voting = stock_info.voting
                past_close = float(stock_info.price)
                max_close = float(
                    StockInfo.objects.filter(stock_id=stock_id).order_by('-date')[:4].aggregate(Max('price'))[
                        'price__max'])
                min_close = float(
                    StockInfo.objects.filter(stock_id=stock_id).order_by('-date')[:4].aggregate(Min('price'))[
                        'price__min'])
                mean_price = (max_close + min_close) / 2
                for model_name in ['pred5', 'pred10', 'voting']:
                    if model_name == 'pred5':
                        past_pred = past_pred5
                    elif model_name == 'pred10':
                        past_pred = past_pred10
                    else:
                        past_pred = past_voting
                    acc_stock, _ = ACCStocks.objects.get_or_create(stock_id=stock_id, model_name=model_name, defaults={
                        'count': 0, 'high': 0, 'low': 0, 'pred_high': 0, 'pred_low': 0, 'pred_high_correct': 0,
                        'pred_low_correct': 0, 'rmse': 0
                    })
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
                    acc_stock.save()
        except Exception as e:
            print(stock_id, e)
            pass
    # Redirect back to the page or render a success message
    latest_date = StockInfo.objects.latest('date').date
    update_mode('low_risk')
    return(latest_date)


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