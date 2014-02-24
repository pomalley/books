''' book.py

The book model & view.

'''

import datetime, requests, feedparser, simplejson
import wtforms, wtforms.validators as validators
from flask import url_for, redirect, flash
from books import connection
import model, view_helpers

worldcat_url = "http://worldcat.org/webservices/catalog/search/opensearch"
worldcat_keys = ['author', 'author_detail', 'authors', 'dc_identifier',
                 'link', 'title', 'title_detail', 'summary']
google_url = "https://www.googleapis.com/books/v1/volumes"

class ControlPanelForm(model.Form):
    read = wtforms.BooleanField('Read')
    want_to_read = wtforms.BooleanField('Want to read')
    owned = wtforms.BooleanField('Owned')
    want_to_own = wtforms.BooleanField('Want to own')

class ExtendedControlPanelForm(ControlPanelForm):
    date_read = model.MonthDateField('Date read', validators=[validators.Optional()])
    comments = wtforms.TextAreaField('Comments')

@connection.register
class Book(model.Model):
    __collection__ = 'books'
    __database__ = 'books'
    use_schemaless=True
    view_decorators = [view_helpers.login_required]

    structure = {
        'title': unicode,
        'authors': [unicode],
        'author_string': unicode,
        'year': int,
        'identifiers': [{'type': unicode, 'identifier': unicode}],
        'subjects': [unicode],
        'genre': [unicode],

        'read': bool,
        'want_to_read': bool,
        'owned': bool,
        'want_to_own': bool,
        'comments': unicode,
        'date_read': model.MonthDate(),

        'date_created': datetime.datetime,
        'date_updated': datetime.datetime,

        'worldcat_entries': [dict],
        'google_volumes': [dict],
    }
    required_fields = ['title', 'date_created',
                       'date_updated']
    default_values = {
        'read': False,
        'want_to_read': True,
        'owned': False,
        'want_to_own': False,
        'date_created': datetime.datetime.utcnow,
        'date_updated': datetime.datetime.utcnow,
    }

    field_choices = {
    }

    form_fields = {
        'comments': wtforms.TextAreaField('Comments'),
    }

    field_order = ['title', 'authors', 'year', 'genre', 'subjects',
                   'identifiers', 'owned', 'want_to_own','read',
                   'want_to_read', 'date_read', 'comments', 'date_created',
                   'date_updated', 'author_string']

    formless_fields = model.Model.formless_fields + ['worldcat_entries',
                      'google_volumes', 'read', 'want_to_read', 'owned',
                      'want_to_own', 'comments', 'date_read',
                      'author_string']

    use_dot_notation = True

    @classmethod
    def views(cls):
        ''' Additional views for Book: get_info, set_info '''
        name = cls.__name__
        index_form_fields = ['read', 'want_to_read', 'owned',
                             'want_to_own']

        def get_info(self, id):
            doc = cls.find_or_404(id)
            redo = model.request.args.get('redo', '')
            if ('google_volumes' not in doc or
                not doc['google_volumes'] or redo):
                query = "intitle:%s" % doc['title']
                for a in doc['authors']:
                    if a and a != 'unknown' and a != '?':
                        query += '+inauthor:%s' % a
                params = {'q': query}
                r = requests.get(google_url, params=params)
                j = simplejson.loads(r.text)
                doc['google_volumes'] = []
                if j['totalItems']:
                    for v in j['items']:
                        doc.google_volumes.append(v['volumeInfo'])
                doc.save()
            return model.render_template(name + '/get_info.html', doc=doc)

        def set_info(self, id):
            ''' Set the author, title, etc to values from worldcat. '''
            doc = cls.find_or_404(id)
            try:
                idx = int(model.request.form['idx'])
            except ValueError:
                return self.get_info(id)
            if ('google_volumes' not in doc or
                not doc['google_volumes'] or
                len(doc['google_volumes']) <= idx):
                return self.get_info(id)
            entry = doc['google_volumes'][idx]
            mine = ['authors', 'title', 'identifiers', 'genre', 'imageLinks', 'year']
            theirs = ['authors', 'title', 'industryIdentifiers', 'categories', 'imageLinks', 'publishedDate']
            for m, t in zip(mine, theirs):
                if t in entry:
                    doc[m] = entry[t]
            doc['google_volumes_idx'] = idx
            try:
                doc['year'] = int(doc['year'][:4])
            except ValueError:
                del doc['year']
            doc.save()
            return model.redirect(doc.url_for())
        set_info.methods=['POST']

        def control_panel(self, id):
            ''' update from the control panel '''
            doc = cls.find_or_404(id)
            form = ControlPanelForm()
            if form.validate_on_submit():
                doc._from_form(form)
                doc.save()
            return model.redirect(doc.url_for())
        control_panel.methods=['POST']

        def get(self, id):
            doc = cls.find_or_404(id)
            control_panel = ControlPanelForm(obj=doc)
            return model.render_template(name + '/get.html', doc=doc,
                                    form=control_panel)

        def update(self, id):
            ''' update user info '''
            doc = cls.find_or_404(id)
            form = ExtendedControlPanelForm(obj=doc)
            if form.validate_on_submit():
                doc._from_form(form)
                doc.save()
                return model.redirect(doc.url_for())
            else:
                url = doc.url_for('update')
                return model.render_template(name + '/update.html', doc=doc,
                                        form=form, url=url)
        update.methods=['GET', 'POST']

        def index(self):
            doclist = list(getattr(connection, name).find())
            form = cls.getMultiForm(index_form_fields, doclist)
            form.subforms = [form._fields[str(x._id)] for x in doclist]
            url = url_for('%s:%s' % (cls.viewName(), 'index_form_post'))
            return model.render_template(name+'/index.html',
                                         doclist=doclist, form=form,
                                         url=url)
        index.methods=['GET']

        def index_form_post(self):
            ''' receives a form with select fields from all books. '''
            doclist = list(getattr(connection, name).find())
            form = cls.getMultiForm(index_form_fields, doclist)
            count = 0
            if form.validate_on_submit():
                for doc in doclist:
                    if doc._from_form(form._fields[str(doc._id)]):
                        doc.save()
                        count += 1
                flash('%d book%s updated' % (count, 's' if count != 1 else ''))
            else:
                flash('invalid form')
            return redirect(url_for('%s:index' % cls.viewName()))
        index_form_post.methods=['POST']

        def library_list(self):
            ''' displays list of books to look for in the library. '''
            q = {"want_to_read": True, "owned": False}
            cursor = getattr(connection, name).find(q)
            doclist = list(cursor.sort(u'author_string', 1))
            return model.render_template(name+'/mini-index.html',
                                title="Library List", doclist=doclist)

        def bookstore_list(self):
            ''' displays list of books to look for in a bookstore '''
            q = {"want_to_own": True, "owned": False}
            cursor = getattr(connection, name).find(q)
            doclist = list(cursor.sort(u'author_string', 1))
            return model.render_template(name+'/mini-index.html',
                                title="Bookstore List", doclist=doclist)



        return [get, get_info, set_info, control_panel, update, index,
                index_form_post, library_list, bookstore_list]

    def get_citation(self, use_author_string=False):
        if 'authors' not in self:
            self['authors'] = []
            self['author_string'] = ''
        if use_author_string:
            s = self['author_string'] + '. '
        else:
            if len(self['authors']) > 1:
                s = ', '.join(self['authors'][:-1])
                s += ', and %s. ' % self['authors'][-1]
            elif self['authors']:
                s = '%s. ' % self['authors'][0]
            else:
                s = ''
        s += '<i>%s</i>' % self['title']
        if self['year']:
            s += ' (%s)' % self['year']
        return s

    def _make_author_string(self):
        ''' string the author names together, last name first. '''
        s = ''
        names = []
        for a in self['authors']:
            if ',' in a:
                names.append(a)
            else:
                first, _, last = a.rpartition(' ')
                names.append('%s, %s' % (last, first))
        return unicode(';'.join(names))

    def save(self, *args, **kwargs):
        # update the author string
        self['author_string'] = self._make_author_string()
        super(Book, self).save(*args, **kwargs)


''' old stuff: from set_info, for worldcat stuff
if ('worldcat_entries' not in doc or
    not doc['worldcat_entries'] or redo):
    query = doc['title']
    for a in doc['author']:
        if a and a != 'unknown' and a != '?':
            query += ' %s' % a
    params = {'format': 'atom', 'cformat': 'mla',
              'wskey': app.worldcat_key, 'q': query}
    r = requests.get(worldcat_url, params=params)
    f = feedparser.parse(r.text)
    l = []
    for e in f.entries:
        l.append({x: e[x] for x in worldcat_keys if x in e})
    doc['worldcat_entries'] = l
    doc.save()
'''
