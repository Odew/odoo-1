(function () {
    'use strict';

openerp.define.active();

define(['summernote/openerp'], function () {

    var _t = openerp._t;

    //////////////////////////////////////////////////////////////////////////////////////////////////////////
    /* Summernote Lib (neek change to make accessible: method and object) */
    var web_editor = openerp.web_editor;
    var dom = $.summernote.core.dom;
    var range = $.summernote.core.range;

    //////////////////////////////////////////////////////////////////////////////////////////////////////////
    /* Change History to have a global History for all summernote instances */

    web_editor.History = function History ($editable) {
        var aUndo = [];
        var pos = 0;

        this.makeSnap = function () {
            var rng = range.create(),
                elEditable = dom.ancestor(rng && rng.commonAncestor(), dom.isEditable) || $('.o_editable:first')[0];
            return {
                editable: elEditable,
                contents: elEditable.innerHTML,
                bookmark: rng && rng.bookmark(elEditable),
                scrollTop: $(elEditable).scrollTop()
            };
        };

        this.applySnap = function (oSnap) {
            var $editable = $(oSnap.editable);

            if (!!document.documentMode) {
                $editable.removeAttr("contentEditable").removeProp("contentEditable");
            }

            $editable.html(oSnap.contents).scrollTop(oSnap.scrollTop);
            $(".oe_overlay").remove();
            $(".note-control-selection").hide();
            
            $editable.trigger("content_changed");

            if (!oSnap.bookmark) {
                return;
            }

            try {
                var r = range.createFromBookmark(oSnap.editable, oSnap.bookmark);
                r.select();
            } catch(e) {
                console.error(e);
                return;
            }

            $(document).trigger("click");
            $(".o_editable *").filter(function () {
                var $el = $(this);
                if($el.data('snippet-editor')) {
                    $el.removeData();
                }
            });

            setTimeout(function () {
                var target = dom.isBR(r.sc) ? r.sc.parentNode : dom.node(r.sc);
                if (!target) {
                    return;
                }
                var evt = document.createEvent("MouseEvents");
                evt.initMouseEvent("mousedown", true, true, window, 0, 0, 0, 0, 0, false, false, false, false, 0, target);
                target.dispatchEvent(evt);

                var evt = document.createEvent("MouseEvents");
                evt.initMouseEvent("click", true, true, window, 0, 0, 0, 0, 0, false, false, false, false, 0, target);
                target.dispatchEvent(evt);
            },0);
        };

        this.undo = function () {
            if (!pos) { return; }
            last = null;
            if (!aUndo[pos]) aUndo[pos] = this.makeSnap();
            if (aUndo[pos-1].jump) pos--;
            this.applySnap(aUndo[--pos]);
        };
        this.hasUndo = function () {
            return pos > 0;
        };

        this.redo = function () {
            if (aUndo.length <= pos+1) { return; }
            if (aUndo[pos].jump) pos++;
            this.applySnap(aUndo[++pos]);
        };
        this.hasRedo = function () {
            return aUndo.length > pos+1;
        };

        this.popUndo = function () {
            pos--;
            aUndo.pop();
        };

        var last;
        this.recordUndo = function ($editable, event, internal_history) {
            if (!internal_history) {
                if (!event || !last || !aUndo[pos-1] || aUndo[pos-1].editable !== $editable[0]) { // don't trigger change for all keypress
                    $(".o_editable.note-editable").trigger("content_changed");
                }
            }
            if (event) {
                if (last && aUndo[pos-1] && aUndo[pos-1].editable !== $editable[0]) {
                    // => make a snap when the user change editable zone (because: don't make snap for each keydown)
                    aUndo.splice(pos, aUndo.length);
                    var prev = aUndo[pos-1];
                    aUndo[pos] = {
                        editable: prev.editable,
                        contents: $(prev.editable).html(),
                        bookmark: prev.bookmark,
                        scrollTop: prev.scrollTop,
                        jump: true
                    };
                    pos++;
                }
                else if (event === last) return;
            }
            last = event;
            aUndo.splice(pos, aUndo.length);
            aUndo[pos] = this.makeSnap($editable);
            pos++;
        };

        this.splitNext = function () {
            last = false;
        };
    };
    web_editor.history = new web_editor.History();

    //////////////////////////////////////////////////////////////////////////////////////////////////////////
    // add focusIn to jQuery to allow to move caret into a div of a contentEditable area

    $.fn.extend({
        focusIn: function () {
            if (this.length) {
                range.create(dom.firstChild(this[0]), 0).select();
            }
            return this;
        },
        focusInEnd: function () {
            if (this.length) {
                var last = dom.lastChild(this[0]);
                range.create(last, dom.nodeLength(last)).select();
            }
            return this;
        },
        selectContent: function () {
            if (this.length) {
                var next = dom.lastChild(this[0]);
                range.create(dom.firstChild(this[0]), 0, next, next.textContent.length).select();
            }
            return this;
        },
        activateBlock: function () {
            var target = web_editor.snippet.globalSelector.closest($(this))[0] || (dom.isBR(this) ? this.parentNode : dom.node(this));
            var evt = document.createEvent("MouseEvents");
            evt.initMouseEvent("click", true, true, window, 0, 0, 0, 0, 0, false, false, false, false, 0, target);
            target.dispatchEvent(evt);
            return this;
        }
    });

    //////////////////////////////////////////////////////////////////////////////////////////////////////////

    function change_default_bootstrap_animation_to_edit() {
        var fn_carousel = $.fn.carousel;
        $.fn.carousel = function () {
            var res = fn_carousel.apply(this, arguments);
            // off bootstrap keydown event to remove event.preventDefault()
            // and allow to change cursor position
            $(this).off('keydown.bs.carousel');
            return res;
        };
    }

    /* ----- RICH TEXT EDITOR ---- */

    web_editor.RTE = openerp.Widget.extend({
        init: function (EditorBar) {
            this.EditorBar = EditorBar;
            $('.inline-media-link').remove();
            this._super.apply(this, arguments);
        },
        /**
         * Add a record undo to history
         * @param {DOM} target where the dom is changed is editable zone
         */
        historyRecordUndo: function ($target, internal_history) {
            var rng = range.create();
            var $editable = $($target || (rng && rng.sc)).closest(".o_editable");
            if ($editable.length) {
                rng = $editable.data('range') || rng;
            }
            if (!rng && $target.length) {
                rng = range.create($target[0],0);
            }
            if (rng) {
                try {
                    rng.select();
                } catch (e) {
                    console.error(e);
                }
            }
            $target = $(rng.sc);
            $target.mousedown();
            web_editor.history.recordUndo($target, null, internal_history);
            $target.mousedown();
        },
        /**
         * Makes the page editable
         *
         * @param {Boolean} [restart=false] in case the edition was already set
         *                                  up once and is being re-enabled.
         * @returns {$.Deferred} deferred indicating when the RTE is ready
         */
        start_edition: function (restart) {
            var self = this;

            change_default_bootstrap_animation_to_edit();

            // handler for cancel editor
            $(document).on('keydown', function (event) {
                if (event.keyCode === 27 && !$('.modal-content:visible').length) {
                    setTimeout(function () {
                        $('#web_editor-top-navbar [data-action="cancel"]').click();
                        var $modal = $('.modal-content > .modal-body').parents(".modal:first");
                        $modal.off('keyup.dismiss.bs.modal');
                        setTimeout(function () {
                            $modal.on('keyup.dismiss.bs.modal', function () {
                                $(this).modal('hide');
                            });
                        },500);
                    },0);
                }
            });

            // activate editor
            var $last;
            $(document).on('mousedown', function (event) {
                var $target = $(event.target);
                var $editable = $target.closest('.o_editable');

                if (!$editable.size()) {
                    return;
                }

                if ($last && (!$editable.size() || $last[0] != $editable[0])) {
                    var $destroy = $last;
                    setTimeout(function () {$destroy.destroy();},150); // setTimeout to remove flickering when change to editable zone (re-create an editor)
                    $last = null;
                }
                if ($editable.size() && (!$last || $last[0] != $editable[0]) &&
                        ($target.closest('[contenteditable]').attr('contenteditable') || "").toLowerCase() !== 'false') {
                    $editable.summernote(self._config());
                    $editable.data('NoteHistory', web_editor.history);
                    $editable.data('rte', self);
                    $last = $editable;

                    // firefox & IE fix
                    try {
                        document.execCommand('enableObjectResizing', false, false);
                        document.execCommand('enableInlineTableEditing', false, false);
                        document.execCommand( '2D-position', false, false);
                    } catch (e) {}
                    document.body.addEventListener('resizestart', function (evt) {evt.preventDefault(); return false;});
                    document.body.addEventListener('movestart', function (evt) {evt.preventDefault(); return false;});
                    document.body.addEventListener('dragstart', function (evt) {evt.preventDefault(); return false;});

                    if (!range.create()) {
                        range.create($editable[0],0).select();
                    }

                    $target.trigger('mousedown'); // for activate selection on picture
                    setTimeout(function () {
                        self.historyRecordUndo($editable, true);
                    },0);
                }
            });

            $('.o_not_editable').attr("contentEditable", false);

            this.editable().addClass('o_editable');

            $('.o_editable').each(function () {
                var node = this;
                var $node = $(node);

                // add class to display inline-block for empty t-field
                if(window.getComputedStyle(node).display === "inline" && $node.data('oe-type') !== "image") {
                    $node.addClass('o_is_inline_editable');
                }

                // start element observation
                $(node).one('content_changed', function () {
                    $node.addClass('o_dirty');
                });
                $(node).on('content_changed', function () {
                    self.trigger('change');
                });
            });

            $(document).trigger('mousedown');

            if (!restart) {
                $('#wrapwrap, .o_editable').on('click', '*', function (event) {
                    event.preventDefault();
                });

                $('body').addClass("editor_enable");

                $(document)
                    .tooltip({
                        selector: '[data-oe-readonly]',
                        container: 'body',
                        trigger: 'hover',
                        delay: { "show": 1000, "hide": 100 },
                        placement: 'bottom',
                        title: _t("Readonly field")
                    })
                    .on('click', function () {
                        $(this).tooltip('hide');
                    });

                self.trigger('rte:ready');
            }
        },

        editable: function () {
            return $('#wrapwrap [data-oe-model]')
                .not('.o_not_editable')
                .filter(function () {
                    return !$(this).closest('.o_not_editable').length;
                })
                .not('link, script')
                .not('[data-oe-readonly]')
                .not('img[data-oe-field="arch"], br[data-oe-field="arch"], input[data-oe-field="arch"]')
                .not('.oe_snippet_editor')
                .add('.o_editable');
        },

        _config: function () {
            return {
                'airMode' : true,
                'focus': false,
                'airPopover': [
                    ['style', ['style']],
                    ['font', ['bold', 'italic', 'underline', 'clear']],
                    ['fontsize', ['fontsize']],
                    ['color', ['color']],
                    ['para', ['ul', 'ol', 'paragraph']],
                    ['table', ['table']],
                    ['insert', ['link', 'picture']],
                    ['history', ['undo', 'redo']],
                ],
                'styleWithSpan': false,
                'inlinemedia' : ['p'],
                'lang': "odoo",
                'onChange': function (html, $editable) {
                    $editable.trigger("content_changed");
                }
            };
        }
    });

});

openerp.define.desactive();

})();
