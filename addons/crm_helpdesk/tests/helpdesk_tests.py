# -*- coding: utf-8 -*-

from openerp.tests.common import TransactionCase

class TestMailFetched(TransactionCase):

    def setUp(self):
        super(TestMailFetched, self).setUp()

    def test_mail_fetched(self):
        # Mail script will be fetched him request from mail server.
        # so I process that mail after read EML file
        mail_thr = self.env['mail.thread']
        helpdesk_obj = self.env['crm.helpdesk']
        request_file = open(openerp.modules.module.get_module_resource('crm_helpdesk','test', 'customer_question.eml'),'rb')
        request_message = request_file.read()
        mail_thr.message_process(helpdesk_obj, request_message)

        #After getting the mail,
        # I check details of new question of that customer.
        question_ids = helpdesk_obj.search([('email_from','=', 'Mr. John Right <info@customer.com>')])
        assert question_ids and len(question_ids), "Question is not created after getting request"
        question = helpdesk_obj.browse(question_ids[0])
        assert question.name == tools.ustr("Where is download link of user manual of your product ? "), "Subject does not match"

        # Now I Update message according to provide services.
        question_ids = helpdesk_obj.search([('email_from','=', 'Mr. John Right <info@customer.com>')])
        try:
          helpdesk_obj.message_update(question_ids, {'subject': 'Link of product', 'body': 'www.openerp.com'})
        except:
          pass
