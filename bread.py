'''

bread.py

implementation of model.Model for bread/baking tracker.

'''

import datetime
import wtforms

from books import connection
import model, view_helpers

@connection.register
class Bread(model.Model):
    __collection__ = 'bread'
    # rename the db to something more general at some point
    __database__ = 'books'

    use_schemaless = False
    #use_schemaless = True
    view_decorators = [view_helpers.login_required]

    structure = {
        'starter_hydration_percent': int,
        'starter_mass': int,
        'sponge_white_mass': int,
        'sponge_whole_wheat_mass': int,
        'sponge_water_mass': int,
        'dough_white_mass': int,
        'dough_whole_wheat_mass': int,
        'dough_water_mass': int,
        'dough_salt_mass': int,
        'other_ingredients': unicode,
        'preparation_comments': unicode,
        'rating': int,
        'final_comments': unicode,
        'date': model.Date(),
    }
    structure.update(model.Model.structure)

    default_values = {
        'starter_hydration_percent': 50,
        'starter_mass': 56,
        'sponge_white_mass': 227,
        'sponge_whole_wheat_mass': 0,
        'sponge_water_mass': 142,
        'dough_white_mass': 567,
        'dough_whole_wheat_mass': 0,
        'dough_water_mass': 400,
        'dough_salt_mass': 18,
    }
    default_values.update(model.Model.default_values)

    form_fields = {
        'preparation_comments': [wtforms.TextAreaField, 'Preparation Comments'],
        'other_ingredients': [wtforms.TextAreaField, 'Other Ingredients'],
        'final_comments': [wtforms.TextAreaField, 'Final Comments'],
    }

    form_validators = {
        'rating': [wtforms.validators.NumberRange(min=0, max=10)],
    }
    form_validators.update(model.Model.form_validators)

    field_order = ['date',
        'starter_hydration_percent',
        'starter_mass',
        'sponge_white_mass',
        'sponge_whole_wheat_mass',
        'sponge_water_mass',
        'dough_white_mass',
        'dough_whole_wheat_mass',
        'dough_water_mass',
        'dough_salt_mass',
        'other_ingredients',
        'preparation_comments',
        'rating',
        'final_comments',
    ]

    def __repr__(self):
        return "<%s %r>" % (self.__class__.__name__, self['_id'])

    def get_name(self):
        return "Bread: %s" % self['date']
