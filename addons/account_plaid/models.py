# -*- coding: utf-8 -*-
import requests
import simplejson
import datetime
from openerp import models, api, fields

class account_journal(models.Model):
    _inherit = "account.journal"

    def _get_plaid_id(self):
        return [('a', 'a')]

    plaid_id = fields.Many2one('plaid.account', "Plaid account")

    @api.multi
    def launch_plaid_wizard(self):
        return self.env['plaid.institutions.wizard'].with_context(goal='login').launch_wizard()

    @api.multi
    def launch_synch(self):
        inst_wizard = self.env['plaid.institutions.wizard'].create({})
        inst_wizard['name'] = self.plaid_id.institution.id
        return inst_wizard.with_context(goal='sync').create_wizard()

class account_bank_statement(models.Model):
    _inherit = "account.bank.statement"

    @api.model
    def sync_bank_statement(self, transactions, journal_id):
        all_lines = self.env['account.bank.statement.line'].search([('journal_id', '=', journal_id)])
        journal = self.env['account.journal'].search([('id', '=', journal_id)])
        account_ids = list(set([journal.default_debit_account_id.id, journal.default_credit_account_id.id]))

        lines_already_accounted = self.env['account.bank.statement.line'].search([('journal_id', '=', journal_id),])
        start_amount = sum([line.amount for line in lines_already_accounted])
        print(start_amount)
        statement = self.create({
                        'journal_id': journal_id,
                        'name': "/PLAID/" + datetime.datetime.now().strftime("%Y%m%d-%H%M"),
                        'balance_start': start_amount
                    })
        total = 0
        have_line = False
        for transaction in transactions:
            if transaction['_account'] != journal.plaid_id.plaid_id \
               or len(all_lines.search([('plaid_id','=', transaction['_id'])])) > 0:
                continue
            have_line = True
            line = self.env['account.bank.statement.line'].create({
                'date': transaction['date'],
                'name': transaction['name'],
                'amount': -1 * transaction['amount'],
                'plaid_id': transaction['_id'],
                'statement_id': statement.id
            })
            total += -1 * transaction['amount']
        statement.balance_end_real = start_amount + total
        if not have_line:
            statement.unlink()
            return True
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.bank.statement',
            'views': [[False, 'form']],
            'res_id': statement.id,
        }
        
class account_bank_statement_line(models.Model):
    _inherit = "account.bank.statement.line"

    plaid_id = fields.Char("Plaid Id")

class plaid_institutions_wizard(models.TransientModel):
    _name = 'plaid.institutions.wizard'

    name = fields.Many2one('plaid.institution', string="Name") 
    username = fields.Char("Username")
    passwd = fields.Char("Password")
    pin = fields.Char("PIN")
    mfa = fields.Many2one('plaid.mfa')
    error = fields.Char("Error")

    @api.one
    def _get_goal(self):
        self.goal = self.env.context['goal'] or 'sync'
    goal = fields.Char("Goal", compute=_get_goal)

    @api.one
    @api.depends('name')
    def _get_have_username(self):
        self.have_username = self.name and self.name.username
        
    @api.one
    @api.depends('name')
    def _get_have_passwd(self):
        self.have_passwd = self.name and self.name.passwd

    @api.one
    @api.depends('name')
    def _get_have_pin(self):
        self.have_pin = self.name and self.name.pin

    @api.one
    @api.depends('name')
    def _get_have_mfa(self):
        self.have_mfa = self.name and self.name.mfa

    have_username = fields.Boolean(string="Have Username", compute=_get_have_username)
    have_passwd = fields.Boolean(string="Have Password", compute=_get_have_passwd)
    have_pin = fields.Boolean(string="Have Pin", compute=_get_have_pin)
    have_mfa = fields.Boolean(string="Have mfa", compute=_get_have_mfa)
        
    @api.model
    def launch_wizard(self):
        # Create wizard
        wizard_institutions = self.env['plaid.institutions.wizard'].create({})
        return wizard_institutions.create_wizard()

    @api.multi
    def create_wizard(self):
        return {
            'name': 'Institutions Wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'plaid.institutions.wizard',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': self.env.context,
        }

    @api.multi
    def plaid_login(self):
        if self.mfa and self.mfa.name == 'code':
            print("---- code")
            return self.env['plaid.code.wizard'].create({}).create_wizard_with_institution(self)
            #create mfa code selection
        else:
            return self.env['plaid.mfa.response.wizard'].create_wizard_with_institution(institution=self)
            #create mfa selection wizard, with mfa if necessary

