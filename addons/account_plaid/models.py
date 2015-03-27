# -*- coding: utf-8 -*-
import requests
import simplejson
import datetime
from openerp import models, api, fields
from openerp.tools.translate import _

class account_journal(models.Model):
    _inherit = "account.journal"

    plaid_id = fields.Many2one('plaid.account', "Plaid account")

    @api.multi
    def launch_plaid_wizard(self):
        return self.env['plaid.institutions.wizard'].with_context(goal='login').launch_wizard()

    @api.multi
    def launch_plaid_update_wizard(self):
        inst_wizard = self.env['plaid.institutions.wizard'].create({})
        inst_wizard['name'] = self.plaid_id.institution.id
        return inst_wizard.with_context(goal='update').create_wizard()

    @api.model
    def launch_synch_cron(self):
        for journal in self.search([('plaid_id', '!=', False)]):
            journal.launch_synch()
            
    @api.multi
    def launch_synch(self):
        # Fetch plaid.com
        params = {
            'access_token': self.plaid_id.access_token,
            'options': '{"gte": "' + self.plaid_id.last_update + '", "account": "'+ self.plaid_id.plaid_id + '"}',
        }
        plaid = self.env['plaid.credentials'].search([('company', '=', self.company_id.id)])
        resp, resp_json = plaid.fetch_plaid("connect/get", params)
        # There is no errors
        if resp.status_code == 200:
            balance = 0
            for account in resp_json['accounts']:
                if account['_id'] == self.plaid_id.plaid_id:
                    self.plaid_id.balance_current = account['balance']['current']
                    if 'available' in account['balance']:
                        self.plaid_id.balance_available = account['balance']['available']
            return self.env['account.bank.statement'].sync_bank_statement(resp_json['transactions'], self)
        # Error from the user (auth, ...)
        elif resp.status_code >= 400 and resp.status_code < 500:
            subject = _("Error in synchronization")
            body = _("The synchronization of the journal \"" + self.name + \
                   "\" with the plaid account \"" + self.plaid_id.name + \
                   "\" has failed.<br><br>" \
                   "The error message is :<br>" \
                   + resp_json['resolve'])
            plaid.message_post(body=body, subject=subject, type="comment")
            return False
        # Error with Plaid.com
        else:
            subject = _("Error with Plaid.com")
            body = _("The synchronization with Plaid.com failed. Please check the error : <br>" \
                   + resp_json)
            plaid.message_post(body=body, subject=subject, type="comment")
            return False

class account_bank_statement(models.Model):
    _inherit = "account.bank.statement"

    @api.model
    def sync_bank_statement(self, transactions, journal):
        all_lines = self.env['account.bank.statement.line'].search([('journal_id', '=', journal.id),
                                                                    ('date', '>=', journal.plaid_id.last_update)])

        statement = self.create({
                        'journal_id': journal.id,
                        'name': "/PLAID/" + datetime.datetime.now().strftime("%Y%m%d-%H%M"),
                        'balance_end_real': journal.plaid_id.balance_current,
                    })
        total = 0
        have_line = False
        journal.plaid_id.last_update = datetime.datetime.now()
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
            # Look for partner
            partner = self.find_partner(transaction)
            if partner:
                line['partner_id'] = partner
        statement.balance_start = journal.plaid_id.balance_current - total 
        if not have_line:
            statement.unlink()
            return True
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.bank.statement',
            'views': [[False, 'form']],
            'res_id': statement.id,
        }
        
    @api.multi
    def find_partner(self, transaction):
        partners = self.env['res.partner']
        domain = []
        location = transaction['meta']['location']
        if 'state' in location and 'address' in location and 'city' in location:
            domain.append(('state_id.name', '=', location['state']))
            domain.append(('street', '=', location['address']))
            domain.append(('city', '=', location['city']))
            if 'zip' in location:
                domain.append(('zip', '=', location['zip']))
            return partners.search(domain, limit=1)
        return partners
            
class account_bank_statement_line(models.Model):
    _inherit = "account.bank.statement.line"

    plaid_id = fields.Char("Plaid Id")

