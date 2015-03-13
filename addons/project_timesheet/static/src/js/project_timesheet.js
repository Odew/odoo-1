openerp.project_timesheet = function(openerp) {

	//Main widget to instantiate the app
	openerp.project_timesheet.ProjectTimesheet = openerp.Widget.extend({
		start: function(){
			self = this;

			// Load session, if there is any :
			this.session = new openerp.Session();
            this.session.session_reload().then(function(){
            	// Set demo data in local storage. TO REMOVE LATER
                var timestamp = (new Date()).getTime();
            	var test_data = [
	                {
	                    "session_user":"admin",
	                    "session_uid":1,
	                    "session_server":"http://localhost:8069",
	                    "data":{
	                    	"next_aal_id":9,
	                    	"next_project_id":3,
	                    	"next_task_id":4,
                            "module_key" : "Project_timesheet_UI_",
                            "original_timestamp" : timestamp,
	                        "settings":{
	                            "default_project_id":undefined,
	                            "minimal_duration":0.25,
	                            "time_unit":0.25
	                        },
	                        "projects":[],
	                        "tasks": [],
	                        "account_analytic_lines":[],
	                        "day_plan":[]
	                    }
	                },
	            ];
                // Comment or uncomment following line to reset demo data
            	//localStorage.setItem("pt_data", JSON.stringify(test_data));


            	// Load (demo) data from local storage
            	self.stored_data = JSON.parse(localStorage.getItem("pt_data"));
             	self.user_local_data = _.findWhere(self.stored_data, {session_user : self.session.username})
             	self.data = self.user_local_data.data;

             	//Load templates for widgets
            	self.load_template().then(function(){
					self.build_widgets();
				});
            });
		},
		load_template: function(){
            var self = this;
            return openerp.session.rpc('/web/proxy/load', {path: "/project_timesheet/static/src/xml/project_timesheet.xml"}).then(function(xml) {
                openerp.qweb.add_template(xml);
            });
        },
        build_widgets: function(){
        	this.activities_screen = new openerp.project_timesheet.Activities_screen(this);
        	this.activities_screen.appendTo(this.$el);
        	this.activities_screen.show();

        	this.day_planner_screen = new openerp.project_timesheet.Day_planner_screen(this);
        	this.day_planner_screen.appendTo(this.$el);
        	this.day_planner_screen.hide();

        	this.settings_screen = new openerp.project_timesheet.Settings_screen(this);
        	this.settings_screen.appendTo(this.$el);
        	this.settings_screen.hide();

        	this.edit_activity_screen = new openerp.project_timesheet.Edit_activity_screen(this);
        	this.edit_activity_screen.appendTo(this.$el);
        	this.edit_activity_screen.hide();
        },
        update_localStorage: function(){
        	localStorage.setItem("pt_data", JSON.stringify(this.stored_data));
        }
	});

	// Basic screen widget, inherited by all screens
	openerp.project_timesheet.BasicScreenWidget = openerp.Widget.extend({
		events:{
            "click .pt_day_planner_link" : "goto_day_planner",
            "click .pt_settings_link" : "goto_settings",
            "click .pt_activities_link" : "goto_activities",
            "click .pt_validate_btn" : "goto_activities"
        },
		init: function(parent){
			this._super(parent);
			this.data = this.getParent().data;
		},
		show: function(){
            this.$el.show();
        },
        hide: function(){
            this.$el.hide();
        },
		goto_day_planner: function(){
            this.hide();
            this.getParent().day_planner_screen.renderElement();
            this.getParent().day_planner_screen.show();
        },
        goto_settings: function(){
        	this.hide();
            this.getParent().settings_screen.renderElement();
            this.getParent().settings_screen.initialize_project_selector();
            this.getParent().settings_screen.show();
        },
        goto_activities: function(){
        	this.hide();
            this.getParent().activities_screen.renderElement();
            this.getParent().activities_screen.show();
        },
        // Methods that might be moved later if necessary :
        get_project_name: function(project_id){
        	project = _.findWhere(self.data.projects, {id : project_id});
        	if (!_.isUndefined(project)){
        		return project.name;
        	}
        	else{
        		return "No project selected yet";
        	}
        },
        get_task_name: function(task_id){
        	task = _.findWhere(self.data.tasks, {id : task_id});
        	if (!_.isUndefined(task)){
        		return task.name;
        	}
        	else{
        		return "No task selected yet";
        	}
        },
        get_project_name_from_task_id: function(task_id){
            task = _.findWhere(self.data.tasks, {id : task_id});
            if (!_.isUndefined(task)){
                project = _.findWhere(self.data.projects, {id : task.project_id});
                if (!_.isUndefined(project)){
                    return project.name;
                }
                else{
                    return "No project selected yet";
                }
            }
        },

        //Utility methods to format and validate time
        
        // Takes a decimal hours and converts it to hh:mm string representation
	    // e.g. 1.5 => "01:30"
	    unit_amount_to_hours_minutes: function(unit_amount){
	        if(_.isUndefined(unit_amount) || unit_amount === 0){
	            return ["00","00"];
	        }

	        var minutes = Math.round((unit_amount % 1) * 60);
	        var hours = Math.floor(unit_amount);

	        if(minutes < 10){
	            minutes = "0" + minutes.toString();
	        }
	        else{
	            minutes = minutes.toString();
	        }
	        if(hours < 10){
	            hours = "0" + hours.toString();
	        }
	        else{
	            hours = hours.toString();
	        }

	        return hours + ":" + minutes;
	    },

	    // Takes a string as input and tries to parse it as a hh:mm duration/ By default, strings without ":" are considered to be hh. 
	    // We use % 1 to avoid accepting NaN as an integer.
	    validate_duration: function(hh_mm){
	        var time = hh_mm.split(":");
	        if(time.length === 1){
	            var hours = parseFloat(time[0]);
	            if(isNaN(hours)){
	                return undefined;
	            }
                else{
                    return hours.toString();
                }
	        }
	        else if(time.length === 2){
	            var hours = parseInt(time[0]);
	            var minutes = parseInt(time[1]);
	            if((hours % 1 === 0) && (minutes % 1 === 0) && minutes < 61){
	                if(minutes < 10){
	                    minutes = "0" + minutes.toString();
	                }
	                else{
	                    minutes = minutes.toString();
	                }
	                if(hours < 10){
	                    hours = "0" + hours.toString();
	                }
	                else{
	                    hours = hours.toString();
	                }

	                return hours + ":" + minutes;
	            }
	            else{
	                return undefined;
	            }
	        }
	        else{
	            return undefined;
	        }
	    },

	    hh_mm_to_unit_amount: function(hh_mm){
	        var time = hh_mm.split(":");
	        if(time.length === 1){
	            return parseFloat(time[0]);
	        }
	        else if(time.length === 2){
	            var hours = parseInt(time[0]);
	            var minutes = parseInt(time[1]);
	            return Math.round((hours + (minutes / 60 )) * 100) / 100;
	        }
	        else{
	            return undefined;
	        }       
	    }
	});

	openerp.project_timesheet.Activities_screen = openerp.project_timesheet.BasicScreenWidget.extend({
        template: "activities_screen",
        init: function(parent) {
            self = this;
            self.screen_name = "Activities";
            self._super(parent);
            // Events specific to this screen
            _.extend(self.events,
                {
                    "click .pt_button_plus_activity":"goto_create_activity_screen",
                    "click .pt_activity":"edit_activity",
                    "click .pt_btn_start_activity":"start_activity",
                    "click .pt_btn_stop_activity":"stop_activity",
                    "click .pt_test_btn":"test_fct",
                    "click .pt_quick_add_time" : "quick_add_time",
                    "click .pt_quick_subtract_time" : "quick_subtract_time",
                    "mouseover .pt_duration" : "on_duration_over",
                    "mouseout .pt_duration" : "on_duration_out",
                    "click .pt_duration_continue":"on_continue_activity",
                    "click .pt_btn_interrupt_activity":"on_interrupt_activity",
                    "click .pt_day_plan_task" : "start_day_plan_activity"
                }
            );
            self.account_analytic_lines = self.data.account_analytic_lines;
        },
        start: function(){
            var self = this;
            if(localStorage.getItem("pt_start_timer_time") !== null && localStorage.getItem("pt_timer_activity_id") === null){
                this.timer_on = true;
                this.getParent().start_timer_time = JSON.parse(localStorage.getItem("pt_start_timer_time"));
                this.getParent().timer_start = setInterval(function(){self.timer_fct(self.getParent().start_timer_time, 0)},500);
            }
            else{
                this.timer_on = false;
            }
            if(localStorage.getItem("pt_timer_activity_id") !== null){
                var current_activity_id = JSON.parse(localStorage.getItem("pt_timer_activity_id"));
                self.current_activity = _.findWhere(self.account_analytic_lines , {id : current_activity_id});
                this.getParent().start_timer_time = JSON.parse(localStorage.getItem("pt_start_timer_time"));
                this.getParent().timer_start = setInterval(function(){self.timer_fct(self.getParent().start_timer_time, self.current_activity.unit_amount)},500);
                
                this.timer_on = false;
            }
            else{
                self.current_activity = false;
            }
            this.renderElement();
        },
        //Go to the create / edit activity
        goto_create_activity_screen: function(){
            this.getParent().edit_activity_screen.re_render();
            this.hide();
            this.getParent().edit_activity_screen.show();
        },
        // Go to the edit screen to edit a specific activity
        edit_activity: function(event){
			this.getParent().edit_activity_screen.re_render(event.currentTarget.dataset.activity_id);
            this.hide();
            this.getParent().edit_activity_screen.show();
        },
        timer_fct: function(start_time, start_amount){
            var ms = moment(moment(new Date()).add(start_amount,"hours")).diff(moment(start_time));
            var d = moment.duration(ms);
            var hours = Math.floor(d.asHours());
            if (hours < 10){
                hours = "0" + hours;
            }
            this.getParent().$(".pt_timer_clock").text(hours + moment.utc(d.asMilliseconds()).format(":mm:ss"));
        },
        start_activity: function(){
            var self = this;
            self.timer_on = true;
            this.renderElement();
            self.getParent().$(".pt_timer_clock").text("00:00:00");
            self.getParent().start_timer_time = new Date();
            localStorage.setItem("pt_start_timer_time", JSON.stringify(self.getParent().start_timer_time));
            this.getParent().timer_start = setInterval(function(){self.timer_fct(self.getParent().start_timer_time, 0)},500);
        },
        stop_activity: function(){
            this.timer_on = false;
            clearInterval(this.getParent().timer_start);
            $(".pt_timer_clock").text("");
            this.goto_create_activity_screen();
            // Trigger the change event to pre-fill the edit activity form with the time spent working.
            this.getParent().edit_activity_screen.$("input.pt_activity_duration").val(moment.utc(new Date() - new Date(JSON.parse(localStorage.getItem("pt_start_timer_time")))).format("HH:mm")).change();
            // The activity was started from the day plan:
            if(this.current_activity){
                this.getParent().edit_activity_screen.$(".pt_activity_project").select2("data", {id : this.current_activity.project_id , name : this.get_project_name(this.current_activity.project_id)});
                this.getParent().edit_activity_screen.activity.project_id = this.current_activity.project_id;
                this.getParent().edit_activity_screen.initialize_task_selector();
                this.getParent().edit_activity_screen.$(".pt_activity_task").select2("data", {id : this.current_activity.task_id , name : this.get_task_name(this.current_activity.task_id)})
                this.getParent().edit_activity_screen.activity.task_id = this.current_activity.task_id;
            }
            this.current_activity = false;
            localStorage.removeItem("pt_current_activity");
            localStorage.removeItem("pt_start_timer_time");
        },
        quick_add_time: function(event){
            var activity = _.findWhere(this.data.account_analytic_lines,  {id: event.currentTarget.dataset.activity_id});
            if(_.isUndefined(this.data.settings.time_unit)){
                activity.unit_amount = parseFloat(activity.unit_amount) + 0.25;
            }
            else{
                activity.unit_amount = parseFloat(activity.unit_amount) + this.data.settings.time_unit;
            }
            activity.write_date = openerp.datetime_to_str(new Date());
            this.getParent().update_localStorage();
            this.renderElement();
        },
        quick_subtract_time: function(event){
            var activity = _.findWhere(this.data.account_analytic_lines,  {id: event.currentTarget.dataset.activity_id});
            if(_.isUndefined(this.data.settings.time_unit)){
                activity.unit_amount = parseFloat(activity.unit_amount) - 0.25;
            }
            else{
                activity.unit_amount = parseFloat(activity.unit_amount) - this.data.settings.time_unit;
            }
            if (activity.unit_amount < 0){
                activity.unit_amount = 0;
            }
            activity.write_date = openerp.datetime_to_str(new Date());
            this.getParent().update_localStorage();
            this.renderElement();            
            //event.currentTarget.dataset.activity_id
        },
        on_duration_over: function(event){
            if(localStorage.getItem("pt_start_timer_time") === null){
                var duration_box = this.$(event.currentTarget);
                duration_box.addClass("pt_duration_continue pt_duration_color_fill");
                duration_box.children(".pt_duration_time").addClass("hidden");
                duration_box.children(".pt_continue_activity_btn").removeClass("hidden");
            }
        },
        on_duration_out: function(event){
            var duration_box = this.$(event.currentTarget);
            duration_box.removeClass("pt_duration_continue pt_duration_color_fill");
            duration_box.children(".pt_duration_time").removeClass("hidden");
            duration_box.children(".pt_continue_activity_btn").addClass("hidden");
        },
        on_continue_activity: function(event){
            var activity = _.findWhere(this.account_analytic_lines , {id : event.currentTarget.dataset.activity_id});
            var self = this;
            this.current_activity = activity;
            this.renderElement();
            self.getParent().$(".pt_timer_clock").text(this.unit_amount_to_hours_minutes(activity.unit_amount) + ":00");
            self.getParent().start_amount = activity.unit_amount;
            self.getParent().start_timer_time = new Date();
            localStorage.setItem("pt_start_timer_time", JSON.stringify(self.getParent().start_timer_time));
            localStorage.setItem("pt_timer_activity_id", JSON.stringify(activity.id));
            this.getParent().timer_start = setInterval(function(){self.timer_fct(self.getParent().start_timer_time, self.getParent().start_amount)},500);
        },
        on_interrupt_activity: function(){
            var activity_id = JSON.parse(localStorage.getItem("pt_timer_activity_id"));
            var activity = _.findWhere(this.account_analytic_lines , {id : activity_id}); 
            clearInterval(this.getParent().timer_start);
            $(".pt_timer_clock").text("");
            var start_time = new Date(JSON.parse(localStorage.getItem("pt_start_timer_time")))
            var ms = moment(moment(new Date()).add(activity.unit_amount,"hours")).diff(moment(start_time));
            var d = moment.duration(ms);
            var hours = Math.floor(d.asHours());
            hh_mm_value = hours + moment.utc(d.asMilliseconds()).format(":mm");
            activity.unit_amount = this.hh_mm_to_unit_amount(hh_mm_value);
            activity.write_date = openerp.datetime_to_str(new Date());
            activity.date = openerp.date_to_str(new Date());

            this.data.account_analytic_lines.sort(function(a,b){
                return openerp.str_to_datetime(b.write_date) - openerp.str_to_datetime(a.write_date);
            });
            this.current_activity = false;
            this.timer_on = false;
            this.getParent().update_localStorage();
            this.renderElement();
            localStorage.removeItem("pt_start_timer_time");
            localStorage.removeItem("pt_timer_activity_id");
        },
        start_day_plan_activity: function(event){
            if(!this.current_activity){
                var task_id = event.currentTarget.dataset.task_id;
                var project_id = _.findWhere(this.data.tasks, {id : task_id}).project_id;
                this.current_activity = {
                    task_id : task_id,
                    project_id : project_id
                };
                localStorage.setItem("pt_current_activity" , JSON.stringify(this.current_activity));
                this.data.day_plan.splice(_.indexOf(this.data.day_plan, event.currentTarget.dataset.task_id), 1);
                this.getParent().update_localStorage();
                this.start_activity();
            }
        },
        test_fct: function(){
            this.sync();
            this.renderElement();    
        },
        sync: function(){
            var self = this;
            var parent = this.getParent();
            var data = parent.data;
            var account_analytic_line_model = new openerp.Model("account.analytic.line");
            account_analytic_line_model.call("export_data_for_ui" , []).then(function(sv_data){
                // SV => LS sync
                sv_aals = sv_data.aals.datas;
                sv_tasks = sv_data.tasks.datas;
                sv_projects = sv_data.projects.datas;

                _.each(sv_projects, function(sv_project){
                    // Check if the project exists in LS.
                    // If it does we simply update the name, otherwise we copy the project in LS.
                    ls_project = _.findWhere(data.projects, {id : sv_project[0]})
                    if (_.isUndefined(ls_project)){
                        data.projects.push({
                            id : sv_project[0],
                            name : sv_project[1]
                        });
                    }
                    else{
                        ls_project.name = sv_project[1];
                    }
                    parent.update_localStorage();
                });

                _.each(sv_tasks, function(sv_task){
                    ls_task = _.findWhere(data.tasks, {id : sv_task[0]})
                    if(_.isUndefined(ls_task)){
                        data.tasks.push({
                            id : sv_task[0],
                            project_id : sv_task[1],
                            name : sv_task[3]
                        });
                    }
                    else{
                        ls_task.name = sv_task[3];
                    }
                    parent.update_localStorage();
                });

                _.each(sv_aals, function(sv_aal){
                    // First, check that the aal is related to a project. If not we don't import it.
                    if(!_.isUndefined(sv_aal[8])){
                        ls_aal = _.findWhere(data.account_analytic_lines, {id : sv_aal[0]})
                        // Create case
                        if (_.isUndefined(ls_aal)){
                            data.account_analytic_lines.push({
                                id : sv_aal[0],
                                project_id : sv_aal[8],
                                task_id : sv_aal[1],
                                desc : sv_aal[3],
                                date : sv_aal[5],
                                unit_amount : sv_aal[6],
                                write_date : sv_aal[7]
                            });
                        }
                        else{
                            //Update case
                            if(openerp.str_to_datetime(ls_aal.write_date) < openerp.str_to_datetime(sv_aal[7])){
                                ls_aal.project_id = sv_aal[8];
                                ls_aal.task_id = sv_aal[1];
                                ls_aal.desc = sv_aal[3];
                                ls_aal.date = sv_aal[5];
                                ls_aal.unit_amount = sv_aal[6];
                                ls_aal.write_date = sv_aal[7];
                            }
                        }
                    }
                    parent.update_localStorage();
                });
                self.renderElement();
            })
            .then(function(){
                //LS => SV sync
                var context = new openerp.web.CompoundContext({default_is_timesheet : true});
                account_analytic_line_model.call("import_ui_data" , [data.account_analytic_lines , data.tasks, data.projects, context]).then(function(sv_response){
                    console.log(sv_response);
                    //@TAC TODO : Better error processing system !
                    if (sv_response.aals_errors.length > 0){
                        alert("Some activities could no be synchronized !");
                    }
                    if (sv_response.project_errors.length > 0){
                        alert("Some projects could no be synchronized !");
                    }
                    if (sv_response.task_errors.length > 0){
                        alert("Some tasks could no be synchronized !");
                    }
                });
            });   
        }
    });

    openerp.project_timesheet.Day_planner_screen = openerp.project_timesheet.BasicScreenWidget.extend({
        template: "day_planner_screen",
        init: function(parent) {
        	this._super(parent);
            this.screen_name = "Day Planner";
            _.extend(self.events,
                {
                    "click .pt_day_plan_select":"add_to_day_plan",
                    "click .pt_day_plan_remove" : "remove_from_day_plan"
                }
            );
            this.tasks = this.data.tasks;
        },
        add_to_day_plan: function(event){ 
            this.data.day_plan.push(event.currentTarget.dataset.task_id);
            this.getParent().update_localStorage();
            this.renderElement();
        },
        remove_from_day_plan: function(event){
            this.data.day_plan.splice(_.indexOf(this.data.day_plan, event.currentTarget.dataset.task_id), 1);
            this.getParent().update_localStorage();
            this.renderElement();
        }
    });

    openerp.project_timesheet.Settings_screen = openerp.project_timesheet.BasicScreenWidget.extend({
        template: "settings_screen",
        init: function(parent) {
        	self = this;
            this._super(parent);
            this.screen_name = "Settings";
            _.extend(self.events,
                {
                    "change input.pt_minimal_duration":"on_change_minimal_duration",
                    "change input.pt_time_unit":"on_change_time_unit",
                    "change input.pt_default_project_select2":"on_change_default_project"
                }
            );
        },
        start: function(){
            this.initialize_project_selector();
        },
        initialize_project_selector: function(){
            self = this;
            // Initialization of select2 for projects
            function format(item) {return item.name}
            function formatRes(item){
                if(item.isNew){
                    return "Create Project : " + item.name;
                }
                else{
                    return item.name;
                }
            }
            this.$('.pt_default_project_select2').select2({
                data: {results : self.data.projects , text : 'name'},
                formatSelection: format,
                formatResult: formatRes,
                createSearchChoicePosition : 'bottom',
                placeholder: "No default project",
                allowClear: true,
                createSearchChoice: function(user_input, new_choice){
                    //Avoid duplictate projects
                    var duplicate = _.find(self.data.projects, function(project){
                        return (project.name.toUpperCase() === user_input.trim().toUpperCase());
                    });
                    if (duplicate){
                        return undefined;
                    }
                    res = {
                        id : self.data.module_key + self.getParent().session.username + self.data.original_timestamp + "_project." + self.data.next_project_id,
                        name : user_input.trim(),
                        isNew: true,
                    };
                    return res;
                },
                initSelection : function(element, callback){
                    var data = {id: self.data.settings.default_project_id, name : self.get_project_name(self.data.settings.default_project_id)};
                    callback(data);
                }
            }).select2('val',[]);
        },
        on_change_default_project: function(event){
            self = this;
            // "cleared" case
            if(_.isUndefined(event.added)){
                self.data.settings.default_project_id = undefined;
            }
            // "Select" case
            else{
                var selected_project = {
                    name : event.added.name,
                    id : event.added.id
                };
                if(event.added.isNew){
                    self.data.next_project_id++;
                    self.data.projects.push(selected_project);
                }
                self.data.settings.default_project_id = selected_project.id;
            }
            self.getParent().update_localStorage();
            
        },
        on_change_minimal_duration: function(){
            //TODO Check that input is an int between 0 and 60
            this.data.settings.minimal_duration = (this.$("input.pt_minimal_duration").val()) / 60;
            this.getParent().update_localStorage();
        },
        on_change_time_unit: function(){
        	//TODO Check that input is an int between 0 and 60
            this.data.settings.time_unit = (this.$("input.pt_time_unit").val()) / 60;
            this.getParent().update_localStorage();
        }
    });
	//TODO : clean up select2 inittialize method and re-rendering logic
    openerp.project_timesheet.Edit_activity_screen = openerp.project_timesheet.BasicScreenWidget.extend({
        template: "edit_activity_screen",
        init: function(parent) {
        	self = this;
        	this._super(parent);
            this.screen_name = "Edit Activity";
            _.extend(self.events,
                {
                    "change input.pt_activity_duration":"on_change_duration",
                    "change textarea.pt_description":"on_change_description",
                    "change input.pt_activity_project":"on_change_project",
                    "change input.pt_activity_task":"on_change_task",
                    "click .pt_discard_changes":"discard_changes",
                    "click .pt_validate_edit_btn" : "save_changes"
                }
            );
            this.activity = {
                project_id: undefined,
                task_id: undefined,
                desc:"/",
                unit_amount: undefined,
                date: (openerp.date_to_str(new Date()))
            };
        },
        initialize_project_selector: function(){
            self = this;
        	// Initialization of select2 for projects
        	function format(item) {return item.name}
        	function formatRes(item){
        		if(item.isNew){
        			return "Create Project : " + item.name;
        		}
        		else{
        			return item.name;
        		}
        	}
        	this.$('.pt_activity_project').select2({
        		data: {results : self.data.projects , text : 'name'},
        		formatSelection: format,
				formatResult: formatRes,
                createSearchChoicePosition : 'bottom',
				createSearchChoice: function(user_input, new_choice){
                    //Avoid duplictate projects in one project
                    var duplicate = _.find(self.data.projects, function(project){
                        return (project.name.toUpperCase() === user_input.trim().toUpperCase());
                    });
                    if (duplicate){
                        return undefined;
                    }
                    res = {
                        id : self.data.module_key + self.getParent().session.username + self.data.original_timestamp + "_project." + self.data.next_project_id,
                        name : user_input.trim(),
                        isNew: true,
                    };
                    return res;
                },
				initSelection : function(element, callback){
					var data = {id: self.activity.project_id, name : self.get_project_name(self.activity.project_id)};
					callback(data);
				}
        	});
        },
        // Initialization of select2 for tasks
        initialize_task_selector: function(){
            self = this;
        	function format(item) {return item.name}
        	function formatRes(item){
        		if(item.isNew){
        			return "Create Task : " + item.name;
        		}
        		else{
        			return item.name;
        		}
        	}
            self.task_list = _.where(self.data.tasks, {project_id : self.activity.project_id});
        	this.$('.pt_activity_task').select2({
        		data: {results : self.task_list , text : 'name'},
        		formatSelection: format,
				formatResult: formatRes,
                createSearchChoicePosition : 'bottom',
				createSearchChoice: function(user_input, new_choice){
                    //Avoid duplictate tasks in one project
                    var duplicate = _.find(self.task_list, function(task){
                        return (task.name.toUpperCase() === user_input.trim().toUpperCase());
                    });
                    if (duplicate){
                        return undefined;
                    }
					res = {
						id : self.data.module_key + self.getParent().session.username + self.data.original_timestamp + "_task." + self.data.next_task_id,
						name : user_input.trim(),
						isNew: true,
                        project_id: self.activity.project_id
					};
					return res;
				},
                initSelection : function(element, callback){
                    var data = {id: self.activity.task_id, name : self.get_task_name(self.activity.task_id)};
                    callback(data);
                }
        	});
        },
        on_change_task: function(event){
            self = this;
        	var selected_task = {
    			name : event.added.name,
    			id : event.added.id,
                project_id: event.added.project_id
        	};
        	if(event.added.isNew){
        		self.data.next_task_id++;
        		self.data.tasks.push(selected_task);
                self.task_list.push(selected_task);
        		self.getParent().update_localStorage();
    		}
    		self.activity.task_id = selected_task.id;
        },
        on_change_project: function(event){
        	var selected_project = {
    			name : event.added.name,
    			id : event.added.id
        	};
        	if(event.added.isNew){
        		self.data.next_project_id++;
        		self.data.projects.push(selected_project);
        		self.getParent().update_localStorage();
    		}
    		self.activity.project_id = selected_project.id;
            // If the project has been changed, we reset the task.
            self.activity.task_id = undefined;
            self.initialize_task_selector();
        },
        on_change_duration: function(event){
            var self = this;
            var duration = self.validate_duration(this.$("input.pt_activity_duration").val());
            if(_.isUndefined(duration)){
                this.$("input.pt_activity_duration").val("00:00");
                this.$("input.pt_activity_duration + p").text("Please enter a valid duration in the hh:mm format, such as 01:30, or 1.5");
            }
            else{
                this.activity.unit_amount = self.hh_mm_to_unit_amount(duration);
                this.$("input.pt_activity_duration").val(this.unit_amount_to_hours_minutes(this.activity.unit_amount));
                this.$("input.pt_activity_duration + p").text("");
            }
        },
        on_change_description: function(event){
            this.activity.desc = this.$("textarea.pt_description").val();
        },

        // Function to re-render the screen with a new activity.
        // we use clone to work on a temporary version of activity.
        re_render: function(activity_id){
        	if(!_.isUndefined(activity_id)){
	            this.activity = _.clone(_.findWhere(this.data.account_analytic_lines,  {id:activity_id}));
			}
            else if(!_.isUndefined(self.data.settings.default_project_id)){
                this.activity.project_id = self.data.settings.default_project_id;
            }

            this.renderElement();
            this.initialize_project_selector();
            this.initialize_task_selector();
        },
        save_changes: function(){
            // Validation step :  The only compulsory field is project.
            if(_.isUndefined(this.activity.project_id)){
                this.$('.pt_save_msg').show(0).delay(5000).hide(0);
                return
            } 

            var old_activity = _.findWhere(this.data.account_analytic_lines,  {id:this.activity.id})
            // If this condition is true, it means that the activity is a newly created one :
            if(_.isUndefined(old_activity)){
                this.data.account_analytic_lines.unshift({id : self.data.module_key + self.getParent().session.username + self.data.original_timestamp + "_aal." + self.data.next_aal_id});
                old_activity = this.data.account_analytic_lines[0];
                old_activity.date = this.activity.date;
                self.data.next_aal_id++;
            }
            old_activity.project_id = this.activity.project_id;
            old_activity.task_id = this.activity.task_id;
            old_activity.desc = this.activity.desc;
            old_activity.unit_amount = this.activity.unit_amount;
            old_activity.write_date = openerp.datetime_to_str(new Date());
            
            this.data.account_analytic_lines.sort(function(a,b){
                return openerp.str_to_datetime(b.write_date) - openerp.str_to_datetime(a.write_date);
            });
            this.getParent().update_localStorage();            

            //To empty screen data
            this.reset_activity();
            this.getParent().activities_screen.renderElement();
            this.goto_activities();
        },
        discard_changes: function(){
            this.reset_activity();
            this.goto_activities();
        },
        reset_activity: function(){
            this.activity = {
                project_id: undefined,
                task_id: undefined,
                desc:"/",
                unit_amount: undefined,
                date: (openerp.date_to_str(new Date()))
            };

            if (!_.isUndefined(self.data.settings.default_project)){
                this.activity.project = self.data.settings.default_project;
            }
        }
    });
};