"""
CSV export for the Status sections (R12 phase 2): `?export=csv` on a list endpoint.

UTF-8 with a BOM (Excel opens Cyrillic and Uzbek text correctly), streamed, at most
CSV_EXPORT_MAX_ROWS data rows followed by a final "truncated" line when there were more.
Cells that a spreadsheet would run as a formula (starting with = + - @, tab or CR) get a
leading apostrophe. Every export is written to the admin access log (`export_csv`, export
name and row count only).
"""
import csv
from itertools import islice

from django.conf import settings
from django.http import StreamingHttpResponse

BOM = '﻿'
TRUNCATED = 'truncated'
_FORMULA_START = ('=', '+', '-', '@', '\t', '\r')


def wants_csv(request):
    return (request.query_params.get('export') or '').strip().lower() == 'csv'


def max_rows():
    return int(getattr(settings, 'CSV_EXPORT_MAX_ROWS', 10000))


def safe_cell(value):
    if value is None:
        return ''
    text = str(value)
    if text.startswith(_FORMULA_START):
        return "'" + text
    return text


class _Echo:
    def write(self, value):
        return value


def csv_response(request, name, header, rows):
    """
    StreamingHttpResponse with `header` and up to max_rows() of `rows` (an iterable of lists).
    Records AdminAccessLog `export_csv` with {export: name, rows: n} before streaming.
    """
    from admin_panel.models import AdminAccessLog

    limit = max_rows()
    taken = list(islice(iter(rows), limit + 1))
    truncated = len(taken) > limit
    taken = taken[:limit]
    AdminAccessLog.record(request.user, 'export_csv', details={'export': name, 'rows': len(taken)})

    writer = csv.writer(_Echo())

    def stream():
        yield BOM + writer.writerow([safe_cell(cell) for cell in header])
        for row in taken:
            yield writer.writerow([safe_cell(cell) for cell in row])
        if truncated:
            yield writer.writerow([TRUNCATED])

    response = StreamingHttpResponse(stream(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{name}.csv"'
    return response


def money_cell(entries):
    """[{'currency', 'amount'}] -> 'UZS 1000000.00; USD 70.00'."""
    return '; '.join(f"{entry['currency']} {entry['amount']}" for entry in entries)
