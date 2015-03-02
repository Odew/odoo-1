odoo.define('lunch.form_widgets', function (require) {
"use strict";

var core = require('web.core');
var common = require('web.form_common');
var Model = require('web.Model');
var form_widgets = require('web.form_widgets');
var _t = core._t;
var QWeb = core.qweb;
var lunch = {};

lunch.lunch_order_widget_previous_orders = common.AbstractField.extend(common.ReinitializeWidgetMixin,{
    template : 'lunch_order_widget_previous_orders',
    events: {
    'click span.add_button': 'set_order_line',
    },
    init: function(field_manager, node){
        this.lunch_data = {};
        this.fields_to_read = ['product_id', 'supplier', 'note', 'price', 'category_id','currency_id'];
        this.monetary = new form_widgets.FieldMonetary(field_manager, node); // create instance to use format_value
        this.monetary.__edispatcherRegisteredEvents = []; // remove all bind events
        return this._super.apply(this, arguments);
    },
    set_value: function(value_) {
        value_ = value_ || [];
        if(value_.length >= 1 && value_[0] instanceof Array) {
          value_ = value_[0][2];
        }
        this._super(value_);
    },
    set_lunchbox_value: function(data){
        var self = this;
        _.each(data, function(datum){
            self.lunch_data[datum['id']] = datum;
        });
    },
    fetch_value: function(){
        var self = this;
        return new Model("lunch.order.line").call('read',[this.get_value(), this.fields_to_read])
            .done(function(data){
              self.set_lunchbox_value(data);
            });
    },
    set_order_line: function(event){
        var id = parseInt($(event.currentTarget).attr('id'));

        if (typeof this.lunch_data[id]['product_id'][0] != 'undefined'){
          this.lunch_data[id]['product_id'] = this.lunch_data[id]['product_id'][0];
        }

        if (typeof this.lunch_data[id]['supplier'][0] != 'undefined'){
          this.lunch_data[id]['supplier'] = this.lunch_data[id]['supplier'][0];
        }

        if (typeof this.lunch_data[id]['category_id'][0] != 'undefined'){
          this.lunch_data[id]['category_id'] = this.lunch_data[id]['category_id'][0];
        }

        // Add the selection to the order lines
        var records = this.field_manager.get_field_value('order_line_ids');
        records.push([0, 0, this.lunch_data[id]]);

        this.field_manager.set_values({'order_line_ids': records});
        this.getParent().fields.order_line_ids.trigger_on_change();

        // If a previous order is selected several time, then the note is modified for one
        // order line, this note is applied to all lines. Forcing to render prevents this bug.
        this.render_value();
    },
    render_value: function() {
        var self = this;
        return this.fetch_value().done(function(data) {
            if (_.isEmpty(data)) {
              return self.$el.html(QWeb.render("lunch_order_widget_no_previous_order"));
            }
            var categories = _.groupBy(data,function(data1){return data1['supplier'][1];});
            return self.$el.html(QWeb.render("lunch_order_widget_previous_orders_list", {'widget': self, 'categories': categories}
            ));
        });
    },
    destroy: function () {
      this.monetary.destroy();
      this._super();
    }
});
core.form_widget_registry.add('previous_order', lunch.lunch_order_widget_previous_orders);

return lunch;

});
