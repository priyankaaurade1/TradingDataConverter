import os
import csv
import json
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from .forms import CSVUploadForm
from .models import CSVUpload
from asgiref.sync import sync_to_async
from datetime import datetime, timedelta
from django.urls import reverse

def process_csv(file_path, timeframe):
    candles = []
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for i, row in enumerate(reader):
            date = datetime.strptime(f"{row['DATE']} {row['TIME']}", '%Y%m%d %H:%M')
            candles.append({
                'id': i,
                'open': float(row['OPEN']),
                'high': float(row['HIGH']),
                'low': float(row['LOW']),
                'close': float(row['CLOSE']),
                'date': date
            })

    # Convert to given timeframe
    timeframe_candles = []
    start_time = candles[0]['date']
    end_time = start_time + timedelta(minutes=timeframe)

    while start_time < candles[-1]['date']:
        timeframe_data = [c for c in candles if start_time <= c['date'] < end_time]
        if not timeframe_data:
            break

        timeframe_candles.append({
            'id': len(timeframe_candles),
            'open': timeframe_data[0]['open'],
            'high': max(c['high'] for c in timeframe_data),
            'low': min(c['low'] for c in timeframe_data),
            'close': timeframe_data[-1]['close'],
            'date': start_time
        })
        start_time = end_time
        end_time += timedelta(minutes=timeframe)

    # Save JSON
    json_file_name = f"converted_{os.path.basename(file_path)}.json"
    json_file_path = os.path.join(settings.MEDIA_ROOT, json_file_name)
    with open(json_file_path, 'w') as jsonfile:
        json.dump(timeframe_candles, jsonfile, default=str)

    return json_file_name

async def upload_csv(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            upload = await sync_to_async(form.save)()
            file_path = upload.file.path
            timeframe = form.cleaned_data['timeframe']
            json_file_name = await sync_to_async(process_csv)(file_path, timeframe)
            json_file_url = request.build_absolute_uri(reverse('download_json', args=[json_file_name]))
            return JsonResponse({'json_file_url': json_file_url})
    else:
        form = CSVUploadForm()
    return render(request, 'upload.html', {'form': form})

async def download_json(request, file_name):
    file_path = os.path.join(settings.MEDIA_ROOT, file_name)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/json")
            response['Content-Disposition'] = f'attachment; filename={os.path.basename(file_path)}'
            return response
    else:
        return JsonResponse({'error': 'File not found'})
