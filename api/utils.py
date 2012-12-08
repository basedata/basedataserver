# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from datetime import datetime
import base64
import re


def normalize_sha1(s):
    if len(s) == 40:
        s = base64.b32encode(s.decode('hex'))
    s = s.upper()
    assert len(s) == 32
    return s

def normalize_md5(s):
    s = s.lower()
    assert len(s) == 32
    return s

def normalize_oshash(s):
    s = s.lower()
    assert len(s) == 16
    return s

def check_isbn10(isbn):
    try:
        digits = map(int, isbn[:9])
        products = [(i+1)*digits[i] for i in range(9)]
        check = sum(products)%11
        if (check == 10 and isbn[9] == 'X') or check == int(isbn[9]):
            return isbn
    except:
        pass
    return None

def check_isbn13(isbn):
    try:
        digits = map(int, isbn[:12])
        products = [(1 if i%2 ==0 else 3)*digits[i] for i in range(12)]
        check = 10 - (sum(products)%10)
        if check == 10:
            check = 0
        if str(check) == isbn[12]:
            return isbn
    except:
        pass
    return None

def check_isbn(isbn):
    if not isbn:
        return None
    isbn = re.sub(r'[^0-9X]', '', isbn.upper())
    all_same = re.match(r'(\d)\1{9,12}$', isbn)
    if all_same is not None:
        return None
    if len(isbn) == 10:
        return check_isbn10(isbn)
    if len(isbn) == 13:
        return check_isbn13(isbn)
    return None

def check_openlibrary(value):
    if not value:
        return None
    if value.startswith('OL'):
        return value
    return None
