# -*- coding: utf-8 -*-
from datetime import datetime

from openerp.tests import common


class TestResourceCommon(common.TransactionCase):

    def setUp(self):
        super(TestResourceCommon, self).setUp()
        cr, uid = self.cr, self.uid
        if not hasattr(self, 'context'):
            self.context = {}

        # Usefull models
        self.ResourceResource = self.env['resource.resource']
        self.ResourceCalendar = self.env['resource.calendar']
        self.ResourceAttendance = self.env['resource.calendar.attendance']
        self.ResourceLeaves = self.env['resource.calendar.leaves']

        # Some demo data
        self.date1 = datetime.strptime('2013-02-12 09:08:07', '%Y-%m-%d %H:%M:%S')  # weekday() returns 1, isoweekday() returns 2
        self.date2 = datetime.strptime('2013-02-15 10:11:12', '%Y-%m-%d %H:%M:%S')  # weekday() returns 4, isoweekday() returns 5
        # Leave1: 19/02/2013, from 9 to 12, is a day 1
        self.leave1_start = datetime.strptime('2013-02-19 09:00:00', '%Y-%m-%d %H:%M:%S')
        self.leave1_end = datetime.strptime('2013-02-19 12:00:00', '%Y-%m-%d %H:%M:%S')
        # Leave2: 22/02/2013, from 9 to 15, is a day 4
        self.leave2_start = datetime.strptime('2013-02-22 09:00:00', '%Y-%m-%d %H:%M:%S')
        self.leave2_end = datetime.strptime('2013-02-22 15:00:00', '%Y-%m-%d %H:%M:%S')
        # Leave3: 25/02/2013 (day0) -> 01/03/2013 (day4)
        self.leave3_start = datetime.strptime('2013-02-25 13:00:00', '%Y-%m-%d %H:%M:%S')
        self.leave3_end = datetime.strptime('2013-03-01 11:30:00', '%Y-%m-%d %H:%M:%S')

        # Resource data
        # Calendar working days: 1 (8-16 -> 8hours), 4 (8-13, 16-23 -> 12hours)
        self.calendar = self.ResourceCalendar.create({'name': 'TestCalendar'})
        self.att1_id = self.ResourceAttendance.create({
                'name': 'Att1',
                'dayofweek': '1',
                'hour_from': 8,
                'hour_to': 16,
                'calendar_id': self.calendar.id,
            }
        )
        self.att2_id = self.ResourceAttendance.create({
                'name': 'Att2',
                'dayofweek': '4',
                'hour_from': 8,
                'hour_to': 13,
                'calendar_id': self.calendar.id,
            }
        )
        self.att3_id = self.ResourceAttendance.create({
                'name': 'Att3',
                'dayofweek': '4',
                'hour_from': 16,
                'hour_to': 23,
                'calendar_id': self.calendar.id,
            }
        )
        self.resource1 = self.ResourceResource.create({
                'name': 'TestResource1',
                'resource_type': 'user',
                'time_efficiency': 150.0,
                'calendar_id': self.calendar.id,
            }
        )
        self.leave1_id = self.ResourceLeaves.create(
            {
                'name': 'GenericLeave',
                'calendar_id': self.calendar.id,
                'date_from': self.leave1_start,
                'date_to': self.leave1_end,
            }
        )
        self.leave2_id = self.ResourceLeaves.create(
            {
                'name': 'ResourceLeave',
                'calendar_id': self.calendar.id,
                'resource_id': self.resource1.id,
                'date_from': self.leave2_start,
                'date_to': self.leave2_end,
            }
        )
        self.leave3_id = self.ResourceLeaves.create(
            {
                'name': 'ResourceLeave2',
                'calendar_id': self.calendar.id,
                'resource_id': self.resource1.id,
                'date_from': self.leave3_start,
                'date_to': self.leave3_end,
            }
        )
        # Some browse data
        # self.calendar = self.ResourceCalendar.browse(self.calendar_id)
