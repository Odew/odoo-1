openerp.hr_material = function(openerp) {
    "use strict";
    openerp.web_kanban.KanbanRecord.include({
        on_card_clicked: function() {
            if (this.view.dataset.model === 'hr.material.category') {
                this.$('.oe_kanban_content a').first().click();
            } else {
                this._super.apply(this, arguments);
            }
        },
    });
};
