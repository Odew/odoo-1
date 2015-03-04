(function () {
    'use strict';

    /* ----- default options ---- */
    var web_editor = openerp.web_editor;
    var snippet = web_editor.snippet;

    /* ----- Editor option (object link the the xml with data-js) ---- */

    snippet.options = {};
    snippet.Option = openerp.Class.extend({
        // initialisation (don't overwrite)
        init: function (BuildingBlock, editor, $target, option_id) {
            this.BuildingBlock = BuildingBlock;
            this.editor = editor;
            this.$target = $target;
            var option = this.BuildingBlock.templateOptions[option_id];
            var styles = this.$target.data("snippet-option-ids") || {};
            styles[option_id] = this;
            this.$target.data("snippet-option-ids", styles);
            this.$overlay = this.$target.data('overlay') || $('<div>');
            this.option= option_id;
            this.$el = option.$el.find(">li").clone();
            this.data = option.$el.data();
        },

        // helper for this.$target.find
        $: function (selector) {
            return this.$target(selector);
        },

        _bind_li_menu: function () {
            this.$el.filter("li:hasData").find('a:first')
                .off('mouseenter click')
                .on('mouseenter click', _.bind(this._mouse, this));

            this.$el
                .off('mouseenter click', "li:hasData a")
                .on('mouseenter click', "li:hasData a", _.bind(this._mouse, this));

            this.$el.closest("ul").add(this.$el)
                .off('mouseleave')
                .on('mouseleave', _.bind(this.reset, this));

            this.$el
                .off('mouseleave', "ul")
                .on('mouseleave', "ul", _.bind(this.reset, this));

            this.reset_methods = [];
        },

        /**
         * this method handles mouse:over and mouse:leave on the snippet editor menu
         */
         _time_mouseleave: null,
        _mouse: function (event) {
            var $next = $(event.currentTarget).parent();

            // triggers preview or apply methods if a menu item has been clicked
            this.select(event.type === "click" ? "click" : "over", $next);
            if (event.type === 'click') {
                this.set_active();
                this.$target.trigger("snippet-option-change", [this]);
            } else {
                this.$target.trigger("snippet-option-preview", [this]);
            }
        },
        /* 
        *  select and set item active or not (add highlight item and his parents)
        *  called before start
        */
        set_active: function () {
            var classes = _.uniq((this.$target.attr("class") || '').split(/\s+/));
            this.$el.find('[data-toggle_class], [data-select_class]')
                .add(this.$el)
                .filter('[data-toggle_class], [data-select_class]')
                .removeClass("active")
                .filter('[data-toggle_class="' + classes.join('"], [data-toggle_class="') + '"] ,'+
                    '[data-select_class="' + classes.join('"], [data-select_class="') + '"]')
                .addClass("active");
        },

        start: function () {
            this.set_active();
            this.$target.on('snippet-option-reset', _.bind(this.set_active, this));
            this._bind_li_menu();
        },

        on_focus : function () {
            this._bind_li_menu();
        },

        on_blur : function () {
        },

        on_clone: function ($clone) {
        },

        on_remove: function () {
        },

        drop_and_build_snippet: function () {
        },

        reset: function () {
            var self = this;
            var lis = self.$el.add(self.$el.find('li')).filter('.active').get();
            lis.reverse();
            _.each(lis, function (li) {
                var $li = $(li);
                for (var k in self.reset_methods) {
                    var method = self.reset_methods[k];
                    if ($li.is('[data-'+method+']') || $li.closest('[data-'+method+']').size()) {
                        delete self.reset_methods[k];
                    }
                }
                self.select("reset", $li);
            });

            for (var k in self.reset_methods) {
                var method = self.reset_methods[k];
                if (method) {
                    self[method]("reset", null);
                }
            }
            self.reset_methods = [];
            self.$target.trigger("snippet-option-reset", [this]);
        },

        // call data-method args as method (data-only can be used)
        select: function (type, $li) {
            var self = this,
                $methods = [],
                el = $li[0],
                $el;

            if ($li.data('only') && type !== $li.data('only')) {
                return;
            }

            if (type==="click") {
                this.reset();
                this.BuildingBlock.parent.rte.historyRecordUndo(this.$target);
            }

            function filter (k) { return k !== 'oeId' && k !== 'oeModel' && k !== 'oeField' && k !== 'oeXpath' && k !== 'oeSourceId' && k !== 'only';}
            function hasData(el) {
                for (var k in el.dataset) {
                    if (filter (k)) {
                        return true;
                    }
                }
                return false;
            }
            function method(el) {
                var data = {};
                for (var k in el.dataset) {
                    if (filter (k)) {
                        data[k] = el.dataset[k];
                    }
                }
                return data;
            }

            while (el && this.$el.is(el) || _.some(this.$el.map(function () {return $.contains(this, el);}).get()) ) {
                if (hasData(el)) {
                    $methods.push(el);
                }
                el = el.parentNode;
            }

            $methods.reverse();

            _.each($methods, function (el) {
                var $el = $(el);
                var methods = method(el);

                for (var k in methods) {
                    if (self[k]) {
                        if (type !== "reset" && self.reset_methods.indexOf(k) === -1) {
                            self.reset_methods.push(k);
                        }
                        self[k](type, methods[k], $el);
                    } else {
                        console.error("'"+self.option+"' snippet have not method '"+k+"'");
                    }
                }
            });
        },

        // default method for snippet
        toggle_class: function (type, value, $li) {
            var $lis = this.$el.find('[data-toggle_class]').add(this.$el).filter('[data-toggle_class]');

            function map ($lis) {
                return $lis.map(function () {return $(this).data("toggle_class");}).get().join(" ");
            }
            var classes = map($lis);
            var active_classes = map($lis.filter('.active, :has(.active)'));

            this.$target.removeClass(classes);
            this.$target.addClass(active_classes);

            if (type !== 'reset') {
                this.$target.toggleClass(value);
            }
        },
        select_class: function (type, value, $li) {
            var $lis = this.$el.find('[data-select_class]').add(this.$el).filter('[data-select_class]');

            var classes = $lis.map(function () {return $(this).data('select_class');}).get();

            this.$target.removeClass(classes.join(" "));
            if(value) this.$target.addClass(value);
        },
        eval: function (type, value, $li) {
            var fn = new Function("node", "type", "value", "$li", value);
            fn.call(this, this, type, value, $li);
        },

        clean_for_save: snippet.dummy
    });

    /* ----- default options ---- */

    snippet.options.media = snippet.Option.extend({
        start: function () {
            this._super();
            snippet.start_animation(true, this.$target);
        },
        edition: function (type, value) {
            if(type !== "click") return;
            var self = this;
            var editor = new web_editor.widgets.MediaDialog(this.$target.closest('.o_editable'), this.$target[0]);
            editor.appendTo(document.body);
            editor.on('saved', this, function (item, old) {
                self.editor.on_blur();
                self.BuildingBlock.make_active(false);
                if (self.$target.parent().data("oe-field") !== "image") {
                    setTimeout(function () {
                        self.BuildingBlock.make_active($(item));
                    },0);
                }
            });
        },
        on_focus : function () {
            var self = this;
            var $parent = this.$target.parent();

            if ($parent.data("oe-field") === "image" && $parent.hasClass('o_editable')) {
                this.$overlay.addClass("hidden");
                self.edition('click', null);
                self.BuildingBlock.make_active(false);
            }
        }
    });

    snippet.options.colorpicker = snippet.Option.extend({
        start: function () {
            var self = this;
            var res = this._super();

            if (!this.$el.find('.colorpicker').length) {
                this.$el.find('li').append( openerp.qweb.render('web_editor.colorpicker') );
            }

            var classes = [];
            this.$el.find(".colorpicker button").map(function () {
                var $color = $(this);
                var color = $color.attr("class");
                if (self.$target.hasClass(color)) {
                    self.color = color;
                    $color.parent().addClass("selected");
                }
                classes.push(color);
            });
            this.classes = classes.join(" ");

            this.bind_events();
            return res;
        },
        bind_events: function () {
            var self = this;
            var $td = this.$el.find(".colorpicker td");
            var $colors = this.$el.find(".colorpicker button");
            $colors
                .mouseenter(function () {
                    self.$target.removeClass(self.classes).addClass($(this).attr("class"));
                })
                .mouseleave(function () {
                    self.$target.removeClass(self.classes)
                        .addClass($td.filter(".selected").children().attr("class"));
                })
                .click(function () {
                    $td.removeClass("selected");
                    $(this).parent().addClass("selected");
                });
        }
    });

    /* t-field options */

    snippet.options.many2one = snippet.Option.extend({
        start: function () {
            var self = this;

            this.Model = this.$target.data('oe-many2one-model');
            this.ID = +this.$target.data('oe-many2one-id');

            // create search button and bind search bar
            this.$btn = $(openerp.qweb.render("web_editor.many2one.button"))
                .insertAfter(this.$overlay.find('.oe_options'));

            this.$ul = this.$btn.find("ul");
            this.$search = this.$ul.find('li:first');
            this.$search.find('input').on('mousedown click mouseup keyup keydown', function (e) {
                e.stopPropagation();
            });

            // move menu item
            setTimeout(function () {
                if (self.$overlay.find('.oe_options').hasClass('hidden')) {
                    self.$btn.css('height', '0').find('> a').addClass('hidden');
                    self.$ul.show().css({
                        'top': '-24px', 'margin': '0', 'padding': '2px 0', 'position': 'relative'
                    });
                } else {
                    self.$btn.find('a').on('click', function (e) {
                        self.clear();
                    });
                }
            },0);

            // bind search input
            this.$search.find('input')
                .focus()
                .on('keyup', function(e) {
                    self.find_existing($(this).val());
                });

            // bind result
            this.$ul.on('click', "li:not(:first) a", function (e) {
                self.select_record(this);
            });
        },

        on_focus: function () {
            this.$target.attr('contentEditable', 'false');
            this.clear();
            this._super();
        },

        clear: function () {
            var self = this;
            this.$search.siblings().remove();
            self.$search.find('input').val("");
            setTimeout(function () {
                self.$search.find('input').focus();
            },0);
        },

        find_existing: function (name) {
            var self = this;
            var domain = [];
            if (!name || !name.length) {
                self.$search.siblings().remove();
                return;
            }
            if (isNaN(+name)) {
                if (this.Model === "res.partner") {
                    domain.push(['name', 'ilike', name]);
                } else {
                    domain.push('|', ['name', 'ilike', name], ['email', 'ilike', name]);
                }
            } else {
                domain.push(['id', '=', name]);
            }

            openerp.jsonRpc('/web/dataset/call_kw', 'call', {
                model: this.Model,
                method: 'search_read',
                args: [domain, this.Model === "res.partner" ? ['name', 'display_name', 'city', 'country_id'] : ['name', 'display_name']],
                kwargs: {
                    order: 'name DESC',
                    limit: 5,
                    context: web_editor.get_context(),
                }
            }).then(function (result){
                self.$search.siblings().remove();
                self.$search.after(openerp.qweb.render("web_editor.many2one.search",{contacts:result}));
            });
        },

        get_contact_rendering: function (options) {
            return openerp.jsonRpc('/web/dataset/call_kw', 'call', {
                model: 'ir.qweb.field.contact',
                method: 'get_record_to_html',
                args: [[this.ID]],
                kwargs: {
                    options: options,
                    context: web_editor.get_context(),
                }
            });
        },

        select_record: function (li) {
            var self = this;

            this.ID = +$(li).data("id");
            this.$target.attr('data-oe-many2one-id', this.ID).data('oe-many2one-id', this.ID);

            this.BuildingBlock.parent.rte.historyRecordUndo(this.$target);

            if (self.$target.data('oe-type') === "contact") {
                $('[data-oe-contact-options]')
                    .filter('[data-oe-model="'+self.$target.data('oe-model')+'"]')
                    .filter('[data-oe-id="'+self.$target.data('oe-id')+'"]')
                    .filter('[data-oe-field="'+self.$target.data('oe-field')+'"]')
                    .filter('[data-oe-contact-options!="'+self.$target.data('oe-contact-options')+'"]')
                    .add(self.$target)
                    .attr('data-oe-many2one-id', self.ID).data('oe-many2one-id', self.ID)
                    .each(function () {
                        var $node = $(this);
                        self.get_contact_rendering($node.data('oe-contact-options'))
                            .then(function (html){
                                $node.html(html);
                            });
                    });
            } else {
                self.$target.html($(li).data("name"));
            }

            setTimeout(function () {
                self.BuildingBlock.make_active(false);
            },0);
        }
    });


    /* end*/

})();
