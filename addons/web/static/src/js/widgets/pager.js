odoo.define('web.Pager', function (require) {
"use strict";

var Widget = require('web.Widget');

var Pager = Widget.extend({
    template: "Pager",
    // pager goes from 1 to size (included).
    // current value is current_min (if limit === 1)
    //              or the interval [current_min, current_min + limit[ if limit > 1
    init: function (parent, size, current_min, limit) {
        this.size = size;
        this.current_min = current_min;
        this.limit = limit;
        this._super(parent);
    },

    start: function () {
        this.$content = this.$('.o-pager-value');
        this.$previous = this.$('.o-pager-previous');
        this.$next = this.$('.o-pager-next');

        this.$previous.click(_.bind(this.change_selection, this, -1));
        this.$next.click(_.bind(this.change_selection, this, 1));
        this.render();
    },

    set_state: function (options) {
        this.size = ('size' in options) ? options.size : this.size;
        this.current_min = ('current_min' in options) ? options.current_min : this.current_min;
        this.limit = ('limit' in options) ? options.limit : this.limit;
        if (this.current_min > this.limit) {
            this.current_min = 1;
        }
        this.render();
    },

    render: function () {
        var state;
        var max = this.get_current_max();

        if (this.size === 0) {
            this.$el.hide();
            return;
        } else {
            this.$el.show();
        }

        if (this.limit === 1) {
            state = "" + this.current_min + " / " + this.size;
        } else {
            state = "" + this.current_min + "-" + max + " / " + this.size;
        }
        var controls_shown = 1 < this.current_min || max < this.size;
        this.$previous.toggle(controls_shown);
        this.$next.toggle(controls_shown);
        this.$content.html(state);
    },

    change_selection: function (direction) {
        this.current_min = (this.current_min + this.limit*direction);
        if (this.current_min > this.size) {
            this.current_min = 1;
        }
        if ((this.current_min < 1) && (this.limit === 1)) {
            this.current_min = this.size;
        }
        if ((this.current_min < 1) && (this.limit > 1)) {
            this.current_min = this.size - (this.size % this.limit) + 1;
        }
        this.trigger('pager_changed', {
            current_min: this.current_min,
            current_max: this.get_current_max(),
        });
        this.render();
    },

    get_current_max: function () {
        return  Math.min(this.current_min + this.limit - 1, this.size);
    },
});

return Pager;

});
