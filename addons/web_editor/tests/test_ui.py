import openerp.tests


class TestUi(openerp.tests.HttpCase):
    def test_01_admin_rte(self):
        self.phantom_js("/web_editor/field/html?callback=FieldTextHtml_0&enable_editor=1&datarecord=%7B%7D", "openerp.Tour.run('rte', 'test')", "openerp.Tour.tours.rte", login='admin')

    def test_02_admin_rte_inline(self):
        self.phantom_js("/web_editor/field/html/inline?callback=FieldTextHtml_0&enable_editor=1&datarecord=%7B%7D", "openerp.Tour.run('rte_inline', 'test')", "openerp.Tour.tours.rte", login='admin')
