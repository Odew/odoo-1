# -*- coding: utf-8 -*-

from openerp.tests.common import TransactionCase


class TestCrmClaimCommon(TransactionCase):

    def setUp(self):
        super(TestCrmClaimCommon, self).setUp()

        self.CrmClaim = self.env['crm.claim']
        self.MailThread = self.env['mail.thread']
