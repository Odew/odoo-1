# -*- coding: utf-8 -*-

from openerp import api, fields, models


class HrJob(models.Model):
    _name = 'hr.job'
    _inherit = ['hr.job', 'website.seo.metadata', 'website.published.mixin']

    @api.multi
    def _website_url(self, field_name, arg):
        res = super(HrJob, self)._website_url(field_name, arg)
        res.update({(job.id, "/jobs/detail/%s" % (job.id)) for job in self})
        return res

    @api.multi
    def set_open(self):
        self.write({'website_published': False})
        return super(HrJob, self).set_open()

    website_description = fields.Html(translate=True)
