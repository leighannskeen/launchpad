import urllib

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.utils import DatabaseError
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect
from django.utils import simplejson as json
from django.views.decorators.cache import cache_page

from ui import voyager, apis
from ui.sort import libsort, availsort, elecsort, splitsort


def home(request):
    return render(request, 'home.html', {
        'title': 'launchpad home',
        'google_analytics_ua': settings.GOOGLE_ANALYTICS_UA,
        })


def _openurl_dict(params):
    """Split openurl params into a useful structure"""
    p = {}
    for k, v in dict(params).items():
        p[k] = ','.join(v)
    d = {'params':  p}
    d['query_string'] = '&'.join(['%s=%s' % (k, v) for k, v
        in params.items()])
    d['query_string_encoded'] = urllib.urlencode(params).encode('utf-8')
    return d


@cache_page(settings.ITEM_PAGE_CACHE_SECONDS)
def item(request, bibid):
    try:
        bib = voyager.get_bib_data(bibid)
        if not bib:
            return render(request, '404.html', {'num': bibid,
                'num_type': 'BIB ID'}, status=404)
        bib['openurl'] = _openurl_dict(request.GET)
        # Ensure bib data is ours if possible
        if not bib['LIBRARY_NAME'] == settings.PREF_LIB:
            for alt_bib in bib['BIB_ID_LIST']:
                if alt_bib['LIBRARY_NAME'] == settings.PREF_LIB:
                    return item(request, alt_bib['BIB_ID'])
        holdings = voyager.get_holdings(bib)
        ours, theirs, shared = splitsort(holdings)
        holdings = availsort(elecsort(ours)) + availsort(elecsort(shared)) \
            + libsort(elecsort(availsort(theirs), rev=True))
        return render(request, 'item.html', {
            'bibid': bibid,
            'bib': bib,
            'debug': settings.DEBUG,
            'title_chars': settings.TITLE_CHARS,
            'title_leftover_chars': settings.TITLE_LEFTOVER_CHARS,
            'holdings': holdings,
            'link': bib.get('LINK', '')[9:],
            'google_analytics_ua': settings.GOOGLE_ANALYTICS_UA,
            'link_resolver': settings.LINK_RESOLVER,
            'enable_humans': settings.ENABLE_HUMANS,
            'audio_tags': settings.STREAMING_AUDIO_TAGS,
            'video_tags': settings.STREAMING_VIDEO_TAGS,
            })
    except DatabaseError:
        from datetime import datetime
        if datetime.now().hour == 3:
            return render(request, '503.html', status=503)
        else:
            raise


def _date_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj


@cache_page(settings.ITEM_PAGE_CACHE_SECONDS)
def item_json(request, bibid):
    bib_data = voyager.get_bib_data(bibid)
    bib_data['holdings'] = voyager.get_holdings(bib_data)
    bib_data['openurl'] = _openurl_dict(request.GET)
    return HttpResponse(json.dumps(bib_data, default=_date_handler,
        indent=2), content_type='application/json')


def non_wrlc_item(request, num, num_type):
    bib = apis.get_bib_data(num=num, num_type=num_type)
    if not bib:
        return render(request, '404.html', {'num': num,
            'num_type': num_type.upper()}, status=404)
    bib['ILLIAD_LINK'] = voyager.get_illiad_link(bib)
    return render(request, 'item.html', {
       'bibid': '',
       'bib': bib,
       'debug': settings.DEBUG,
       'title_chars': settings.TITLE_CHARS,
       'title_leftover_chars': settings.TITLE_LEFTOVER_CHARS,
       'holdings': [],
       'link': '',
       'google_analytics_ua': settings.GOOGLE_ANALYTICS_UA,
       'link_resolver': settings.LINK_RESOLVER,
       'audio_tags': settings.STREAMING_AUDIO_TAGS,
       'video_tags': settings.STREAMING_VIDEO_TAGS,
       })


def gtitem(request, gtbibid):
    bibid = voyager.get_wrlcbib_from_gtbib(gtbibid)
    if bibid:
        return redirect('item', bibid=bibid)
    return render(request, '404.html', {'num': gtbibid,
        'num_type': 'Georgetown BIB ID'}, status=404)


def gtitem_json(request, gtbibid):
    bibid = voyager.get_wrlcbib_from_gtbib(gtbibid)
    if bibid:
        return redirect('item_json', bibid=bibid)
    raise Http404


def gmitem(request, gmbibid):
    bibid = voyager.get_wrlcbib_from_gmbib(gmbibid)
    if bibid:
        return redirect('item', bibid=bibid)
    return render(request, '404.html', {'num': gmbibid,
        'num_type': 'George Mason BIB ID'}, status=404)


def gmitem_json(request, gmbibid):
    bibid = voyager.get_wrlcbib_from_gmbib(gmbibid)
    if bibid:
        return redirect('item_json', bibid=bibid)
    raise Http404


def isbn(request, isbn):
    bibid = voyager.get_primary_bibid(num=isbn, num_type='isbn')
    openurl = _openurl_dict(request.GET)
    if bibid:
        url = '%s?%s' % (reverse('item', args=[bibid]),
            openurl['query_string_encoded'])
        return redirect(url)
    return non_wrlc_item(request, num=isbn, num_type='isbn')


def issn(request, issn):
    bibid = voyager.get_primary_bibid(num=issn, num_type='issn')
    openurl = _openurl_dict(request.GET)
    if bibid:
        url = '%s?%s' % (reverse('item', args=[bibid]),
            openurl['query_string_encoded'])
        return redirect(url)
    return non_wrlc_item(request, num=issn, num_type='issn')


def oclc(request, oclc):
    bibid = voyager.get_primary_bibid(num=oclc, num_type='oclc')
    openurl = _openurl_dict(request.GET)
    if bibid:
        url = '%s?%s' % (reverse('item', args=[bibid]),
            openurl['query_string_encoded'])
        return redirect(url)
    return render(request, '404.html', {'num': oclc,
        'num_type': 'OCLC number'}, status=404)


def error500(request):
    return render(request, '500.html', {
        'title': 'error',
        'google_analytics_ua': settings.GOOGLE_ANALYTICS_UA,
        }, status=500)


def robots(request):
    return render(request, 'robots.txt', {
        'enable_sitemaps': settings.ENABLE_SITEMAPS,
        'sitemaps_base_url': settings.SITEMAPS_BASE_URL,
        }, content_type='text/plain')


def humans(request):
    return render(request, 'humans.txt', {}, content_type='text/plain')
