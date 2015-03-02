# -*- coding: utf-8 -*-

import random
from openerp import api, fields, models
from openerp.addons.base_geolocalize.models.res_partner import geo_find, geo_query_address


class ResPartnerGrade(models.Model):
    _order = 'sequence'
    _name = 'res.partner.grade'

    sequence = fields.Integer()
    active = fields.Boolean(default=True)
    name = fields.Char(string='Grade Name')
    partner_weight = fields.Integer(string='Grade Weight',
                                    default=True,
                                    help="Gives the probability to assign a lead to this partner. (0 means no assignation.)")


class ResPartnerActivation(models.Model):
    _name = 'res.partner.activation'
    _order = 'sequence'

    sequence = fields.Integer()
    name = fields.Char(required=True)


class ResPartner(models.Model):
    _inherit = "res.partner"

    partner_weight = fields.Integer(string='Grade Weight', default=0,
        help="Gives the probability to assign a lead to this partner. (0 means no assignation.)")
    grade_id = fields.Many2one('res.partner.grade', string='Grade')
    activation = fields.Many2one('res.partner.activation', index=True)
    date_partnership = fields.Date(string='Partnership Date')
    date_review = fields.Date(string='Latest Partner Review')
    date_review_next = fields.Date(string='Next Partner Review')
    # customer implementation
    assigned_partner_id = fields.Many2one('res.partner', string='Implemented by')
    implemented_partner_ids = fields.One2many('res.partner', 'assigned_partner_id',
                                              string='Implementation References')

    @api.onchange('grade_id')
    def onchange_grade_id(self):
        self.partner_weight = self.grade_id.partner_weight


class CrmLead(models.Model):
    _inherit = "crm.lead"

    partner_latitude = fields.Float(string='Geo Latitude', digits=(16, 5))
    partner_longitude = fields.Float(string='Geo Longitude', digits=(16, 5))
    partner_assigned_id = fields.Many2one('res.partner', string='Assigned Partner',
                                          track_visibility='onchange',
                                          index=True,
                                          help="Partner this case has been forwarded/assigned to.")
    date_assign = fields.Date(string='Assignation Date',
                              help="Last date this case was forwarded/assigned to a partner")

    @api.model
    def _merge_data(self, oldest, fields):
        fields += ['partner_latitude', 'partner_longitude',
                   'partner_assigned_id', 'date_assign']
        return super(CrmLead, self)._merge_data(oldest, fields)

    @api.onchange('partner_assigned_id')
    def onchange_assign_id(self):
        """This function updates the "assignation date" automatically,
           when manually assign a partner in the geo assign tab"""
        if not self.partner_assigned_id:
            self.date_assign = False
        else:
            partners = self.env['res.partner'].browse(self.partner_assigned_id.id)
            self.date_assign = fields.Date.context_today(self)
            self.user_id = partners and partners.user_id.id or False

    @api.multi
    def action_assign_partner(self):
        return self.assign_partner(partner_id=False)

    def assign_partner(self, partner_id=False):
        partner_ids = {}
        res = False
        ResPartner = self.env['res.partner']
        if not partner_id:
            partner_ids = self.search_geo_partner()
        for lead in self:
            if not partner_id:
                partner_id = partner_ids.get(lead.id, False)
            if not partner_id:
                continue
            self.assign_geo_localize(lead.partner_latitude, lead.partner_longitude)
            partner = ResPartner.browse(partner_id)
            if partner.user_id:
                salesteam_id = partner.team_id and partner.team_id.id or False
                for lead_id in self.ids:
                    self.allocate_salesman(
                        [lead_id], [partner.user_id.id], team_id=salesteam_id)

            self.browse(lead.id).write({
                'date_assign': fields.Date.context_today(self),
                'partner_assigned_id': partner_id})
        return res

    def assign_geo_localize(self, latitude=False, longitude=False):
        if latitude and longitude:
            self.write({
                'partner_latitude': latitude,
                'partner_longitude': longitude
            })
        for lead in self:
            if lead.partner_latitude and lead.partner_longitude:
                continue
            if lead.country_id:
                result = geo_find(geo_query_address(street=lead.street,
                                                    zip=lead.zip,
                                                    city=lead.city,
                                                    state=lead.state_id.name,
                                                    country=lead.country_id.name))
                if result:
                    self.browse(lead.id).write({
                        'partner_latitude': result[0],
                        'partner_longitude': result[1]
                    })

    def search_geo_partner(self):
        ResPartner = self.env['res.partner']
        res_partner_ids = {}
        self.assign_geo_localize()
        for lead in self:
            if not lead.country_id:
                continue
            latitude = lead.partner_latitude
            longitude = lead.partner_longitude
            if latitude and longitude:
                # 1. first way: in the same country, small area
                Partners = ResPartner.search([
                    ('partner_weight', '>', 0),
                    ('partner_latitude', '>', latitude - 2),
                    ('partner_latitude', '<', latitude + 2),
                    ('partner_longitude', '>', longitude - 1.5),
                    ('partner_longitude', '<', longitude + 1.5),
                    ('country_id', '=', lead.country_id.id),
                ])

                # 2. second way: in the same country, big area
                if not Partners:
                    Partners = ResPartner.search([
                        ('partner_weight', '>', 0),
                        ('partner_latitude', '>', latitude - 4),
                        ('partner_latitude', '<', latitude + 4),
                        ('partner_longitude', '>', longitude - 3),
                        ('partner_longitude', '<', longitude + 3),
                        ('country_id', '=', lead.country_id.id),
                    ])

                # 3. third way: in the same country, extra large area
                if not Partners:
                    Partners = ResPartner.search([
                        ('partner_weight', '>', 0),
                        ('partner_latitude', '>', latitude - 8),
                        ('partner_latitude', '<', latitude + 8),
                        ('partner_longitude', '>', longitude - 8),
                        ('partner_longitude', '<', longitude + 8),
                        ('country_id', '=', lead.country_id.id),
                    ])

                # 5. fifth way: anywhere in same country
                if not Partners:
                    # still haven't found any, let's take all partners in the
                    # country!
                    Partners = ResPartner.search([
                        ('partner_weight', '>', 0),
                        ('country_id', '=', lead.country_id.id),
                    ])

                # 6. sixth way: closest partner whatsoever, just to have at
                # least one result
                if not Partners:
                    # warning: point() type takes (longitude, latitude) as
                    # parameters in this order!
                    self.env.cr.execute("""SELECT id, distance
                                  FROM  (select id, (point(partner_longitude, partner_latitude) <-> point(%s,%s)) AS distance FROM res_partner
                                  WHERE partner_longitude is not null
                                        AND partner_latitude is not null
                                        AND partner_weight > 0) AS d
                                  ORDER BY distance LIMIT 1""", (longitude, latitude))
                    res = self.env.cr.dictfetchone()
                    if res:
                        Partners = Partners + ResPartner.browse(res['id'])

                total_weight = 0
                toassign = []
                for partner in Partners:
                    total_weight += partner.partner_weight
                    toassign.append((partner.id, total_weight))

                # avoid always giving the leads to the first ones in db natural
                # order!
                random.shuffle(toassign)
                nearest_weight = random.randint(0, total_weight)
                for partner_id, weight in toassign:
                    if nearest_weight <= weight:
                        res_partner_ids[lead.id] = partner_id
                        break
        return res_partner_ids
