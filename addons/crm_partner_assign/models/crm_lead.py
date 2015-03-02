# -*- coding: utf-8 -*-

from openerp import _, api, models
from openerp.exceptions import UserError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    @api.v7
    def get_interested_action(self, cr, uid, interested, context=None):
        try:
            model, action_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'crm_partner_assign', 'crm_lead_channel_interested_act')
        except ValueError:
            raise UserError(_("The CRM Channel Interested Action is missing"))
        action = self.pool[model].read(cr, uid, [action_id], context=context)[0]
        action_context = eval(action['context'])
        action_context['interested'] = interested
        action['context'] = str(action_context)
        return action

    @api.v8
    def get_interested_action(self, interested):
        try:
            LeadChannelAct = self.env.ref('crm_partner_assign.crm_lead_channel_interested_act')
        except ValueError:
            raise UserError(_("The CRM Channel Interested Action is missing"))
        action = self.env[LeadChannelAct._model].read([LeadChannelAct.id])
        action_context = eval(action['context'])
        action_context['interested'] = interested
        action['context'] = str(action_context)
        return action

    @api.v7
    def case_interested(self, cr, uid, ids, context=None):
        return self.get_interested_action(cr, uid, True, context=context)

    @api.v8
    def case_interested(self):
        return self.get_interested_action(True)

    @api.v7
    def case_disinterested(self, cr, uid, ids, context=None):
        return self.get_interested_action(cr, uid, False, context=context)

    @api.v8
    def case_disinterested(self):
        return self.get_interested_action(False)

    @api.v7
    def assign_salesman_of_assigned_partner(self, cr, uid, ids, context=None):
        salesmans_leads = {}
        for lead in self.browse(cr, uid, ids, context=context):
            if (lead.stage_id.probability > 0 and lead.stage_id.probability < 100) or lead.stage_id.sequence == 1:
                if lead.partner_assigned_id and lead.partner_assigned_id.user_id and lead.partner_assigned_id.user_id != lead.user_id:
                    salesman_id = lead.partner_assigned_id.user_id.id
                    if salesmans_leads.get(salesman_id):
                        salesmans_leads[salesman_id].append(lead.id)
                    else:
                        salesmans_leads[salesman_id] = [lead.id]
        for salesman_id, lead_ids in salesmans_leads.items():
            salesteam_id = self.on_change_user(cr, uid, lead_ids, salesman_id, context=None)['value'].get('team_id')
            self.write(cr, uid, lead_ids, {'user_id': salesman_id, 'team_id': salesteam_id}, context=context)

    @api.v8
    def assign_salesman_of_assigned_partner(self):
        salesmans_leads = {}
        for lead in self:
            if (lead.stage_id.probability > 0 and lead.stage_id.probability < 100) or lead.stage_id.sequence == 1:
                if lead.partner_assigned_id and lead.partner_assigned_id.user_id and lead.partner_assigned_id.user_id != lead.user_id:
                    salesman_id = lead.partner_assigned_id.user_id.id
                    if salesmans_leads.get(salesman_id):
                        salesmans_leads[salesman_id].append(lead.id)
                    else:
                        salesmans_leads[salesman_id] = [lead.id]
        for salesman_id, lead_ids in salesmans_leads.items():
            salesteam_id = self.on_change_user(lead_ids, salesman_id)['value'].get('team_id')
            self.browse(lead_ids).write({'user_id': salesman_id, 'team_id': salesteam_id})