class plaid_institution(models.Model):
    _name = 'plaid.institution'

    type = fields.Char("Type")
    name = fields.Char("name")
    
    username = fields.Char(string="Have Username")
    passwd = fields.Char(string="Have Password")
    pin = fields.Char(string="Have Pin")
    plaid_id = fields.Char("Plaid ID")
    mfa = fields.Boolean("Have MFA")

class plaid_mfa(models.Model):
    _name = 'plaid.mfa'

    name = fields.Char("Mfa")
    institution = fields.Many2one('plaid.institution')

class plaid_mfa_response_wizard(models.TransientModel):
    _name = 'plaid.mfa.response.wizard'

    mfa_type = fields.Selection([('message', 'message'),
                                 ('selections', 'selections'),
                                 ('code', 'code')])
    institution_wizard = fields.Many2one('plaid.institutions.wizard')
    code_wizard = fields.Many2one('plaid.code.wizard')
    message = fields.Char("Message")
    response = fields.Char("Response")
    selections = fields.Char("JSON in Char")
    access_token = fields.Char("Access Token")
    error = fields.Char("error")

    @api.model
    def create_wizard_with_institution(self, institution=None, code=None):
        wizard = self.create({})
        if institution:
            wizard.institution_wizard = institution
        if code:
            wizard.code_wizard = code    
            wizard.institution_wizard = code.institution_wizard
        return wizard.create_wizard()

    @api.multi
    def create_wizard(self):
        import pudb; pu.db
        if (self.response or self.selections) and self.access_token:
            params = {
                'access_token': self.access_token,
                'mfa': self.response,
            }
            resp, resp_json = fetch_plaid("connect/step", params)
        elif self.code_wizard:
            params = {
                'access_token': self.code_wizard.access_token,
                'options': '{"send_method":{"mask": "' + self.code_wizard.type.name + '"}}',
            }
            resp, resp_json = fetch_plaid("connect/step", params)
        else:
            params = {
                'username': self.institution_wizard.username,
                'password': self.institution_wizard.passwd,
                'type': self.institution_wizard.name.type,
            }
            if self.institution_wizard.pin:
                params['pin'] = self.institution_wizard.pin
            if self.institution_wizard.goal == 'login':
                params['options'] = '{"login_only": true}'
            resp, resp_json = fetch_plaid("connect", params)
            
        return self.mfa(resp, resp_json)
        
        
    @api.multi
    def mfa(self, resp, resp_json):
        if resp.status_code == 200:
            if self.env.context['goal'] == 'login':
                print("-------- LOGIN OK -----------")
                pp(resp_json)
                return self.env['plaid.select.account.wizard'].create_wizard_with_accounts(resp_json['accounts'])
            elif self.env.context['goal'] == 'sync':
                print("-------- SYNC ---------")
                return self.env['account.bank.statement'].sync_bank_statement(resp_json['transactions'], self.env.context['active_id'])
        elif resp.status_code == 201:
            self.message = ""
            self.response = ""
            self.selections = ""
            self.access_token = resp_json['access_token']
            print("MFA CREATE WIZARD")
            if resp_json['type'] == 'questions':
                self.mfa_type = 'message'
                self.message = resp_json['mfa'][0]['question']
            elif resp_json['type'] == 'selections':
                self.mfa_type = 'selections'
                self.selections = resp.text
            else:
                self.mfa_type = 'message'
                self.message = resp_json['mfa']['message']
            return {
                'name': 'Response MFA Wizard',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'plaid.mfa.response.wizard',
                'res_id': self.id,
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': self.env.context,
            }
        elif resp.status_code >= 400 and resp.status_code < 500:
            if resp_json['code'] == 1203:
                self.error = resp_json['resolve']
                self.response = ""
                self.selections = ""
                return self.create_wizard()
            else:
                self.institution_wizard.error = resp_json['resolve']
                return self.institution_wizard.create_wizard()
        else:
            print("EERRROR")
            print(resp.status_code)
            print(resp.text)
        return True

