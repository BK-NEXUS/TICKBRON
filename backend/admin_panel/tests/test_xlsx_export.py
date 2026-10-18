"""
R12 additions slice 3: `?export=xlsx` next to `?export=csv` on every Status export
(same permissions, row limit and audit log).
"""
import io
import zipfile
from xml.etree import ElementTree

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from admin_panel.models import AdminAccessLog
from users.models import User

NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
XLSX_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
S = '/api/v1/admin-panel/status'
P = '/api/v1/partner/status'


def read_xlsx(response):
    """Rows of the first sheet as lists (numbers stay numbers, text stays text) and the raw sheet xml."""
    archive = zipfile.ZipFile(io.BytesIO(response.content))
    strings = []
    if 'xl/sharedStrings.xml' in archive.namelist():
        root = ElementTree.fromstring(archive.read('xl/sharedStrings.xml'))
        strings = [''.join(t.text or '' for t in si.iter('{%s}t' % NS['m'])) for si in root.findall('m:si', NS)]
    sheet_xml = archive.read('xl/worksheets/sheet1.xml')
    rows = []
    for row in ElementTree.fromstring(sheet_xml).iter('{%s}row' % NS['m']):
        values = []
        for cell in row.findall('m:c', NS):
            raw = cell.find('m:v', NS)
            if cell.get('t') == 's':
                values.append(strings[int(raw.text)])
            elif raw is not None:
                values.append(float(raw.text))
        rows.append(values)
    return rows, sheet_xml


@pytest.fixture
def staff(db):
    return User.objects.create_user(email='staff@example.com', password='StaffPassword#123', is_staff=True)


def get_as(user, url, **params):
    client = APIClient()
    client.force_authenticate(user=user)
    return client.get(url, params)


@pytest.mark.django_db
class TestAdminXlsx:

    def test_hotels_list_as_a_spreadsheet(self, staff, status_world):
        response = get_as(staff, f'{S}/hotels/', export='xlsx', ordering='-bookings')
        assert response.status_code == 200
        assert response['Content-Type'] == XLSX_TYPE
        assert response['Content-Disposition'] == 'attachment; filename="status_hotels.xlsx"'
        rows, _ = read_xlsx(response)
        assert rows[0][:3] == ['rank', 'id', 'name']
        assert [row[2] for row in rows[1:]] == ['Alpha Hotel', 'Beta Hotel', 'Delta Hotel', 'Gamma Hotel']
        assert rows[1][-2] == 'USD 450.00'

    def test_it_is_audit_logged_with_its_format(self, staff, status_world):
        get_as(staff, f'{S}/hotels/', export='xlsx')
        log = AdminAccessLog.objects.get(action='export_csv')
        assert (log.actor_id, log.details) == (staff.id, {'export': 'status_hotels', 'rows': 4, 'format': 'xlsx'})

    def test_formulas_stay_text(self, staff, status_world):
        guest = status_world['guests'][0]
        status_world['hotels']['alpha'].translations.filter(language='en').update(name='=HYPERLINK("http://x")')
        response = get_as(staff, f'{S}/users/{guest.id}/', export='xlsx')
        rows, sheet_xml = read_xlsx(response)
        assert {row[3] for row in rows[1:]} == {'=HYPERLINK("http://x")'}
        assert b'<f>' not in sheet_xml

    @override_settings(CSV_EXPORT_MAX_ROWS=1)
    def test_truncated_after_max_rows(self, staff, status_world):
        guest = status_world['guests'][0]
        rows, _ = read_xlsx(get_as(staff, f'{S}/users/{guest.id}/', export='xlsx'))
        assert len(rows) == 3 and rows[-1] == ['truncated']

    def test_a_guest_cannot_export(self, status_world):
        guest = status_world['guests'][0]
        assert get_as(guest, f'{S}/hotels/', export='xlsx').status_code == 403

    def test_unknown_export_value_gives_the_normal_json(self, staff, status_world):
        response = get_as(staff, f'{S}/hotels/', export='pdf')
        assert response.status_code == 200 and 'results' in response.data


@pytest.mark.django_db
class TestPartnerXlsx:

    def test_reconciliation_as_a_spreadsheet(self, status_world):
        owner = status_world['owners'][0]
        response = get_as(owner, f'{P}/', export='xlsx')
        assert response['Content-Type'] == XLSX_TYPE
        assert response['Content-Disposition'] == 'attachment; filename="partner_reconciliation.xlsx"'
        rows, _ = read_xlsx(response)
        assert rows[0][:2] == ['hotel_id', 'hotel']
        assert len(rows) == 1 + 2 * 5
        alpha_all = next(r for r in rows[1:] if r[1] == 'Alpha Hotel' and r[2] == 'all_time')
        assert alpha_all[5:] == [3.0, 3.0, 1.0, 1.0]
        assert AdminAccessLog.objects.get(action='export_csv').details['format'] == 'xlsx'

    def test_other_owners_hotels_are_not_in_it(self, status_world):
        rows, _ = read_xlsx(get_as(status_world['owners'][0], f'{P}/', export='xlsx'))
        assert {r[1] for r in rows[1:]} == {'Alpha Hotel', 'Beta Hotel'}
