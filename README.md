# CindreBay CRM Custom Module

## Overview

The CindreBay CRM Custom module enhances Odoo's standard CRM functionality with several specialized features designed for educational institutions and businesses that require advanced lead management, walk-in appointments, and detailed customer profiles. This module is tailored to meet the specific needs of CindreBay's sales process.

## Key Features

### 1. Enhanced Lead Management

- **Branch-Based Lead Assignment**: Automatic assignment of leads to sales teams based on preferred branches
- **Duplicate Lead Detection**: Auto-assignment of leads with matching phone/email to the same salesperson
- **Random Lead Assignment**: Fallback mechanism when branch matching isn't available
- **Custom Lead Fields**: Additional fields to capture more detailed lead information
- **Editable Closed Date**: Option to edit the closed date of opportunities with proper tracking
- **Lead Import Tool**: Wizard for bulk importing leads from CSV files

### 2. Walk-in Appointment System

- **Walk-in Scheduling**: Complete system for scheduling and managing walk-in appointments
- **Appointment Tracking**: Track appointment status (scheduled, completed, rescheduled, cancelled, no-show)
- **Rescheduling Process**: Structured process for handling appointment rescheduling with reason tracking
- **Follow-up Activities**: Automatic creation of follow-up activities after appointments
- **Sequential Appointment References**: Automatic generation of unique reference numbers for appointments

### 3. Enhanced Contact Information

- **Extended Contact Details**: Additional fields for contacts including:
  - WhatsApp number
  - Alternative mobile number
  - Date of birth and age
  - Father/Guardian information
  - Qualification and district
  - Aadhaar number

- **Banking Information**: Fields to store bank account details:
  - Account holder name
  - Account number
  - IFSC code
  - Bank name
  - Relationship with account holder

## Configuration

### Sales Teams Configuration

1. Navigate to CRM > Configuration > Sales Teams
2. For each team, configure the `Preferred Branches` field:
   - Enter a comma-separated list of branches the team handles
   - Example: "kochi, calicut, trivandrum"
   - This enables branch-based lead assignment

### Walk-in Appointment Setup

1. The system is pre-configured with necessary sequence numbering for walk-in references
2. Walk-in appointments can be created from the lead form or from the dedicated Walk-ins menu
3. The module includes pre-defined activity types for appointment follow-ups

## Usage Guidelines

### Lead Assignment Process

When a lead is created or its preferred branch is updated:
1. First, the system checks for existing leads with matching phone number or email address
   - If found, the new lead is assigned to the same salesperson who handles the existing matching lead
   - This prevents assignment conflicts and ensures consistent follow-up with the same customer
2. If no duplicate is found, the system attempts to find a matching sales team based on the preferred branch
3. If a branch match is found, the lead is assigned to that team
4. If no match is found, the lead may be assigned randomly to a sales team

### Importing Leads

1. Navigate to CRM > Tools > Import Leads
2. Upload a CSV file with required columns:
   - Customer
   - Email
   - Phone
   - City/Town
   - Opportunity
   - Sales Team
   - Source
   - Referred By

### Managing Walk-in Appointments

1. **Creating Appointments**: Create from lead form or Walk-ins menu
2. **Tracking Status**: Update appointment status as they progress
3. **Rescheduling**: Use the reschedule button to create linked follow-up appointments
4. **Completion**: Mark appointments as completed and add notes about the interaction

### Managing Call Logs

1. **Call Status Tracking**: Track the progression of calls with leads
   - Set call status to track the communication lifecycle (1st Call, Followup 1-10)
   - Record detailed call remarks for each interaction
   - View color-coded call status indicators on kanban cards

2. **Call History**: Maintain a complete record of all call interactions
   - All calls are timestamped and recorded with the responsible user
   - Call history is displayed in a dedicated tab for each lead
   - Filter and group calls by date, status, or responsible user

3. **Call Logging Process**:
   - Update the call status field to reflect the current interaction stage
   - Add relevant remarks about the call
   - Click "Log Call" to save the interaction to history
   - Each call log updates the lead's "Last Updated" timestamp

## Technical Notes

- **Duplicate Lead Detection**: The system detects duplicates by matching phone numbers or email addresses
  - Only considers leads that already have a salesperson assigned 
  - Only older leads (created before the current lead) are considered for duplicate matching
  - Phone matching is checked first, then email if no phone match is found
- **Branch Matching Logic**: Branch matching is case-insensitive and ignores trailing underscores and whitespace
  - Example: "kochi_", "Kochi", and "kochi" are all considered the same branch
- **Call Logging System**: Uses a dedicated model for storing call history
  - Call dates are stored with proper timezone consideration
  - Logging a call automatically updates the lead's last updated timestamp
- **Module Dependencies**: base, crm, sale, sale_crm, hr, mail
- **Data Security**: Includes custom security groups and access rights for proper data management
- **Mail Integration**: Leverages Odoo's mail system for activity scheduling and notifications

## Maintenance and Troubleshooting

- When updating the module, verify that custom fields and views remain compatible
- For import issues, ensure CSV format matches the expected structure
- If lead assignment isn't working as expected, verify team branch configurations

---

*Last Updated: June 9, 2025*