from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta
from odoo.tools.misc import format_date
import json


class CrmSalespersonPerformance(models.Model):
    _name = "crm.salesperson.performance"
    _description = "Salesperson Performance Report"
    _auto = False
    _order = "user_id, engagement_date desc"
    _transient = True  # Making it transient for the summary view

    user_id = fields.Many2one('res.users', string='Salesperson', readonly=True)
    team_id = fields.Many2one('crm.team', string='Sales Team', readonly=True)
    engagement_date = fields.Date(string='Engagement Date', readonly=True)
    lead_id = fields.Many2one('crm.lead', string='Lead', readonly=True)
    stage_id = fields.Many2one('crm.stage', string='Stage', readonly=True)
    call_status = fields.Selection([
        ('not_called', 'Not Called'),
        ('not_connected', 'Call not connected'),
        ('call_1', '1st Call'),
        ('followup_1', 'Followup 1'),
        ('followup_2', 'Followup 2'),
        ('followup_3', 'Followup 3'),
        ('followup_4', 'Followup 4'),
        ('followup_5', 'Followup 5'),
        ('followup_6', 'Followup 6'),
        ('followup_7', 'Followup 7'),
        ('followup_8', 'Followup 8'),
        ('followup_9', 'Followup 9'),
        ('followup_10', 'Followup 10'),
    ], string="Call Status", readonly=True)
    
    # Fields for summary form view
    date_from = fields.Date(string="From Date")
    date_to = fields.Date(string="To Date", default=fields.Date.today)
    summary_loaded = fields.Boolean(string="Summary Loaded", default=False)
    summary_html = fields.Html(string="Summary", sanitize=False)
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    ROW_NUMBER() OVER() as id,
                    ch.user_id,
                    l.team_id,
                    DATE(ch.call_date) as engagement_date,
                    ch.lead_id,
                    l.stage_id,
                    ch.call_status
                FROM
                    crm_lead_call_history ch
                JOIN
                    crm_lead l ON ch.lead_id = l.id
                WHERE
                    ch.call_date IS NOT NULL
                GROUP BY
                    ch.user_id, l.team_id, DATE(ch.call_date), ch.lead_id, l.stage_id, ch.call_status
            )
        """ % (self._table))

    def action_view_leads(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_action_pipeline")
        action['domain'] = [('id', '=', self.lead_id.id)]
        action['context'] = {}
        return action
        
    @api.model
    def get_engagement_summary(self, start_date=None, end_date=None):
        """
        Get summary of salesperson engagement across different call statuses
        within the specified date range.
        """
        if not start_date:
            start_date = fields.Date.today() - timedelta(days=7)
        if not end_date:
            end_date = fields.Date.today()
            
        # Convert to strings if they are date objects
        if isinstance(start_date, datetime):
            start_date = start_date.date()
        if isinstance(end_date, datetime):
            end_date = end_date.date()
            
        query = """
            SELECT 
                u.id as user_id,
                u.name as user_name,
                ch.call_status,
                COUNT(DISTINCT ch.lead_id) as lead_count
            FROM 
                crm_lead_call_history ch
            JOIN 
                res_users u ON ch.user_id = u.id
            WHERE 
                DATE(ch.call_date) BETWEEN %s AND %s
            GROUP BY 
                u.id, u.name, ch.call_status
            ORDER BY 
                u.name, ch.call_status
        """
        
        self.env.cr.execute(query, (start_date, end_date))
        results = self.env.cr.dictfetchall()
        
        # Organize results by user
        summary = {}
        for row in results:
            user_id = row['user_id']
            if user_id not in summary:
                summary[user_id] = {
                    'user_id': user_id,
                    'user_name': row['user_name'],
                    'total_leads': 0,
                    'statuses': {}
                }
            
            summary[user_id]['statuses'][row['call_status']] = row['lead_count']
            summary[user_id]['total_leads'] += row['lead_count']
            
        return {
            'start_date': format_date(self.env, start_date),
            'end_date': format_date(self.env, end_date),
            'data': list(summary.values())
        }
        
    def action_load_summary(self):
        """
        Load engagement summary data for the specified date range
        and display it in a formatted HTML table.
        """
        self.ensure_one()
        
        if not self.date_from or not self.date_to:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Missing Date Range'),
                    'message': _('Please select a date range.'),
                    'sticky': False,
                    'type': 'warning'
                }
            }
            
        # Get summary data
        summary = self.get_engagement_summary(self.date_from, self.date_to)
        
        # Build HTML report
        html = """
        <div class="container mt-4">
            <div class="alert alert-info">
                <strong>Period:</strong> {} to {}
            </div>
            <table class="table table-striped table-hover">
                <thead class="thead-dark">
                    <tr>
                        <th>Salesperson</th>
                        <th>Not Connected</th>
                        <th>1st Call</th>
                        <th>Followup Calls</th>
                        <th>Total Engagements</th>
                    </tr>
                </thead>
                <tbody>
        """.format(summary['start_date'], summary['end_date'])
        
        if not summary['data']:
            html += """
                <tr>
                    <td colspan="5" class="text-center">No engagement data found for this period</td>
                </tr>
            """
        else:
            for user_data in summary['data']:
                # Count different call statuses
                not_connected = user_data['statuses'].get('not_connected', 0)
                first_call = user_data['statuses'].get('call_1', 0)
                
                # Count all followups
                followups = 0
                for status, count in user_data['statuses'].items():
                    if status.startswith('followup_'):
                        followups += count
                
                html += """
                    <tr>
                        <td>{}</td>
                        <td>{}</td>
                        <td>{}</td>
                        <td>{}</td>
                        <td><strong>{}</strong></td>
                    </tr>
                """.format(
                    user_data['user_name'],
                    not_connected,
                    first_call,
                    followups,
                    user_data['total_leads']
                )
        
        html += """
                </tbody>
            </table>
        </div>
        """
        
        # Update the record
        self.write({
            'summary_loaded': True,
            'summary_html': html
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
