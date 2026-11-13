"""
Status bólimleri ushın CSV hám Excel eksport (R12 2-basqısh): dizim endpoint inde `?export=csv` yamasa `?export=xlsx`
(`export_response` formattı tańlaydı; basqa mánis ádettegi JSON beredi).

BOM menen UTF-8 (Excel Kirill hám ózbek tekstin durıs ashadı), aǵım menen, eń kóbi
CSV_EXPORT_MAX_ROWS maǵlıwmat qatarı, kóbi bolsa aqırında "truncated" qatarı.
Elektron kestede formula retinde isleytuǵın (= + - @, tab yamasa CR den baslanatuǵın) kataklar
aldına apostrof alıp turadı; Excel fayllarında hár tekst tekst retinde jazıladı, sol sebepli hesh nárse formula bolıp
islemeydi.
Hár eksport admin kirisiw logına jazıladı (`export_csv`, eksport atı, qatar sanı hám Excel
ushın `format: xlsx`).
"""
import csv
import io
from decimal import Decimal
from itertools import islice

from django.conf import settings
from django.http import HttpResponse, StreamingHttpResponse
from xlsxwriter import Workbook

BOM = '﻿'
TRUNCATED = 'truncated'
_FORMULA_START = ('=', '+', '-', '@', '\t', '\r')


XLSX_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


def export_format(request):
    """'csv', 'xlsx' yamasa None."""
    value = (request.query_params.get('export') or '').strip().lower()
    return value if value in ('csv', 'xlsx') else None


def wants_export(request):
    return export_format(request) is not None


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


def export_response(request, name, header, rows):
    """
    `?export=` ke qarap CSV yamasa Excel fayl, `header` hám max_rows() ke shekem `rows` (list lerdiń iterable ı) menen.
    Jiberiwden aldın AdminAccessLog `export_csv` di {export: name, rows: n} (+ Excel ushın format) menen jazadı.
    """
    from admin_panel.models import AdminAccessLog

    limit = max_rows()
    taken = list(islice(iter(rows), limit + 1))
    truncated = len(taken) > limit
    taken = taken[:limit]
    fmt = export_format(request)
    details = {'export': name, 'rows': len(taken)} | ({'format': 'xlsx'} if fmt == 'xlsx' else {})
    AdminAccessLog.record(request.user, 'export_csv', details=details)
    if fmt == 'xlsx':
        return _xlsx_response(name, header, taken, truncated)
    return _csv_response(name, header, taken, truncated)


def _csv_response(name, header, taken, truncated):
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


def _xlsx_response(name, header, taken, truncated):
    buffer = io.BytesIO()
    workbook = Workbook(buffer, {'in_memory': True})
    sheet = workbook.add_worksheet()
    lines = [header, *taken] + ([[TRUNCATED]] if truncated else [])
    for row_number, line in enumerate(lines):
        for column, value in enumerate(line):
            if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
                sheet.write_number(row_number, column, float(value))
            else:
                sheet.write_string(row_number, column, '' if value is None else str(value))
    workbook.close()
    response = HttpResponse(buffer.getvalue(), content_type=XLSX_TYPE)
    response['Content-Disposition'] = f'attachment; filename="{name}.xlsx"'
    return response


def money_cell(entries):
    """[{'currency', 'amount'}] -> 'UZS 1000000.00; USD 70.00'."""
    return '; '.join(f"{entry['currency']} {entry['amount']}" for entry in entries)
