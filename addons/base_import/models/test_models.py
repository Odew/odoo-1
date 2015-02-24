# -*- coding: utf-8 -*-
from openerp import fields, models


def name(n):
    return 'base_import.tests.models.%s' % n


class Char(models.Model):
    _name = name('char')

    value = fields.Char()


class CharRequired(models.Model):
    _name = name('char.required')

    value = fields.Char(required=True)


class CharReadonly(models.Model):
    _name = name('char.readonly')

    value = fields.Char(readonly=True)


class CharStates(models.Model):
    _name = name('char.states')

    value = fields.Char(readonly=True, states={'draft': [('readonly', False)]})


class CharNoReadOnly(models.Model):
    _name = name('char.noreadonly')

    value = fields.Char(readonly=True, states={'draft': [('invisible', True)]})


class CharStillReadOnly(models.Model):
    _name = name('char.stillreadonly')

    value = fields.Char(readonly=True, states={'draft': [('readonly', True)]})


# TODO: complex field (m2m, o2m, m2o)
class M2o(models.Model):
    _name = name('m2o')

    value = fields.Many2one(name('m2o.related'))


class M2oRelated(models.Model):
    _name = name('m2o.related')

    value = fields.Integer(defualt=42)


class M2oRequired(models.Model):
    _name = name('m2o.required')

    value = fields.Many2one(name('m2o.required.related'), required=True)


class M2oRequiredRelated(models.Model):
    _name = name('m2o.required.related')

    value = fields.Integer(defualt=42)


class O2m(models.Model):
    _name = name('o2m')

    value = fields.One2many(name('o2m.child'), 'parent_id')


class O2mChild(models.Model):
    _name = name('o2m.child')

    parent_id = fields.Many2one(name('o2m'))
    value = fields.Integer()


class PreviewModel(models.Model):
    _name = name('preview')

    name = fields.Char()
    somevalue = fields.Integer(string='Some Value', required=True)
    othervalue = fields.Integer(string='Other Variable')