class plaid_institutions_wizard(models.TransientModel):
    _name = 'plaid.institutions.wizard'

    name = fields.Many2one('plaid.institution', string="Name") 
    username = fields.Char("Username")
    passwd = fields.Char("Password")
    pin = fields.Char("PIN")
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
        self.have_mfa = self.name and self.name.mfa_code

    have_username = fields.Boolean(string="Have Username", compute=_get_have_username)
    have_passwd = fields.Boolean(string="Have Password", compute=_get_have_passwd)
    have_pin = fields.Boolean(string="Have Pin", compute=_get_have_pin)
    have_mfa = fields.Boolean(string="Have mfa", compute=_get_have_mfa)
        
    @api.model
    def launch_wizard(self):
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
        if self.have_mfa:
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
    mfa_code = fields.Boolean("Have MFA code")

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

    # The method create_wizard fetch plaid.com, the method mfa() proccess the response
    @api.multi
    def create_wizard(self):
        journal = self.env['account.journal'].search([('id', '=', self.env.context['active_id'])])
        plaid = self.env['plaid.credentials'].search([('company', '=', journal.company_id.id)])
        # Two cases : 1) The user already fill the wizard 2) The wizard is open for the first time
        # First case
        if (self.response or self.selections) and self.access_token:
            # The mfa is a question or a selection
            params = {
                'access_token': self.access_token,
                'mfa': self.response,
            }
            resp, resp_json = plaid.fetch_plaid("connect/step", params)
        elif self.code_wizard:
            # The mfa is a code
            params = {
                'access_token': self.code_wizard.access_token,
                'options': '{"send_method":{"mask": "' + self.code_wizard.type.name + '"}}',
            }
            resp, resp_json = plaid.fetch_plaid("connect/step", params)
        else:
            # It the first time the user try to connect
            params = {
                'username': self.institution_wizard.username,
                'password': self.institution_wizard.passwd,
                'options': '{"login_only": true}'
            }
            if self.institution_wizard.pin:
                params['pin'] = self.institution_wizard.pin
            # Update the access_token
            if self.env.context['goal'] == 'update':
                params['access_token'] = journal.plaid_id.access_token
                resp, resp_json = plaid.fetch_plaid("connect", params, type="patch")
            # create a new access_token
            if self.env.context['goal'] == 'login':
                params['type'] = self.institution_wizard.name.type
                resp, resp_json = plaid.fetch_plaid("connect", params)
            
        return self.mfa(resp, resp_json)
        
        
    @api.multi
    def mfa(self, resp, resp_json):
        # The connection is ok
        if resp.status_code == 200:
            self.error = ""
            if self.env.context['goal'] == 'update':
                return True
            return self.env['plaid.select.account.wizard'].create_wizard_with_accounts(resp_json['accounts'], resp_json['access_token'])
        # There is a MFA request
        elif resp.status_code == 201:
            self.error = ""
            self.message = ""
            self.response = ""
            self.selections = ""
            self.access_token = resp_json['access_token']
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
        # Error from the user
        elif resp.status_code >= 400 and resp.status_code < 500:
            if resp_json['code'] == 1203:
                self.error = resp_json['resolve']
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
            else:
                self.institution_wizard.error = resp_json['resolve']
                return self.institution_wizard.create_wizard()
        # Error from plaid.com
        else:
            self.institution_wizard.error = _("Problem with Plaid.com. See mail for full log")
            return self.institution_wizard.create_wizard()

class plaid_select_account_wizard(models.TransientModel):
    _name = 'plaid.select.account.wizard'

    name = fields.Many2one('plaid.account.transient', string="Account") 
    access_token = fields.Char("access token")

    @api.model
    def create_wizard_with_accounts(self, accounts, access_token):
        wizard = self.create({})
        wizard.access_token = access_token
        for account in accounts:
            inst_type = account['institution_type']
            # HACK for the sandbox
            if inst_type == "fake_institution":
                inst_type = "citi"
            institution = self.env['plaid.institution'].search([('type', '=', inst_type)])
            new_account = self.env['plaid.account.transient'].create({
                'name': account['meta']['name'],
                'plaid_id': account['_id'],
                'institution': institution.id,
                'balance_current': account['balance']['current'],
            })
            new_account['wizard'] = wizard
            if account['balance'].get('available'):
                new_account['balance_available'] = account['balance']['available']
        return wizard.create_wizard()

    @api.multi
    def create_wizard(self):
        return {
            'name': 'Select account',
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
        account = self.env['plaid.account'].create({
            'name': self.name['name'],
            'plaid_id': self.name['plaid_id'],
            'balance_available': self.name['balance_available'],
            'balance_current': self.name['balance_current'],
            'access_token': self.access_token,
        })
        account['institution'] = self.name['institution']
        self.env['account.journal'].search([('id', '=', self.env.context['active_id'])]).write({'plaid_id': account.id})

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
        journal = self.env['account.journal'].search([('id', '=', self.env.context['active_id'])])
        plaid = self.env['plaid.credentials'].search([('company', '=', journal.company_id.id)])
        resp, resp_json = plaid.fetch_plaid("connect", params)
        #IF GOOD
        if (resp.status_code == 201):
            for select in resp_json['mfa']:
                code = self.env['plaid.code.selection'].create({
                    'name': select['mask'],
                })
                code['wizard'] = self
            self.access_token = resp_json['access_token']
            return {
                'name': 'Select code',
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
            self.institution_wizard.error = _("Problem with Plaid.com. See mail for full log")
            return self.institution_wizard.create_wizard()
        
    @api.multi
    def select(self):
        return self.env['plaid.mfa.response.wizard'].create_wizard_with_institution(code=self)
        
class plaid_code_selection(models.TransientModel):
    _name = 'plaid.code.selection'

    wizard = fields.Many2one('plaid.code.wizard', 'type', String="Wizard")
    name = fields.Char("Name")

class plaid_account_transient(models.TransientModel):
    _name = 'plaid.account.transient'

    name = fields.Char("Name")
    plaid_id = fields.Char("Plaid Account")
    institution = fields.Many2one('plaid.institution', String="Institution")
    balance_available = fields.Float("Available balance")
    balance_current = fields.Float("Current balance")
    wizard = fields.Many2one('plaid.select.account.wizard')
    access_token = fields.Char("Access token")

    
class plaid_account(models.Model):
    _name = 'plaid.account'

    name = fields.Char("Name")
    plaid_id = fields.Char("Plaid Account")
    institution = fields.Many2one('plaid.institution', String="Institution")
    balance_available = fields.Float("Available balance")
    balance_current = fields.Float("Current balance")
    access_token = fields.Char("Access Token")
    last_update = fields.Date("Last update", default=datetime.datetime.now())

class plaid_credentials(models.Model):
    _name = 'plaid.credentials'
    _inherit = 'mail.thread'

    plaid_id = fields.Char("Id")
    plaid_secret = fields.Char("Secret")
    company = fields.Many2one('res.company', string="Company")

    @api.multi
    def fetch_plaid(self, service, params, type="post"):
        params['client_id'] = self.plaid_id
        params['secret'] = self.plaid_secret
        if type == "post":
            resp = requests.post('https://tartan.plaid.com/'+service, params=params)
        elif type == "patch":
            resp = requests.patch('https://tartan.plaid.com/'+service, params=params)
        return (resp, simplejson.loads(resp.text))
        
