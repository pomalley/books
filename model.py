''' model.py

Basic flask-classy / mongokit / wtforms model.

Usage:
Create a class inheriting from Model.
Define class values per mongokit model (structure, required_fields,
default_values).
For additional wtforms functionality, update the following:
    formless_fields: list of field names not to be displayed (e.g.
                     created_date, updated_date)
    field_choices: dict of field_name: [(name, value), (name, value)...]
                   these field will become select fields.
    field_order: list of fields: order to display
    default_on_save: use the default value/function on save. e.g.
        date_updated has utcnow as default, so use that on every save.


'''

import bson, simplejson
import datetime
import mongokit
from flask.ext.classy import FlaskView, route
from flask import abort, render_template, url_for, redirect, request, jsonify, json, flash
from flask_wtf import Form
import wtforms, wtforms.validators as validators

# TODO: figure out proper way to get connection
from books import connection

def prune(l):
    if isinstance(l, list):
        return [prune(x) for x in l if prune(x)]
    elif isinstance(l, dict):
        return {prune(k): prune(v) for k, v in l.items() if prune(k) and prune(v)}
    else:
        return l

class MonthDate(mongokit.CustomType):
    mongo_type = unicode
    python_type = datetime.date
    def to_bson(self, value):
        if value:
            return unicode(value.strftime("%Y-%m"))
    def to_python(self, value):
        if value is not None:
            y, _, m = value.partition('-')
            return datetime.date(int(y), int(m), 15)

class MonthDateField(wtforms.DateField):
    def _value(self):
        if self.data:
            return u'%04d-%02d' % (self.data.year, self.data.month)
        else:
            return u''
    def process_formdata(self, valuelist):
        if valuelist:
            value = ' '.join(valuelist)
            try:
                y, _, m = value.partition('-')
                self.data = datetime.date(int(y), int(m), 15)
            except ValueError:
                self.data = None
                raise ValueError(self.gettext('Must have format yyyy-mm.'))

class DeleteForm(Form):
    id = wtforms.HiddenField('id')

fieldMap = {
    unicode:            wtforms.TextField,
    int:                wtforms.IntegerField,
    bool:               wtforms.BooleanField,
    datetime.datetime:  wtforms.DateTimeField,
    MonthDate:          MonthDateField,
}

