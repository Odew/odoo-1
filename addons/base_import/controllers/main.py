# -*- coding: utf-8 -*-
import simplejson
from openerp.http import Controller, route

class ImportController(Controller):
    @route('/base_import/set_file')
    def set_file(self, req, file, import_id, jsonp='callback'):
        import_id = int(import_id)
        written = req.env['base_import.import'].browse([import_id]).write({
            'file': file.read(),
            'file_name': file.filename,
            'file_type': file.content_type,
        })
        return 'window.top.%s(%s)' % (
            jsonp, simplejson.dumps({'result': written}))
