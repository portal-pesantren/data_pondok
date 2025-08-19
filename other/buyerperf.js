// Copyright (c) 2025, MyERPNext Developers and contributors
// For license information, please see license.txt

frappe.provide("erpnext.utils");

frappe.query_reports["Buyer Performance v1_0_00"] = {
	"filters": [
		{
			fieldname: "date_from",
			label: __("Date From"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "date_until",
			label: __("Date Until"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.get_today(),
		},

	],
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		const done_Columns = ["done_item", "done_item_percent", "done_doc", "done_doc_percent"];
		const total_Columns = ["total_item", "total_doc"];

		if (done_Columns.includes(column.fieldname)) {
			value = `<div style="background-color: #e6e6e6; padding: 4px;">${value}</div>`; // light yellow
		} else if (total_Columns.includes(column.fieldname)) {
			value = `<div style="background-color: #d9d9d9; padding: 4px;">${value}</div>`; // light green
		}		
		
		if (data && data.bold) {
			value = `<b>${value}</b>`;			
		}
		return value;
	},
};