class Model(mongokit.Document):
    ''' Base class for other documents. '''
    # presumably here the user puts
    # structure = {}
    # required_fields = {}
    # default_values = {}
    # use_dot_notation = True/False
    # etc...
    structure = {
        'date_created': datetime.datetime,
        'date_updated': datetime.datetime,
    }
    default_values = {
        'date_created': datetime.datetime.utcnow,
        'date_updated': datetime.datetime.utcnow,
    }
    formless_fields = ['date_created', 'date_updated']
    field_choices = {}
    field_order = []
    default_on_save = ['date_updated']
    form_fields = {}

    view_decorators = []

    def __repr__(self):
        return "<%s %r>" % (self.__class__.__name__, self.title)

    @classmethod
    def find_or_404(cls, id):
        try:
            id = bson.ObjectId(id)
        except bson.errors.InvalidId:
            id = id
        doc = getattr(connection, cls.__name__).one({"_id": id})
        if not doc:
            abort(404)
        return doc

    @staticmethod
    def label_for(name):
        label = name.replace('_', ' ')
        label = label[0].upper() + label[1:]
        return label

    @classmethod
    def viewName(cls):
        return cls.__name__ + 'View'

    @classmethod
    def views(cls):
        ''' Override in subclases to return a list of additional view
        functions.
        '''
        return []

    @classmethod
    def getView(cls):
        ''' Returns a FlaskView subclass.
        To be used as: cls.register(app)
        The name of the class will be [model class name]View '''
        name = cls.__name__
        viewName = name + "View"    # must == viewName method above
        class MyView(FlaskView):
            decorators = cls.view_decorators
            def index(self):
                doclist = getattr(connection, name).find()
                return render_template(name + '/index.html',
                                       doclist=doclist)
            def get(self, id):
                doc = cls.find_or_404(id)
                return render_template(name + '/get.html', doc=doc)

            def edit(self, id):
                doc = cls.find_or_404(id)
                form = doc.getForm()
                if form.validate_on_submit() and not ('btn' in request.form
                            and request.form['btn'].startswith("Add")):
                    doc._from_form(form)
                    doc.save()
                    return redirect(doc.url_for())
                elif 'btn' in request.form and request.form['btn'].startswith("Add"):
                    fname = request.form['btn'][4:]
                    form[fname].append_entry()
                return render_template(name + '/edit.html', doc=doc,
                                    form=form)
            edit.methods=['GET', 'POST']

            def patch(self, id):
                data = request.get_json()
                doc = cls.find_or_404(id)
                doc._from_json(data)
                doc.save()
                return jsonify()

            def delete(self, id):
                doc = cls.find_or_404(id)
                doc.delete()
                flash("Deleted: %s" % doc['title'])
                return redirect(cls.class_url())

            @route("/delete/<id>", methods=["POST"])
            def post_delete(self, id):
                ''' for use in browsers, calls DELETE method '''
                form = DeleteForm()
                doc = cls.find_or_404(id)
                if form.validate_on_submit() and form.data['id'] == str(doc._id):
                    return self.delete(id)
                else:
                    flash("delete failed")
                    return redirect(doc.url_for())

            def new(self):
                doc = getattr(connection, name)()
                form = doc.getForm()
                url = url_for('%s:post' % viewName)
                return render_template(name + '/edit.html', doc=doc,
                                       form=form, action=url)

            def post(self):
                doc = getattr(connection, name)()
                form = doc.getForm()
                if form.validate_on_submit():
                    doc._from_form(form)
                    doc.save()
                    url = url_for("%s:get" % viewName, id=doc._id)
                    return redirect(url)
                else:
                    return render_template(name + '/edit.html',
                                           doc=doc, form=form)
        MyView.__name__ = viewName
        for f in cls.views():
            setattr(MyView, f.func_name, f)
        return MyView

    def _subform(self, name, field_types, values=None):
        class SubForm(Form):
            pass
        SubForm.__name__ = name + 'Form'
        for n, t in field_types.items():
            field = fieldMap[t](self.label_for(n))
            setattr(SubForm, n, field)
        return SubForm

    def _getField(self, name, field_type, value=None):
        if name in self.form_fields:
            return self.form_fields[name]
        label = self.label_for(name)
        if isinstance(field_type, list):
            subfield = self._getField(name, field_type[0])
            field = wtforms.FieldList(subfield, min_entries=1)
            return field
        elif isinstance(field_type, dict):
            subform = self._subform(name, field_type, value)
            field = wtforms.FormField(subform)
            return field
        else:
            kwargs = {}
            if name in self.field_choices:
                field_type = wtforms.SelectField
                kwargs['choices'] = self.field_choices[name]
            else:
                if field_type in fieldMap:
                    field_type = fieldMap[field_type]
                else:
                    field_type = fieldMap[type(field_type)]
            field_vals = []
            if name in self.required_fields:
                field_vals.append(validators.DataRequired())
            else:
                field_vals.append(validators.Optional())
            return field_type(label, validators=field_vals, **kwargs)

    def getForm(self, return_class=False, field_list=None):
        ''' Returns a WTForms object for this model.
            e.g. to be passed to a template. '''
        class MyForm(Form):
            pass
        MyForm.__name__ = self.__class__.__name__ + 'Form'
        if field_list:
            l = field_list
        else:
            l = self.field_order + [s for s in self.structure if s not in
                                self.field_order]
            l = [s for s in l if s not in self.formless_fields]
        for s in l:
            field = self._getField(s, self.structure[s])
            setattr(MyForm, s, field)
        if not return_class:
            return MyForm(obj = self)
        else:
            return MyForm

    @classmethod
    def getMultiForm(cls, fields, docs):
        data = {}
        class MultiForm(Form):
            pass
        for d in docs:
            form_class = d.getForm(return_class=True, field_list=fields)
            setattr(MultiForm, str(d._id), wtforms.FormField(form_class))
            data[str(d._id)] = {k: d[k] for k in fields}
        return MultiForm(**data)

    def _from_form(self, form):
        changed=False
        for k, v in form.data.items():
            v = prune(v)
            if k in self.structure and self[k] != v:
                self[k] = v
                changed = True
        return changed

    def _from_json(self, data):
        for k, v in data.items():
            v = prune(v)
            if k in self.structure:
                self[k] = v

    def save(self, *args, **kwargs):
        # lame implementation of pre- and post-save hooks
        for k in self.default_on_save:
            v = self.default_values[k]
            try:
                self[k] = v()
            except TypeError:
                self[k] = v
        super(Model, self).save(*args, **kwargs)

    def delete_form(self):
        self.id = self._id
        form = DeleteForm(obj=self)
        form.action = self.url_for("post_delete")
        return form

    def url_for(self, endpoint=None, **kwargs):
        if endpoint is None:
            return self.url_for("get")
        return url_for("%s:%s" % (self.viewName(), endpoint),
                       id=str(self._id), **kwargs)

    @classmethod
    def class_url(cls, endpoint=None, **kwargs):
        if endpoint is None:
            endpoint = 'index'
        return url_for("%s:%s" % (cls.viewName(), endpoint), **kwargs)