class plaid_select_account_wizard(models.Model):
    _name = 'plaid.select.account.wizard'

    name = fields.Many2one('plaid.account', string="Account") 

    @api.model
    def create_wizard_with_accounts(self, accounts):
        wizard = self.create({})
        self.env['plaid.account'].search([]).unlink()
        for account in accounts:
            inst_type = account['institution_type']
            if inst_type == "fake_institution":
                inst_type = "citi"
            institution = self.env['plaid.institution'].search([('type', '=', inst_type)])
            new_account = self.env['plaid.account'].create({
                'name': account['meta']['name'],
                'plaid_id': account['_id'],
                'institution': institution.id,
                'balance_current': account['balance']['current'],
            })
            if account['balance'].get('available'):
                new_account['balance_available'] = account['balance']['available']
        return wizard.create_wizard()

    @api.multi
    def create_wizard(self):
        return {
            'name': 'Response MFA Wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'plaid.select.account.wizard',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': self.env.context,
        }

    @api.multi
    def select(self):
        self.env['account.journal'].search([('id', '=', self.env.context['active_id'])]).write({'plaid_id': self.name.id})
        print("END")

class plaid_code_wizard(models.TransientModel):
    _name = 'plaid.code.wizard'

    institution_wizard = fields.Many2one('plaid.institutions.wizard', "Institution")
    type = fields.Many2one('plaid.code.selection', "Choice")
    access_token = fields.Char("Access Token")

    @api.multi
    def create_wizard_with_institution(self, institution):
        self.institution_wizard = institution
        params = {
            'username': self.institution_wizard.username,
            'password': self.institution_wizard.passwd,
            'type': self.institution_wizard.name.type,
            'options': '{"list":true}'
        }
        resp, resp_json = fetch_plaid("connect", params)
        #IF GOOD
        if (resp.status_code == 201):
            self.env['plaid.code.selection'].search([]).unlink()
            for select in resp_json['mfa']:
                self.env['plaid.code.selection'].create({
                    'name': select['mask']
                })
            self.access_token = resp_json['access_token']
            return {
                'name': 'Response MFA Wizard',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'plaid.code.wizard',
                'res_id': self.id,
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': self.env.context,
            }
        elif (resp.status_code >= 400 and resp.status_code < 500):
            self.institution_wizard.error = resp_json['resolve']
            return self.institution_wizard.create_wizard()
        else:
            print(resp.text)
            return False
        
    @api.multi
    def select(self):
        return self.env['plaid.mfa.response.wizard'].create_wizard_with_institution(code=self)
        
class plaid_code_selection(models.TransientModel):
    _name = 'plaid.code.selection'

    name = fields.Char("Name")

    
class plaid_account(models.Model):
    _name = 'plaid.account'

    name = fields.Char("Name")
    plaid_id = fields.Char("Plaid Account")
    institution = fields.Many2one('plaid.institution', String="Institution")
    balance_available = fields.Float("Available balance")
    balance_current = fields.Float("Current balance")

def pp(json):
    print(simplejson.dumps(json, sort_keys=True, indent=4 * ' '))

def fetch_plaid(service, params):
    params['client_id'] = 'test_id'
    params['secret'] = 'test_secret'
    resp = requests.post('https://tartan.plaid.com/'+service, params=params)
    return (resp, simplejson.loads(resp.text))
