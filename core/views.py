import json
import requests
import os
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from .models import Comment

ADMIN_PASSWORD = getattr(settings, 'ADMIN_PASSWORD', '27112010')
RATES_FILE = os.path.join(settings.BASE_DIR, 'custom_rates.json')
CURRENCIES = ['USD', 'EUR', 'RUB', 'UZS', 'KZT', 'CNY']

DEFAULT_RATES = {
    'USD': {'buy': 87.40, 'sell': 87.65},
    'EUR': {'buy': 99.00, 'sell': 103.00},
    'RUB': {'buy': 1.09,  'sell': 1.15},
    'UZS': {'buy': 0.0067,'sell': 0.0075},
    'KZT': {'buy': 0.15,  'sell': 0.19},
    'CNY': {'buy': 12.00, 'sell': 14.00},
}


def index(request):
    return render(request, 'index.html')


def load_custom_rates():
    try:
        if os.path.exists(RATES_FILE):
            with open(RATES_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_custom_rates(rates):
    with open(RATES_FILE, 'w') as f:
        json.dump(rates, f, indent=2)


def fetch_external_rates():
    try:
        resp = requests.get(
            'https://api.exchangerate-api.com/v4/latest/KGS', timeout=5)
        data = resp.json()
        rates_from_kgs = data.get('rates', {})
        result = {}
        for code in CURRENCIES:
            r = rates_from_kgs.get(code)
            if r and r != 0:
                result[code] = round(1 / r, 6)
        return result
    except Exception:
        return {}


def rates_view(request):
    custom = load_custom_rates()
    external = fetch_external_rates()
    SPREAD = 0.005
    result = {}
    for code in CURRENCIES:
        if code in custom:
            buy = custom[code].get('buy')
            sell = custom[code].get('sell')
            if buy is None and sell is None:
                mid = external.get(code) or DEFAULT_RATES[code]['buy']
                buy = round(mid * (1 - SPREAD), 4)
                sell = round(mid * (1 + SPREAD), 4)
            elif buy is None:
                buy = round(sell * (1 - SPREAD * 2), 4)
            elif sell is None:
                sell = round(buy * (1 + SPREAD * 2), 4)
            result[code] = {'buy': buy, 'sell': sell}
        elif code in external:
            mid = external[code]
            result[code] = {
                'buy': round(mid * (1 - SPREAD), 4),
                'sell': round(mid * (1 + SPREAD), 4)
            }
        else:
            result[code] = DEFAULT_RATES.get(code, {'buy': 0, 'sell': 0})
    return JsonResponse({'rates': result})


@csrf_exempt
@require_http_methods(['POST'])
def admin_check_view(request):
    try:
        data = json.loads(request.body)
        if data.get('password') == ADMIN_PASSWORD:
            return JsonResponse({'ok': True})
        return JsonResponse({'ok': False}, status=403)
    except Exception:
        return JsonResponse({'error': 'bad request'}, status=400)


def admin_rates_view(request):
    return JsonResponse({'rates': load_custom_rates()})


@csrf_exempt
@require_http_methods(['POST'])
def admin_save_view(request):
    try:
        data = json.loads(request.body)
        if data.get('password') != ADMIN_PASSWORD:
            return JsonResponse({'error': 'forbidden'}, status=403)
        rates = data.get('rates', {})
        clean = {}
        for code, vals in rates.items():
            if code in CURRENCIES and isinstance(vals, dict):
                clean[code] = {
                    'buy':  float(vals['buy'])  if vals.get('buy')  else None,
                    'sell': float(vals['sell']) if vals.get('sell') else None,
                }
        save_custom_rates(clean)
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(['GET'])
def api_comments(request):
    comments = Comment.objects.order_by('-pinned', '-created_at')
    data = [
        {
            'id': c.id,
            'author': c.author,
            'text': c.text,
            'currency': c.currency,
            'rating': c.rating,
            'pinned': c.pinned,
            'created_at': c.created_at.strftime('%d.%m.%Y %H:%M'),
        }
        for c in comments
    ]
    return JsonResponse({'comments': data})


@csrf_exempt
@require_http_methods(['POST'])
def api_comment_add(request):
    try:
        data = json.loads(request.body)
        author   = (data.get('author') or 'Аноним').strip()[:80]
        text     = (data.get('text') or '').strip()[:500]
        currency = (data.get('currency') or '').strip()[:10]
        rating   = max(1, min(5, int(data.get('rating') or 5)))
        if not text:
            return JsonResponse({'ok': False, 'error': 'empty'}, status=400)
        c = Comment.objects.create(
            author=author, text=text, currency=currency, rating=rating)
        return JsonResponse({'ok': True, 'comment': {
            'id': c.id, 'author': c.author, 'text': c.text,
            'currency': c.currency, 'rating': c.rating,
            'pinned': c.pinned,
            'created_at': c.created_at.strftime('%d.%m.%Y %H:%M'),
        }})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(['POST'])
def api_comment_delete(request):
    try:
        data = json.loads(request.body)
        if data.get('password') != ADMIN_PASSWORD:
            return JsonResponse({'ok': False}, status=403)
        Comment.objects.filter(id=data.get('id')).delete()
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(['POST'])
def api_comment_pin(request):
    try:
        data = json.loads(request.body)
        if data.get('password') != ADMIN_PASSWORD:
            return JsonResponse({'ok': False}, status=403)
        c = Comment.objects.get(id=data.get('id'))
        c.pinned = not c.pinned
        c.save()
        return JsonResponse({'ok': True, 'pinned': c.pinned})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)