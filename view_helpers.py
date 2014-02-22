''' view_helpers.py

misc helpers for view functions.
'''

import functools
from flask import redirect, url_for, request, g

def login_required(f):
    @functools.wraps(f)
    def func(*args, **kwargs):
        if g.get('user', None) is None:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return func
