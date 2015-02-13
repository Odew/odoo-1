openerp.project_timesheet = function(openerp) {

	//Main widget to instantiate the app
	openerp.project_timesheet.ProjectTimesheet = openerp.Widget.extend({
		//template:"test_screen",
		init: function(){

		},
		start: function(){
			self = this;
			this.load_template().then(function(){
				self.build_widgets();
			});
		},
		load_template: function(){
            var self = this;
            return openerp.session.rpc('/web/proxy/load', {path: "/project_timesheet/static/src/xml/project_timesheet.xml"}).then(function(xml) {
                openerp.qweb.add_template(xml);
            });
        },
        build_widgets: function(){
        	screenWidget = new openerp.project_timesheet.Activites_screen();	
        	screenWidget.appendTo(this.$el);
        }
	});

	// Basic screen widget, inherited by all screens
	openerp.project_timesheet.BasicScreenWidget = openerp.Widget.extend({
		init: function(){

		},
		start: function(){

		}
	});

	openerp.project_timesheet.Activites_screen = openerp.project_timesheet.BasicScreenWidget.extend({
        template: "activities_screen",
        init: function() {
            self = this;
            // self._super.apply(this, arguments);
            // self.project_timesheet_widget = project_timesheet_widget;
            self.screen_name = "Activities";
            // self.project_timesheet_model = options.project_timesheet_model;

            // Events specific to this screen
            _.extend(self.events,
                {
                    "click .pt_button_plus_activity":"goto_edit_activity_screen",
                    "click .pt_activity":"edit_activity",
                    "click .pt_btn_start_activity":"start_activity",
                    "click .pt_test_btn":"test_fct"
                }
            );

            // self.projects = self.project_timesheet_model.projects;
            // self.tasks = self.project_timesheet_model.tasks;
            // self.account_analytic_lines = self.project_timesheet_model.account_analytic_lines;

            // _.each(self.account_analytic_lines, function(account_analytic_line){
            //     account_analytic_line.hours_minutes = project_timesheet.unit_amount_to_hours_minutes(account_analytic_line.unit_amount);
            // });
        },
        //Go to the create / edit activity
        goto_edit_activity_screen: function(){
            // => chemin d'accès à l'activité du widget d'édition. à modifier avec les infos récupérées lors du click sur une acti
            // this.project_timesheet_widget.edit_activity_screen.activity;
            this.project_timesheet_widget.edit_activity_screen.reset_activity();
            this.project_timesheet_widget.screen_selector.set_current_screen("edit_activity_screen");
        },
        // Go to the edit screen to edit a specific activity
        edit_activity: function(event){
            this.project_timesheet_widget.edit_activity_screen.re_render(event.currentTarget.dataset.activity_id);
            this.project_timesheet_widget.screen_selector.set_current_screen("edit_activity_screen");
        },
        start_activity: function(){

        },
        // test_fct: function(){
        //     this.project_timesheet_model.load_server_data();
        // }
    });

    // openerp.project_timesheet.Day_planner_screen = project_timesheet.BasicScreenWidget.extend({
    //     template: "day_planner_screen",
    //     init: function(project_timesheet_widget, options) {
    //         this._super.apply(this, arguments);
    //         this.project_timesheet_widget = project_timesheet_widget;
    //         this.screen_name = "Day Planner";

    //         _.extend(self.events,
    //             {
    //                 "click .pt_day_plan_select":"add_to_day_plan"
    //             }
    //         );

    //         this.tasks = options.project_timesheet_model.tasks;
    //     },
    //     add_to_day_plan: function(event){
    //         console.log(event.currentTarget.dataset.task_id);
    //     }
    // });

    // openerp.project_timesheet.Settings_screen = project_timesheet.BasicScreenWidget.extend({
    //     template: "settings_screen",
    //     init: function(project_timesheet_widget, options) {
    //         this._super.apply(this, arguments);
    //         this.project_timesheet_widget = project_timesheet_widget;
    //         this.screen_name = "Settings";
    //         this.project_timesheet_model = options.project_timesheet_model;

    //         _.extend(self.events,
    //             {
    //                 "change input.pt_minimal_duration":"on_change_minimal_duration",
    //                 "change input.pt_time_unit":"on_change_time_unit",
    //                 "click .pt_default_project":"on_change_default_project"
    //             }
    //         );

    //         this.settings = this.project_timesheet_model.settings;
    //     },
    //     on_change_minimal_duration: function(){
    //         this.project_timesheet_model.set_minimal_duration(this.$("input.pt_minimal_duration").val());
    //     },
    //     on_change_time_unit: function(){
    //         this.project_timesheet_model.set_time_unit(this.$("input.pt_time_unit").val());
    //     },
    //     on_change_default_project: function(event){
    //         this.project_timesheet_model.set_default_project(event.target.dataset.project_id);
    //         this.renderElement();
    //         this.goto_settings();
    //     }

    // });

    // openerp.project_timesheet.Edit_activity_screen = project_timesheet.BasicScreenWidget.extend({
    //     template: "edit_activity_screen",
    //     init: function(project_timesheet_widget, options) {
    //         this._super.apply(this, arguments);
    //         this.project_timesheet_widget = project_timesheet_widget;
    //         this.screen_name = "Edit Activity";
    //         this.project_timesheet_model = options.project_timesheet_model;

    //         _.extend(self.events,
    //             {
    //                 "click .pt_activity_project":"select_project",
    //                 "click .pt_activity_task":"select_task",
    //                 "change input.pt_activity_duration":"on_change_duration",
    //                 "change textarea.pt_description":"on_change_description",
    //                 "click .pt_project_create_confirm":"create_project",
    //                 "click .pt_discard_changes":"discard_changes",
    //                 "click .pt_validate_edit_btn" : "save_changes"
    //             }
    //         );

    //         this.tasks = {};
    //         this.activity = {
    //             project: undefined,
    //             task: undefined,
    //             desc:"/",
    //             unit_amount: undefined,
    //             date: (project_timesheet.date_to_str(new Date()))
    //         };
    //     },
    //     select_project: function(event){
    //         var project_id = parseInt(event.currentTarget.dataset.project_id);
    //         this.activity.project = _.findWhere(this.project_timesheet_model.projects, {id : project_id});
    //         this.activity.task = undefined;
    //         this.tasks = _.where(this.project_timesheet_model.tasks, {project_id : project_id});
    //         this.renderElement();
    //     },
    //     select_task: function(event){
    //         var task_id = parseInt(event.currentTarget.dataset.task_id);
    //         this.activity.task = _.findWhere(this.tasks, {id : task_id});
    //         this.renderElement();
    //     },
    //     create_project: function(){
    //         this.project_timesheet_model.create_project(this.$(".pt_new_project_name").val());
    //         this.$("#pt_project_creator").modal('hide');
    //     },
    //     on_change_duration: function(event){
    //         var duration = project_timesheet.validate_duration(this.$("input.pt_activity_duration").val());
    //         if(_.isUndefined(duration)){
    //             this.$("input.pt_activity_duration").val("00:00");
    //             this.$("input.pt_activity_duration + p").text("Please entre a valid duration in the hh:mm format, such as 01:30");
    //         }
    //         else{
    //             this.$("input.pt_activity_duration").val(duration);
    //             this.$("input.pt_activity_duration + p").text("");
                
    //             this.activity.unit_amount = project_timesheet.hh_mm_to_unit_amount(duration);
    //         }
    //     },
    //     on_change_description: function(event){
    //         this.activity.desc = this.$("textarea.pt_description").val();
    //     },
    //     // Function to re-render the screen with a new activity.
    //     // we use clone to work on a temporary version of activity.
    //     re_render: function(activity_id){
    //         this.activity = _.clone(_.findWhere(project_timesheet.project_timesheet_model.account_analytic_lines,  {id:parseInt(activity_id)}));

    //         if(!_.isUndefined(this.activity.project)){
    //             this.tasks = _.where(this.project_timesheet_model.tasks, {project_id : this.activity.project.id});
    //         }
    //         this.renderElement();
    //     },
    //     save_changes: function(){
    //         //TODO Save here

    //         //To empty screen data
    //         this.reset_activity();
    //         this.goto_welcome_screen();
    //     },
    //     discard_changes: function(){
    //         this.reset_activity();
    //         this.goto_welcome_screen();
    //     },
    //     reset_activity: function(){
    //         this.activity = {
    //             project: undefined,
    //             task: undefined,
    //             desc:"/",
    //             unit_amount: undefined,
    //             date: (project_timesheet.date_to_str(new Date()))
    //         };

    //         if (!_.isUndefined(this.project_timesheet_model.settings.default_project)){
    //             this.activity.project = this.project_timesheet_model.settings.default_project;
    //             this.tasks = _.where(this.project_timesheet_model.tasks, {project_id : this.activity.project.id});
    //         }

    //         this.renderElement();
    //     }
    // });
};