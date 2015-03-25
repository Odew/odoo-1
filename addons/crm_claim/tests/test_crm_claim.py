# -*- coding: utf-8 -*-

from openerp.modules.module import get_module_resource
from common import TestCrmClaimCommon


class TestCrmClaim(TestCrmClaimCommon):

    def test_01_email_message(self):
        msg = open(get_module_resource('crm_claim', 'tests', 'customer_claim.eml'), 'rb').read()
        self.MailThread.message_process('crm.claim', msg)

        domain = [
            ('name', '=', u'demande der\xe8glement de votre produit.'),
            ('email_from', '=', u'Mr. John Right <info@customer.com>'),
            ('partner_id', '=', False),
            ('email_cc', '=', None),
        ]
        self.assertEqual(self.CrmClaim.search_count(domain), 1, msg="Unable to parse the Crm Claim from Email")
