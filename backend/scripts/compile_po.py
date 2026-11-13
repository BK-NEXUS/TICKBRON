"""
Proekttiń awdarma derekleri (locale/<til>/LC_MESSAGES/django.po) django.mo ǵa kompilyaciyalaw.

Build mashinalarında GNU gettext (msgfmt) joq, sol sebepli bul proekt paydalanatuǵın ápiwayı jazbalar ushın
(kóplik hám kontekst joq) sol jumıstı isleydi. .po faylın ózgertkennen keyin isletiń:

    python scripts/compile_po.py
"""
import array
import ast
import struct
import sys
from pathlib import Path

LOCALE = Path(__file__).resolve().parents[1] / 'locale'
MAGIC = 0x950412DE


def read_po(path):
    """.po fayldıń {msgid: msgstr} i; header bos msgid li jazba."""
    entries, msgid, msgstr, target = {}, None, None, None
    for raw in Path(path).read_text(encoding='utf-8').splitlines() + ['']:
        line = raw.strip()
        if line.startswith('#'):
            continue
        if line.startswith('msgid '):
            if msgid is not None:
                entries[msgid] = msgstr
            msgid, msgstr, target = ast.literal_eval(line[6:]), '', 'id'
        elif line.startswith('msgstr '):
            msgstr, target = ast.literal_eval(line[7:]), 'str'
        elif line.startswith('"'):
            piece = ast.literal_eval(line)
            if target == 'id':
                msgid += piece
            else:
                msgstr += piece
    if msgid is not None:
        entries[msgid] = msgstr
    return entries


def compile_po(path):
    """.po fayl ushın .mo fayldıń baytları (jazbalar msgid boyınsha tártiplengen, msgfmt jazǵanday)."""
    entries = {key: value for key, value in read_po(path).items() if value or key == ''}
    keys = sorted(entries)
    ids = strs = b''
    offsets = []
    for key in keys:
        encoded_key, encoded_value = key.encode('utf-8'), entries[key].encode('utf-8')
        offsets.append((len(ids), len(encoded_key), len(strs), len(encoded_value)))
        ids += encoded_key + b'\0'
        strs += encoded_value + b'\0'
    header_size = 7 * 4
    table_size = len(keys) * 8
    keys_start = header_size + 2 * table_size
    values_start = keys_start + len(ids)
    key_table, value_table = [], []
    for id_offset, id_length, str_offset, str_length in offsets:
        key_table += [id_length, id_offset + keys_start]
        value_table += [str_length, str_offset + values_start]
    output = struct.pack('Iiiiiii', MAGIC, 0, len(keys), header_size, header_size + table_size, 0, 0)
    output += array.array('i', key_table + value_table).tobytes()
    return output + ids + strs


def main():
    for po in sorted(LOCALE.glob('*/LC_MESSAGES/django.po')):
        po.with_suffix('.mo').write_bytes(compile_po(po))
        print(f'compiled {po.relative_to(LOCALE.parent)}')


if __name__ == '__main__':
    sys.exit(main())
