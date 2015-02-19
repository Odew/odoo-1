odoo.define('web.Menu', function (require) {
"use strict";

var core = require('web.core');
var session = require('web.session');
var Widget = require('web.Widget');

var QWeb = core.qweb;

var Menu = Widget.extend({
    init: function(parent) {
        this._super.apply(this, arguments);
        this.webclient = parent;
        this.is_bound = $.Deferred();

        this.primary_secondary_map = {};
        this.current_primary_menu = undefined;
        this.current_secondary_menu = undefined;

        this.state = 'initial';
        core.bus.on('do_reload_needaction', this, this.fetch_needactions);
    },
    setElement: function($primary_menu, $secondary_menu, $menu_toggler, $menu_brand) {
        debugger
        this.$primary_menu = $primary_menu;
        this.$secondary_menu = $secondary_menu;
        this.$menu_toggler = $menu_toggler;
        this.$menu_brand = $menu_brand;
    },
    start: function() {
        var self = this;

        // Menu toggler event handler
        self.$menu_toggler.click(function (ev) {
            ev.preventDefault();

            if (self.state !== 'initial') {
                self.slide('initial');
            } else {
                self.is_mobile_layout() ? self.slide('secondary') : self.slide('primary');
            }
        });

        // Primary menu event delegation
        self.$primary_menu.on('click', 'a[data-menu]', self, function (ev) {
            ev.preventDefault();
            var menu_id = $(ev.currentTarget).data('menu');
            var action_id = $(ev.currentTarget).data('action-id');
            var needaction = $(ev.target).is('#menu_counter');
            self._on_primary_menu_click(menu_id, action_id, needaction);
        });

        // Secondary menu event delegation
        self.$secondary_menu.on('click', 'a[data-menu]', self, function (ev) {
            ev.preventDefault();
            var menu_id = $(ev.currentTarget).data('menu');
            var action_id = $(ev.currentTarget).data('action-id');
            var needaction = $(ev.target).is('#menu_counter');
            self._on_secondary_menu_click(menu_id, action_id, needaction);
        });

        // FIXME: Mobile link to display the primary menu
        self.$secondary_menu.parent().find('.oe_applications_link').click(function (ev) {
            ev.preventDefault();
            self.slide('primary');
        });

        // Fill the primary - secondary menu ids relation by querying the DOM
        self.$secondary_menu.find('.oe_secondary_menu').each(function(index, oe_secondary_menu) {
            var submenu_parent_id = $(oe_secondary_menu).data('menuParent');
            var submenu_menu_ids = $(oe_secondary_menu).find('a[data-menu]').map(function() {
                return $(this).data('menu');
            }).get();

            if (submenu_menu_ids) {
                self.primary_secondary_map[submenu_parent_id] = submenu_menu_ids;
            }
        });

        self.is_bound.resolve();

        return self._super.apply(self, arguments);
    },
    /**
     * Return the current layout state of the webclient. The webclient is
     * in "xs mode" when its viewport's width is < 768.
     */
    is_mobile_layout: function() {
        // FIXME: this method is not implemented in IE9
        return window.matchMedia('(max-width: 767px)').matches;
    },
    /**
     * Trigger a sliding animation to show/hide parts of the menu.
     *
     * In the desktop layout, the secondary menu is always shown and a click on
     * the hamburger icon triggers a slide transition to display the primary
     * menu. In mobile layout, both menus are hidden and once the hamburger is
     * clicked, we display the secondary menu. The `oe_applications_link`
     * button trigger the display of the primary menu in the mobile layout.
     */
    slide: function(state) {
        if (state === 'initial') {
            this.$primary_menu.parent().toggleClass('slided', false);
            this.$secondary_menu.parent().toggleClass('slided', false);
            this.webclient.toggle_overlay(false);
        } else if (state === 'secondary') {
            // Unused in desktop layout
            this.$primary_menu.parent().toggleClass('slided', false);
            this.$secondary_menu.parent().toggleClass('slided', true);
        } else if (state === 'primary') {
            this.$primary_menu.parent().toggleClass('slided', true);
            this.$secondary_menu.parent().toggleClass('slided', true);
            this.webclient.toggle_overlay(true);
        }
        this.state = state;
    },
    _menu_id_to_action_id: function(menu_id) {
        // find back the menuitem in dom to get the action
        var $item = this.$primary_menu.add(this.$secondary_menu).find('a[data-menu=' + menu_id + ']');
        var action_id = $item.data('action-id');
        if (!action_id) {
            // If first level menu doesnt have action trigger first leaf
            if (this.$primary_menu.has($item).length) {
                var $sub_menu = this.$secondary_menu.find('.oe_secondary_menu[data-menu-parent=' + menu_id + ']');
                var $items = $sub_menu.find('a[data-action-id]').filter('[data-action-id!=""]');
                if ($items.length) {
                    action_id = $items.data('action-id');
                }
            }
        }
        return action_id;
    },
    _action_id_to_menu_id: function(action_id) {
        var $item = this.$primary_menu.add(this.$secondary_menu).find('a[data-action-id="' + action_id + '"]');
        return $item.data('menu');
    },
    /**
     * Fetch the needactions counter associated to the secondary menu items of
     * a primary menu and render their badges.
     */
    fetch_needactions: function(primary_menu_id) {
        var self = this;
        if (!primary_menu_id && self.current_primary_menu) {
            primary_menu_id = self.current_primary_menu;
        }
        // Needaction
        var secondary_menu_ids = self.primary_secondary_map[primary_menu_id];
        if (secondary_menu_ids) {
            self.rpc('/web/menu/load_needaction', {
                'menu_ids': secondary_menu_ids,
            }).done(function(needactions) {
                _.each(needactions, function (item, menu_id) {
                    var $item = self.$secondary_menu.find('a[data-menu="' + menu_id + '"]');
                    $item.find('.badge').remove();
                    if (item.needaction_counter && item.needaction_counter > 0) {
                        $item.append(QWeb.render("Menu.needaction_counter", { widget : item }));
                    }
                });
            });
        }
    },
    /**
     * Style the primary menu as if it were manually selected, but does not
     * trigger the `menu_click` event (listened by the Action Manager). Also
     * run the needaction logic.
     *
     * Triggers a `primary_menu_click`.
     */
    decorate_primary_menu: function(menu_id) {
        var self = this;
        var $clicked_menu, $secondary_menu, $main_menu;

        // Decorate a primary menu item
        // Reset
        self.$primary_menu.find('.active').removeClass('active');
        self.$secondary_menu.find('.oe_secondary_menu').hide();

        $clicked_menu = self.$primary_menu.find('a[data-menu=' + menu_id + ']');
        $secondary_menu = self.$secondary_menu.find('.oe_secondary_menu[data-menu-parent=' + $clicked_menu.attr('data-menu') + ']');
        $main_menu = $clicked_menu;

        // Decoration
        $main_menu.parent().addClass('active');
        $secondary_menu.show();
        $secondary_menu.find('.oe_menu_toggler').siblings('.oe_secondary_submenu').hide();
        self.$menu_brand.text($main_menu.text());

        // Run needaction
        self.fetch_needactions(menu_id);

        self.trigger('primary_menu_click', {id: menu_id});
        self.current_primary_menu = menu_id;
    },
    /**
     * Style the secondary menu as if it were manually selected, but does not
     * trigger the `menu_click` event (listened by the Action Manager).
     *
     * Triggers a `secondary_menu_click`.
     */
    decorate_secondary_menu: function(menu_id) {
        var self = this;
        var $clicked_menu, $secondary_menu, primary_menu_id;

        // Decorate a secondary menu item
        // Reset
        self.$secondary_menu.find('.oe_secondary_menu').hide();

        $clicked_menu = self.$secondary_menu.find('a[data-menu=' + menu_id + ']');
        $secondary_menu = $clicked_menu.parents('.oe_secondary_menu');
        primary_menu_id = $secondary_menu.data('menu-parent');

        // Decoration
        $clicked_menu.parents().show();

        if (!self.current_primary_menu) {
            self.decorate_primary_menu(primary_menu_id);  // Keep primary menu sync
        }

        if ($clicked_menu.is('.oe_menu_toggler')) {
            $clicked_menu.toggleClass('oe_menu_opened').siblings('.oe_secondary_submenu:first').toggle();
        } else {
            self.$secondary_menu.find('.active').removeClass('active');
            $clicked_menu.parent().addClass('active');
        }

        // add a tooltip to cropped menu items
        this.$secondary_menu.find('.oe_secondary_submenu li a span').each(function() {
            $(this).tooltip(this.scrollWidth > this.clientWidth ? {title: $(this).text().trim(), placement: 'right'} :'destroy');
       });

        self.current_secondary_menu = menu_id;
        self.trigger('secondary_menu_click', {id: menu_id});
    },
    /**
     * Find the menu id associated to an action id by querying the DOM and then
     * run the decorate logic.
     */
    decorate_action: function(action_id) {
        var menu_id = this._action_id_to_menu_id(action_id);
        if (this.$primary_menu.find('a[data-menu=' + menu_id + ']').length) {
            this.decorate_primary_menu(menu_id);
        } else {
            this.decorate_secondary_menu(menu_id);
        }
    },
    _trigger_menu_click: function(menu_id, action_id, needaction) {
        this.trigger('menu_click', {
            id: menu_id,
            action_id: action_id,
            needaction: needaction,
            previous_menu_id: this.current_secondary_menu || this.current_primary_menu,
        });
    },
    _on_primary_menu_click: function(menu_id, action_id, needaction) {
        var self = this;
        self.decorate_primary_menu(menu_id);

        if (action_id) {
            self._trigger_menu_click(menu_id, action_id, needaction);
        }

        self.is_mobile_layout() ? self.slide('secondary') : self.slide('primary');
    },
    _on_secondary_menu_click: function(menu_id, action_id, needaction) {
        var self = this;
        self.decorate_secondary_menu(menu_id);

        action_id = action_id ? action_id : self._menu_id_to_action_id(menu_id);

        // It is still possible that we don't have an action_id (for example, menu toggler)
        if (action_id) {
            // Trigger an event to inform the action manager of the clicked menu
            self._trigger_menu_click(menu_id, action_id, needaction);
        }

        self.slide('initial');
    },
    open_menu: function(menu_id) {
        if (this.$primary_menu.find('a[data-menu=' + menu_id + ']').length) {
            var $item = this.$secondary_menu.find("div[data-menu-parent=" + menu_id + "]").find('a:first');
            this._on_secondary_menu_click($item.data('menu'));
        } else {
            this._on_secondary_menu_click(menu_id);
        }
    },
    /**
     * Open the webclient's default action. Done by querying the DOM of the
     * first menu item.
     */
    open_default_action: function() {
        var $menu_item = this.$secondary_menu.find('a:first');
        this._on_secondary_menu_click($menu_item.data('menu'), $menu_item.data('action-id'));
    },
});

return Menu;
});
