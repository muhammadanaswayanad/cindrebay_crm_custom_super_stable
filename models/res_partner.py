from odoo import models,fields,api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    whatsapp_number = fields.Char(string="WhatsApp Number")
    mobile_alt = fields.Char(string="Mobile (Alt)", )

    date_of_birth = fields.Date(string="Date of Birth", )
    age = fields.Integer(string="Age")
    father_guardian = fields.Char(string="Father/Guardian", )
    qualification = fields.Char(string="Qualification", )
    district = fields.Char(string="District", )

    aadhaar_no = fields.Char(string="Student Aadhaar No")
    # Bank Details
    bank_account_name = fields.Char(string="Account Holder Name")
    bank_account_no = fields.Char(string="Account No")
    bank_ifsc_code = fields.Char(string="IFSC Code")
    bank_name = fields.Char(string="Bank Name")
    relation_with_bank_acc_holder = fields.Selection(
        selection=[('self', 'Self/Own'),('spouse', 'Spouse'),
            ('mother', 'Mother'),('father', 'Father'),('grand_father', 'Grand Father'),
            ('grand_mother', 'Grand Mother'),('uncle', 'Uncle'),
            ('aunt', 'Aunt'),('brother', 'Brother'),
            ('sister', 'Sister'),('son', 'Son'),
            ('daughter', 'Daughter'),('other', 'Other (Specify)')
        ],
        string="Relationship with Account Holder", default="self"
    )
    relation_with_bank_acc_holder_manual = fields.Char(string="Specify Relation")