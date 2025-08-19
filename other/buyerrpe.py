# Copyright (c) 2025, MyERPNext Developers and contributors
# For license information, please see license.txt
import datetime

import frappe
from frappe import _, qb, query_builder, scrub
from frappe.query_builder import Criterion
from frappe.query_builder.functions import Date, Substring, Sum
from frappe.utils import cint, cstr, flt, getdate, formatdate

from collections import defaultdict

logger = frappe.logger("myerpnext_custom.report.buyer_performance_v1_0_00", allow_site=True, file_count=10)
logger.setLevel("DEBUG") 

def execute(filters=None):
	#columns, data = [], []
	#return columns, data
	return BuyerPerformanceReport(filters).run()

class BuyerPerformanceReport:
	def __init__(self, filters=None):
		self.filters = frappe._dict(filters or {})

	def run(self):
		self.columns = []
		self.data = []
		self.chart = []
		self.message = None
		self.summary = []
		self.skip_total_row = 0  # or False

		self.docs = None

		self.set_defaults()
		self.filter_validation()
		self.get_columns()
		self.get_data()
		self.get_chart()
		self.get_message()
		#self.message = "hello"

		log_message = f"self.columns: {self.columns}"
		logger.debug(log_message)

		log_message = f"self.data: {self.data}"
		logger.debug(log_message)

		return self.columns, self.data, self.message, self.chart, self.summary, self.skip_total_row
		#self.set_defaults()
		#self.party_naming_by = frappe.db.get_value(args.get("naming_by")[0], None, args.get("naming_by")[1])
		#self.get_columns()
		#self.get_data()
		#self.get_chart_data()
		#return self.columns, self.data, None, self.chart, None, self.skip_total_row

	def set_defaults(self):
		if not self.filters.get("company"):
			self.filters.company = frappe.db.get_single_value("Global Defaults", "default_company")

		if not self.filters.date_from:
			self.filters.date_from = getdate(nowdate())

		if not self.filters.date_until:
			self.filters.date_until = getdate(nowdate())

		self.skip_total_row = 0 #disable for temporary

	def filter_validation(self):
		if self.filters.date_until < self.filters.date_from:
			frappe.throw(_("Date From suppose earlier than Date Until"))

	def get_columns(self):
		self.columns = []
		self.add_column(
			label=_("RFQ Date"), 
			fieldname="transaction_date", 
			fieldtype="Data",
			width=140,
		)
		self.add_column(
			label=_("Buyer"),
			fieldname="buyer_name",
			fieldtype="Data",
			width=140,
		)
		self.add_column(
			label=_("WOI Item"),
			fieldname="woi_item",
			fieldtype="Data",
			width=100,
		)
		self.add_column(
			label=_("WOI Item %"),
			fieldname="woi_item_percent",
			fieldtype="Data",
			width=100,
		)
		self.add_column(
			label=_("Done Item"),
			fieldname="done_item",
			fieldtype="Data",
			width=100,
		)
		self.add_column(
			label=_("Done Item %"),
			fieldname="done_item_percent",
			fieldtype="Data",
			width=100,
		)
		self.add_column(
			label=_("Total Item"),
			fieldname="total_item",
			fieldtype="Data",
			width=100,
		)
		self.add_column(
			label=_("WOI Doc"),
			fieldname="woi_doc",
			fieldtype="Data",
			width=100,
		)
		self.add_column(
			label=_("WOI Doc %"),
			fieldname="woi_doc_percent",
			fieldtype="Data",
			width=100,
		)
		self.add_column(
			label=_("Done Doc"),
			fieldname="done_doc",
			fieldtype="Data",
			width=100,
		)
		self.add_column(
			label=_("Done Doc %"),
			fieldname="done_doc_percent",
			fieldtype="Data",
			width=100,
		)
		self.add_column(
			label=_("Total doc"),
			fieldname="total_doc",
			fieldtype="Data",
			width=100,
		)

	def add_column(self, label, fieldname=None, fieldtype="Currency", options=None, width=120):
		if not fieldname:
			fieldname = scrub(label)
		if fieldtype == "Currency":
			options = "currency"
		if fieldtype == "Date":
			width = 90

		self.columns.append(
			dict(label=label, fieldname=fieldname, fieldtype=fieldtype, options=options, width=width)
		)

	def get_data(self):
		self.data = []
		self.build_data()

	def build_data(self):
		company = self.filters.company #company temporay disable awhile
		date_from = self.filters.date_from
		date_until = self.filters.date_until

		self.docs = frappe.db.sql(
            """
				SELECT 
					`transaction_date`,
					`buyer_name`,
					SUM(`woi_item`) AS `woi_item`,
					ROUND((SUM(`woi_item`) / NULLIF(SUM(`total_item`), 0)) * 100, 2) AS `woi_item_percent`,
					SUM(`done_item`) AS `done_item`,
					ROUND((SUM(`done_item`) / NULLIF(SUM(`total_item`), 0)) * 100, 2) AS `done_item_percent`,    
					SUM(`total_item`) AS `total_item`,
					SUM(`woi_doc`) AS `woi_doc`,
					ROUND((SUM(`woi_doc`) / NULLIF(SUM(`total_doc`), 0)) * 100, 2) AS `woi_doc_percent`,
					SUM(`done_doc`) AS `done_doc`,
					ROUND((SUM(`done_doc`) / NULLIF(SUM(`total_doc`), 0)) * 100, 2) AS `done_doc_percent`,    
					SUM(`total_doc`) AS `total_doc`
				FROM 
					`tabBuyer Performance`
				WHERE 
					`transaction_date` BETWEEN %s AND %s
				GROUP BY 
					`transaction_date`,
					`buyer_name`
				ORDER BY 
					`transaction_date`,
					`buyer_name`;            
            """,
            (date_from, date_until),
            as_dict=True
        )

		return_docs = self.docs

		sums = {
				"woi_item": 0,
				"done_item": 0,
				"total_item": 0,
				"woi_doc": 0,
				"done_doc": 0,
				"total_doc": 0,
				"woi_item_percent": 0,
				"done_item_percent": 0,
				"woi_doc_percent": 0,
				"done_doc_percent": 0
			}
		count = len(return_docs)

		for row in return_docs:
			for key in sums:
				sums[key] += row.get(key) or 0

		# Average percentage fields
		total_row = {
			"transaction_date": "Total",
			"buyer_name": "",
			"woi_item": sums["woi_item"],
			"done_item": sums["done_item"],
			"total_item": sums["total_item"],
			"woi_doc": sums["woi_doc"],
			"done_doc": sums["done_doc"],
			"total_doc": sums["total_doc"],
			"woi_item_percent": round(sums["woi_item_percent"] / count, 2) if count else 0,
			"done_item_percent": round(sums["done_item_percent"] / count, 2) if count else 0,
			"woi_doc_percent": round(sums["woi_doc_percent"] / count, 2) if count else 0,
			"done_doc_percent": round(sums["done_doc_percent"] / count, 2) if count else 0,
			"bold": 1,  
		}

		return_docs.append(total_row)
		self.data = return_docs

	def get_chart(self):
		buyer_date_data = defaultdict(lambda: defaultdict(float))
		date_set = set()

		for row in self.docs:
			if row.get("transaction_date") == "Total":
				continue			
			buyer = row["buyer_name"]
			date = row["transaction_date"]

			# Convert to string for uniform comparison and sorting
			if isinstance(date, datetime.date):
				date = date.strftime("%Y-%m-%d")

			value = row.get("done_doc") or 0
			buyer_date_data[buyer][date] += value
			date_set.add(date)

		sorted_dates = sorted(date_set)

		datasets = []
		for buyer, date_map in buyer_date_data.items():
			datasets.append({
				"name": buyer,
				"values": [date_map.get(d, 0) for d in sorted_dates]
			})		

		self.chart = {
			"data": {
				"labels": sorted_dates,
				"datasets": datasets,
			},
			"title": "Buyer Done Performance",
			"type": "line",
			"colors": ["#007bff", "#28a745", "#ffc107", "#dc3545", "#6f42c1"]			
		}

	def get_message(self):
		self.rank_table()

	def rank_table(self):
		buyer_totals = defaultdict(float)
		for row in self.docs:
			buyer = row.get("buyer_name")
			amount = row.get("total_done", 0)
			if buyer:
				buyer_totals[buyer] += amount

		# Sort by total_done descending
		sorted_buyers = sorted(buyer_totals.items(), key=lambda x: x[1], reverse=True)

		# Render HTML table
		table_html = """
		<div style="margin-top:1rem">
			<table class="table table-bordered" style="width:auto">
				<thead>
					<tr>
						<th>No</th>
						<th>Buyer</th>
						<th style="text-align:right;">Total Done</th></tr></thead>
				<tbody>
		"""
		for idx, (buyer, total) in enumerate(sorted_buyers, 1):
			table_html += f"""
				<tr>
					<td style="text-align:center;">{idx}</td>
					<td style="text-align:left;">{buyer}</td>
					<td style="text-align:right;">{frappe.utils.fmt_money(total)}</td>
				</tr>
			"""
		table_html += "</tbody></table></div>"

		# Set it to self.message to render in report view
		self.message = table_html
