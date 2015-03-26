(function () {
    'use strict';

    (function($) {
        $.fn.bindFirst = function(/*String*/ eventType, /*[Object])*/ eventData, /*Function*/ handler) {
            var indexOfDot = eventType.indexOf(".");
            var eventNameSpace = indexOfDot > 0 ? eventType.substring(indexOfDot) : "";

            eventType = indexOfDot > 0 ? eventType.substring(0, indexOfDot) : eventType;
            handler = handler == undefined ? eventData : handler;
            eventData = typeof eventData == "function" ? {} : eventData;

            return this.each(function() {
                var $this = $(this);
                var currentAttrListener = this["on" + eventType];

                if (currentAttrListener) {
                    $this.bind(eventType, function(e) {
                        return currentAttrListener(e.originalEvent);
                    });

                    this["on" + eventType] = null;
                }

                $this.bind(eventType + eventNameSpace, eventData, handler);

                var allEvents = $this.data("events") || $._data($this[0], "events");
                var typeEvents = allEvents[eventType];
                var newEvent = typeEvents.pop();
                typeEvents.unshift(newEvent);
            });
        };
    })(jQuery);


    var web_editor = openerp.web_editor;
    web_editor.Translate = openerp.Widget.extend({
        do_not_translate : ['-','*','!'],
        init: function (parent, $target, model, id, field, lang) {
            this.parent = parent;

            this.setTarget($target);

            this.model = model;
            this.id = id;
            this.field = field;
            this.lang = lang || web_editor.get_context().lang;

            this.initial_content = {};

            this._super();
        },
        setTarget: function ($target) {
            this.$target = $target
                .not('link, script')
                .filter('[data-oe-field=arch], [data-oe-type][data-oe-translate!=0]');
        },
        find: function (selector) {
            return selector ? this.$target.find(selector).addBack().filter(selector) : this.$target;
        },
        edit: function () {
            return this.translate().then(_.bind(this.onTranslateReady, this));
        },
        translate: function () {
            var self = this;
            this.translations = null;
            return openerp.jsonRpc('/web_editor/get_view_translations', 'call', {
                'xml_id': this.id,
                'lang': this.lang,
            }).then(function (translations) {
                self.translations = translations;
                self.processTranslatableNodes();
            });
        },
        onTranslateReady: function () {
            this.trigger("edit");
        },
        processTranslatableNodes: function () {
            var self = this;
            this.$target.each(function () {
                var $node = $(this);
                var $object = $node.closest('[data-oe-id]');
                var view_id = $object.attr('data-oe-source-id') || $object.attr('data-oe-id') | 0;
                self.transNode(this, view_id);
            });
            this.find('.o_translatable_text').on('paste', function () {
                var node = $(this);
                setTimeout(function () {
                    self.sanitizeNode(node);
                }, 0);
            });
            $(document).on('keyup paste', '.o_translatable_text, .o_translatable_field', function(ev) {
                var $node = $(this);
                setTimeout(function () {
                    // Doing stuff next tick because paste and keyup events are
                    // fired before the content is changed
                    if (ev.type == 'paste') {
                        self.sanitizeNode($node[0]);
                    }

                    var $nodes = $node;
                    if ($node.attr('data-oe-nodeid')) {
                        $nodes = $nodes.add(self.find('[data-oe-nodeid=' + $node.attr('data-oe-nodeid') + ']').each(function () {
                            if ($node[0] !== this) self.setText(this, $node.text());
                        }));
                    }

                    if (self.getInitialContent($node[0]) !== $node.text().trim()) {
                        $nodes.addClass('o_dirty');
                        if ($node.hasClass('o_translatable_todo_r')) {
                            $nodes.removeClass('o_translatable_todo').addClass('o_translatable_todo_r');
                        }
                        if ($node.hasClass('o_translatable_inprogress_r')) {
                            $nodes.removeClass('o_translatable_inprogress').addClass('o_translatable_inprogress_r');
                        }
                    } else {
                        $nodes.removeClass('o_dirty');
                        if ($node.hasClass('o_translatable_todo_r')) {
                            $nodes.addClass('o_translatable_todo').removeClass('o_translatable_todo_r');
                        }
                        if ($node.hasClass('o_translatable_inprogress_r')) {
                            $nodes.addClass('o_translatable_inprogress').removeClass('o_translatable_inprogress_r');
                        }
                    }
                }, 0);
            });
        },
        getInitialContent: function (node) {
            return this.initial_content[node.getAttribute('data-oe-nodeid')];
        },
        sanitizeNode: function (node) {
            node.text(node.text());
        },
        isTranslatableNode: function (node) {
            return  node.nodeType === 3 || node.nodeType === 4 || !$(node).find("p,div,h1,h2,h3,h4,h5,h6,li,td,th").length;
        },
        isTranslatable: function (node) {
            return node.textContent && !!node.textContent.match(/[a-z]/i);
        },
        setText: function (node, text) {
            node.textContent = node.getAttribute('data-oe-translate-space-before') + _.str.trim(text) + node.getAttribute('data-oe-translate-space-after');
        },
        transNode: function (node, view_id) {
            if (node.childNodes.length === 1
                    && this.isTranslatableNode(node.childNodes[0])
                    && !node.getAttribute('data-oe-model')) {
                this.markTranslatableNode(node, view_id);
            } else {
                for (var i = 0, l = node.childNodes.length; i < l; i ++) {
                    var n = node.childNodes[i];
                    if (this.isTranslatableNode(n)) {
                        if (this.isTranslatable(n)) {
                            var container = document.createElement('span');
                            container.className = "o_translatable_ghost_node";
                            node.insertBefore(container, n);
                            container.appendChild(n);
                            this.markTranslatableNode(container, view_id);
                        }
                    } else {
                        this.transNode(n, view_id);
                    }
                }
            }

            this.$target.bindFirst('click', this._cancelClick);
        },
        _cancelClick: function (event) {
            event.preventDefault();
            event.stopPropagation();
        },
        getTranslateContent: function (node) {
            var text = "";
            if (node.nodeType === 3 || node.nodeType === 4) {
                if (node.data.match(/\S|\u00A0/)) {
                    text += node.data;
                }
            } else {
                for (var k=0,len=node.childNodes.length; k<len; k++) {
                    var n = node.childNodes[k];
                    if (n.nodeType === 3 || n.nodeType === 4) {
                    }
                    text += this.getTranslateContent(n);
                }
            }

            return text.trim().replace(/[ \t\r\n]+/, " ");
        },
        markTranslatableNode: function (node, view_id) {
            var is_field = !!$(node).closest("[data-oe-type]").length;

            console.log(  this.getTranslateContent(node)  );

            var content = node.childNodes[0].textContent.trim();
            var nid = _.findKey(this.initial_content, function (v, k) { return v === content;});

            if (!is_field) {
                node.className += ' o_translatable_text';
                node.setAttribute('data-oe-translation-view-id', view_id);

                var trans = this.translations.filter(function (t) {
                    return t.res_id === view_id && t.value.trim() === content;
                });
                if (trans.length) {
                    node.setAttribute('data-oe-translation-id', trans[0].id);
                    if(trans[0].state && (trans[0].state == 'inprogress' || trans[0].state == 'to_translate')){
                        node.className += ' o_translatable_inprogress';
                    }
                } else {
                    node.className += this.do_not_translate.indexOf(node.textContent.trim()) ? ' o_translatable_todo' : '';
                }
            } else {
                node.className += ' o_translatable_field';
            }

            nid = nid || _.uniqueId();
            node.setAttribute('data-oe-nodeid', nid);
            node.setAttribute('contentEditable', true);
            var space = node.textContent.match(/^([\s]*)[\s\S]*?([\s]*)$/);
            node.setAttribute('data-oe-translate-space-before', space[1] || '');
            node.setAttribute('data-oe-translate-space-after', space[2] || '');

            this.initial_content[nid] = content;
        },
        save: function () {
            var self = this;
            var keys = {};
            var trans = [];
            this.find('.o_translatable_text.o_dirty').each(function () {
                var content = self.getInitialContent(this);
                if (keys[content]) return;
                keys[content] = true;

                var oeTranslationViewId = this.getAttribute('data-oe-translation-view-id') | 0;
                trans.push({
                    'initial_content':  content,
                    'new_content':      _.str.trim($(this).text()),
                    'model':            'ir.ui.view',
                    'id':               oeTranslationViewId,
                    'field':            'arch',
                    'translation_id':   (this.getAttribute('data-oe-translation-id') | 0) || null
                });
            });

            this.find('.o_translatable_field.o_dirty').each(function () {
                var $node = $(this).closest("[data-oe-type]");

                var content = self.getInitialContent(this);
                if (keys[content]) return;
                keys[content] = true;

                trans.push({
                    'initial_content':  content,
                    'new_content':      _.str.trim($(this).text()),
                    'model':            $node.attr('data-oe-model') || null,
                    'id':               ($node.attr('data-oe-id') | 0) || null,
                    'field':            $node.attr('data-oe-field') || null,
                    'translation_id':   ($node.attr('data-oe-translation-id') | 0) || null
                });
            });

            console.log("TO DO translate for t-field and for html field");
            console.log(trans);

            return openerp.jsonRpc('/web_editor/set_translations', 'call', {
                'data': trans,
                'lang': this.lang,
            }).then(function () {
                self.unarkTranslatableNode();
                self.trigger("saved");
            }).fail(function () {
                // TODO: bootstrap alert with error message
                alert("Could not save translation");
            });
        },
        unarkTranslatableNode: function () {
            this.find('.o_translatable_ghost_node').each(function () {
                this.parentNode.insertBefore(this.firstChild, this);
                this.parentNode.removeChild(this);
            });

            this.find('.o_translatable_text, .o_translatable_field')
                .removeClass('o_translatable_text o_translatable_todo o_translatable_inprogress o_translatable_field o_dirty')
                .removeAttr('data-oe-nodeid')
                .removeAttr('data-oe-translation-id')
                .removeAttr('data-oe-translation-view-id')
                .removeAttr('data-oe-translation-space-before')
                .removeAttr('data-oe-translation-space-after')
                .removeAttr('contentEditable')
                .each(function () {
                    if (!this.className.match(/\S/)) {
                        this.removeAttribute("class");
                    }
                });

            this.$target.off('click', this._cancelClick);
        },
        cancel: function () {
            var self = this;
            this.find('.o_translatable_text').each(function () {
                self.setText(this, self.getInitialContent(this));
            });
            this.unarkTranslatableNode();
            this.trigger("cancel");
        },
        destroy: function () {
            this.cancel();
            this._super();
        }
    });

})();
