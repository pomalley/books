''' The, uh, API of the books app. '''

import datetime

import bson
from mongokit import Document

from flask import abort, render_template, url_for, redirect
from flask.ext.classy import FlaskView
from flask_wtf import Form
import wtforms, wtforms.validators as validators
from wtforms.validators import DataRequired

from books import connection, collection

@connection.register
class Book(Document):
    __collection__ = 'books'
    __database__ = 'books'

    structure = {
        'title': unicode,
        'author': [unicode],
        'year': int,
        'ISBN': int,
        'subjects': [unicode],
        'genre': [unicode],

        'read': bool,
        'want_to_read': bool,
        'owned': bool,
        'want_to_own': bool,
        'date_read': datetime.datetime,
        # 'year','month','day' -- display as "2005" vs "June 2005", etc.
        'date_read_specificity': unicode,

        'date_created': datetime.datetime,
        'date_updated': datetime.datetime,
    }
    required_fields = ['title', 'author', 'date_created',
                       'date_updated']
    default_values = {
        'read': False,
        'date_created': datetime.datetime.utcnow,
        'date_updated': datetime.datetime.utcnow,
        'date_read_specificity': u'month',
    }
    use_dot_notation = True

    def __repr__(self):
        return "<Book %r>" % (self.title)

def find_or_404(id):
    try:
        id = bson.ObjectId(id)
    except bson.errors.InvalidId:
        id = id
    book = connection.Book.find_one(id)
    if not book:
        abort(404)
    return book


class BooksView(FlaskView):
    def index(self):
        return render_template('books.html',
                               book_list = collection.Book.find())

    def get(self, id):
        book = find_or_404(id)
        return render_template('books_single.html', book=book)

    def edit(self, id):
        book = find_or_404(id)
        form = BookForm()
        return render_template('books_edit.html', book=book, form=form)

    def put(self, id):
        book = find_or_404(id)
        form = BookForm()
        if form.validate_on_submit():
            form.populate_obj(book)
            book.save()
            return redirect(url_for("BooksView:get", id=book._id))
        else:
            # TODO: include form errors
            #return redirect(url_for("BooksView:edit", id=book._id))
            return render_template('books_edit.html', book=book,
                                   form=form, method="PUT")

    def new(self, form=None):
        book = connection.Book()
        if not form:
            form = BookForm()
        return render_template('books_edit.html', book=book, form=form)

    def post(self):
        book = connection.Book()
        form = BookForm()
        if form.validate_on_submit():
            form.populate_obj(book)
            book.save()
            return redirect(url_for("BooksView:get", id=book._id))
        else:
            # TODO: include form errors
            #return redirect(url_for("BooksView:new", form=form))
            return render_template('books_edit.html', book=book, form=form)

    def wutwut(self):
        return "wut wut yourself!"

class BookForm(Form):
    title = wtforms.TextField('Title',
                              validators=[validators.InputRequired()])
    author = wtforms.FieldList(wtforms.TextField('Author',
                               validators=[validators.InputRequired()]),
                               min_entries=1)
    year = wtforms.IntegerField('Year',
                               validators=[validators.Optional()])
    isbn = wtforms.IntegerField('ISBN',
                               validators=[validators.Optional()])
    genre = wtforms.FieldList(wtforms.TextField('Genre'),
                              min_entries=1)
    subjects = wtforms.FieldList(wtforms.TextField('Subjects'),
                                 min_entries=1)
    read = wtforms.BooleanField('Read')
    want_to_read = wtforms.BooleanField("Want to read")
    owned = wtforms.BooleanField('Owned')
    want_to_own = wtforms.BooleanField('Want to own')
    date_read = wtforms.DateField('Date read',
                               validators=[validators.Optional()])



