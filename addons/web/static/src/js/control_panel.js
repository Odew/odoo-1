odoo.define('web.ControlPanelMixin', function (require) {
"use strict";

/**
 * Mixin allowing widgets to communicate with the ControlPanel. Widgets needing a
 * ControlPanel should use this mixin and call update_control_panel(cp_status) where
 * cp_status contains information for the ControlPanel to update itself.
 */
var ControlPanelMixin = {
    need_control_panel: true,
    /**
     * @param {web.Bus} [cp_bus] Bus to communicate with the ControlPanel
     */
    set_cp_bus: function(cp_bus) {
        this.cp_bus = cp_bus;
    },
    /**
     * Triggers 'update' on the cp_bus to update the ControlPanel according to cp_status
     * @param {Object} [cp_status] see web.ControlPanel.update() for a description
     */
    update_control_panel: function(cp_status) {
        this.cp_bus.trigger("update", cp_status || {});
    },
};

return ControlPanelMixin;

});

odoo.define('web.ControlPanel', function (require) {
"use strict";

var core = require('web.core');
var Widget = require('web.Widget');

var ControlPanel = Widget.extend({
    template: 'ControlPanel',
    /**
     * @param {String} [template] the QWeb template to render the ControlPanel.
     * By default, the template 'ControlPanel' will be used
     */
    init: function(parent, template) {
        this._super(parent);
        if (template) {
            this.template = template;
        }

        this.bus = new core.Bus();
        this.bus.on("update", this, this.update);
        this.bus.on("update_breadcrumbs", this, this.update_breadcrumbs);
    },
    start: function() {
        // Retrieve ControlPanel jQuery nodes
        this.$first_row = this.$el.siblings('.o-control-panel-first-row');
        this.$second_row = this.$el.siblings('.o-control-panel-second-row');
        this.$title_col = this.$('.o-cp-breadcrumbs-col');
        this.$breadcrumbs = this.$('.o-cp-breadcrumbs');
        this.$searchview = this.$('.o-cp-searchview');
        this.$searchview_buttons = this.$('.o-search-options');
        this.$buttons = this.$('.o-cp-buttons');
        this.$sidebar = this.$('.o-cp-sidebar');
        this.$pager = this.$('.o-cp-pager');
        this.$switch_buttons = this.$('.o-cp-switch-buttons');

        // By default, hide the ControlPanel and remove its contents from the DOM
        this.toggle_visibility(true);

        return this._super();
    },
    /**
     * @return {Object} the Bus the ControlPanel is listening on
     */
    get_bus: function() {
        return this.bus;
    },
    /**
     * Hides (or shows) the ControlPanel in headless (resp. non-headless) mode
     * Also detaches or attaches its contents to clean the DOM
     */
    toggle_visibility: function(hidden) {
        this.$el.toggle(!hidden);
        if (hidden) {
            this.$first_row_content = this.$first_row.contents().detach();
            this.$second_row_content = this.$second_row.contents().detach();
        } else {
            this.$first_row_content.appendTo(this.$first_row);
            this.$second_row_content.appendTo(this.$second_row);
        }
    },
    /**
     * Detaches the content of the ControlPanel
     */
    _detach_content: function() {
        this.$buttons.contents().detach();
        this.$switch_buttons.contents().detach();
        this.$pager.contents().detach();
        this.$sidebar.contents().detach();
        this.$searchview.contents().detach();
        this.$searchview_buttons.contents().detach();
    },
    /**
     * Attaches content to the ControlPanel
     * @param {Object} [content] dictionnary of jQuery elements to attach, whose keys
     * are jQuery nodes identifiers
     */
    _attach_content: function(content) {
        var self = this;
        _.each(content, function($nodeset, $element) {
            if ($nodeset && self[$element]) {
                $nodeset.appendTo(self[$element]);
            }
        });
    },
    /**
     * Updates the content and display of the ControlPanel
     * @param {Object} [status.active_view] the current active view
     * @param {Array} [status.breadcrumbs] the breadcrumbs to display
     * @param {Object} [status.cp_content] dictionnary containing the new ControlPanel jQuery elements
     * @param {Boolean} [status.hidden] true if the ControlPanel should be hidden
     * @param {openerp.web.SearchView} [status.searchview] the searchview widget
     * @param {Boolean} [status.search_view_hidden] true if the searchview is hidden, false otherwise
     */
    update: function(status) {
        this.toggle_visibility(status.hidden);
        if (!status.hidden) {
            // Don't update the ControlPanel in headless mode as the views have
            // inserted themselves the buttons where they want, so inserting them
            // again in the ControlPanel will removed them from there they should be
            this._detach_content();
            this._attach_content(status.cp_content);
            if (status.active_view_selector) this.update_switch_buttons(status.active_view_selector);
            if (status.searchview) this.update_search_view(status.searchview, status.search_view_hidden);
            if (status.breadcrumbs) this.update_breadcrumbs(status.breadcrumbs);
        }
    },
    /**
     * Removes active class on all switch-buttons and adds it to the one of the active view
     * @param {Object} [active_view_selector] the selector of the div to activate
     */
    update_switch_buttons: function(active_view_selector) {
        _.each(this.$switch_buttons.find('button'), function(button) {
            $(button).removeClass('active');
        });
        this.$(active_view_selector).addClass('active');
    },
    /**
     * Updates the breadcrumbs
     **/
    update_breadcrumbs: function (breadcrumbs) {
        var self = this;

        if (!breadcrumbs.length) return;

        var $breadcrumbs = breadcrumbs.map(function (bc, index) {
            return make_breadcrumb(bc, index === breadcrumbs.length - 1);
        });

        this.$breadcrumbs
            .empty()
            .append($breadcrumbs);

        function make_breadcrumb (bc, is_last) {
            var $bc = $('<li>')
                    .append(is_last ? bc.title : $('<a>').text(bc.title))
                    .toggleClass('active', is_last);
            if (!is_last) {
                $bc.click(function () {
                    self.trigger("on_breadcrumb_click", bc.action, bc.index);
                });
            }
            return $bc;
        }
    },
    /**
     * Updates the SearchView's visibility and extend the breadcrumbs area if the SearchView is not visible
     * @param {openerp.web.SearchView} [searchview] the searchview Widget
     * @param {Boolean} [is_hidden] visibility of the searchview
     **/
    update_search_view: function(searchview, is_hidden) {
        // Set the $buttons div (in the DOM) of the searchview as the $buttons
        // have been appended to a jQuery node not in the DOM at SearchView initialization
        searchview.$buttons = this.$searchview_buttons;
        searchview.toggle_visibility(!is_hidden);
        this.$title_col.toggleClass('col-md-6', !is_hidden).toggleClass('col-md-12', is_hidden);
    },
});

return ControlPanel;

});
