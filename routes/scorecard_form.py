from fastapi import APIRouter, Body, HTTPException
from typing import Any, Dict
import json
import re
from utils.scorecard_form_helper import get_user, get_kpi_checklist_fields, submit_data_to_airtable

router = APIRouter()


def normalize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {}

    for raw_key, value in payload.items():
        match = re.match(r"^([^\[]+)\[([^\]]+)\]$", raw_key)
        if not match:
            normalized[raw_key] = value
            continue

        fieldset_key = match.group(1)
        inner_key = match.group(2)
        section_bucket = normalized.setdefault(fieldset_key, {})

        # Group indexed keys like 1_score, 2_label, etc.
        indexed_match = re.match(r"^(\d+)_(.+)$", inner_key)
        if indexed_match:
            item_index = indexed_match.group(1)
            item_field = indexed_match.group(2)

            items_bucket = section_bucket.setdefault("items", {})
            item_bucket = items_bucket.setdefault(item_index, {})
            item_bucket[item_field] = value
        else:
            section_bucket[inner_key] = value

    return normalized

@router.post("/submit-form")
async def submit_form(payload: Dict[str, Any] = Body(...)):
    normalized = normalize_payload(payload)

    #data = json.dumps(normalized, indent=2, ensure_ascii=False)
    isSubmitted = submit_data_to_airtable(normalized)

    return {
        "status": "success",
        "received_keys": list(payload.keys()),
        "normalized_data": normalized
    }


FORM_SCHEMAS = [
    {
        "section": "Scorecard Proctor",
        "fields": [
            {
                "Label": "Fullname",
                "type": "text",
                "value": ""
            },
            {
                "Label": "Email",
                "type": "email",
                "value": ""
            }
        ]
    },
    {
        "section": "Employee Being Scored",
        "fields": [
            {
                "Label": "Fullname",
                "type": "text",
                "value": ""
            },
            {
                "Label": "Email",
                "type": "email",
                "value": ""
            },
            {
                "Label": "Position",
                "type": "text",
                "value": ""
            },
            {
                "Label": "Is Team Lead, Manager, Director, or Above",
                "type": "radio",
                "options": ["Yes", "No"],
                "value": ""
            },
            {
                "Label": "Last Raise Given",
                "type": "date",
                "value": ""
            },
            {
                "Label": "Last Review Date",
                "type": "date",
                "value": ""
            },
            {
                "Label": "Next Review Date",
                "type": "date",
                "value": ""
            }
        ]
    },
    {
        "section": "Core Values",
        "fields": [
            {
                "label": "Learning - Never ending acquisition of knowledge and skills",
                "plus": "Upgrading skills by keeping self upto date with processes, industry trends and continuously enhancing ones knowledge. Suggests process improvements timely. Pitch new ideas based on your research.",
                "mid": "Reviews SOP's and self help videos before asking questions",
                "minus": "Waiting to always be fed the answer. Does not take initiative to learn and discover unfamaliar tasks."
            },
            {
                "label": "Eagerness - to Get Started. Keenness. Bias for Action",
                "plus": "Can complete tasks quicker and more efficiently that expected. Volunteers to help complete tasks outside of scope to help out the team. Mentors colleagues to help keep tasks on track. Builds a strong sense of urgency in the team in exceeding goals.",
                "mid": "Can consistently complete assigned work on time. Does not need to extend due dates.",
                "minus": "Just waiting for things to happen to tasks to be assigned. Needs to be reminded or prompted to take action."
            },
            {
                "label": "Tech Savvy - Types 55+ WPM, Excel Guru, Google Enthusiast, Train 1 time",
                "plus": "Builds systems, templates and other initiatives to make processes more efficient that us currently used org wide. Stay knowledgeable about new technology",
                "mid": "Can use systems and softwares without supervision and can troubleshoot on their own.",
                "minus": "Takes time to learn systems and software. Does not know how to vlookup, CRTL F search, needs a lot of guidance to maximize use of software."
            },
            {
                "label": "Consistent Communication - Frequently conveys info with clarity, accuracy, and purpose to all parties",
                "plus": "Communicates with confidence, integrity and credibility and maintains a consistent flow of communication and information across the levels of the organization.",
                "mid": "Assertively expresses one’s ideas and feelings but adapts content, style, tone and medium of communication appropriately.",
                "minus": "Does not communicate effectively and lacks empathy in listening to others; misses vital opportunities to communicate."
            },
            {
                "label": "Teaching - Help others learn, share your knowledge",
                "plus": "Employee is a true champion of MAG's vision. They live and breathe it every day, inspiring others to do the same. Their dedication and actions have a significant impact on the organization's success.",
                "mid": "Employee consistently works towards MAG's vision but may occasionally falter. They demonstrate understanding and make efforts to implement it, but there's room for improvement.",
                "minus": "Employee struggles to grasp and align with MAG's vision. They often get bogged down in day-to-day tasks and lack a clear connection to the bigger picture."
            }
        ]
    },
    {
        "section": "Manager Values",
        "fields": [
            {
                "label": "Multiply Yourself - Replace Yourself to Scale MAG 1 + 1 = 3",
                "plus": "Employee excels at multiplying themselves and replacing themselves effectively across various aspects of their role. They are instrumental in scaling MAG and inspire others to do the same. Has successfully replaced themselves more than once.",
                "mid": "Employee consistently collaborates with others and is willing to share tasks and knowledge. They contribute to scaling MAG but could be more proactive.",
                "minus": "Employee prefers to work in isolation and is reluctant to share responsibilities or knowledge. They struggle to collaborate and don't contribute to scaling MAG effectively."
            },
            {
                "label": "Soft on the People - Treat Employee's with Respect and Sincerity.",
                "plus": "Promotes a non-threatening environment to allow for healthy assertions of varying opinions and views and thus encourage openness and flexibility.",
                "mid": "Listens to opinions and respects others but needs to be more assertive in handling conflicting views or members",
                "minus": "Speaks to client or teamates in a rude or condescending way. Make others feel bad due to inappriate gestures, expressions or actions."
            },
            {
                "label": "Compete - We are a team not a family. Crush your competitors. Play to win.",
                "plus": "With an unwavering drive and winning mindset, Committed to pushing the boundaries of what is possible. Tirelessly strive for excellence in every endeavor, breaking through limitations and setting new achievement standards. Has dedication to surpassing expectations and achieving unparalleled success fuels every move, not only meet but exceed the highest benchmarks of performance.",
                "mid": "Routinely navigates challenges and drives success by leveraging the strength of the team.",
                "minus": "Misses opportunities to instill a sense of urgency for reaching goals and meeting deadlines."
            },
            {
                "label": "Extreme Ownership - Seizes Accountability. Prioritizes then Executes. Maintains Discipline to create a simple but often difficult plan of action in motion at all times.",
                "plus": "Fosters an environment in which the team holds each other accountable for always delivering on workgroup goals as well as adhering to all policies and procedures.  Gives close attention to metrics and milestones to chart progress, quickly identifying gaps and redirecting efforts accordingly.",
                "mid": "Typically accepts responsibility for the successes and failures of own work and the team’s work.",
                "minus": "Allows self or team to ignore or stretch policies, procedures, or workgroup goals."
            },
            {
                "label": "Candor - Feedback Faster. Telling direct reports where they stand every single day. Tell it like it is.",
                "plus": "Creates a climate where setting expectations and providing feedback is the norm.  Identifies patterns in employee behavior that indicate development needs across the organization and identifies ways to systematically enhance the performance of Detector Inspector employees.",
                "mid": "Holds regular formal and informal performance discussions with each direct report to assess progress towards the goals. Collaborates with each direct report in creating well-defined actions plans to meet requirements and improve performance.",
                "minus": "Avoids addressing team member's poor performance and does not initiate work-habit discussions."
            }
        ]
    },
    {
        "section": "Work Ethic",
        "fields": [
            "Employee Attendance is Dependable - Shows up to work on time, can be counted on to show up",
            "Employee properly manages Asana, has clean boards, due dates active and proper, utilizes for new tasks, comments and responds within 1 business day",
            "Employee follows MAG protocols (Take Client notes before calls, Follow Tiers, Follow Ticketing System Guidelines, Show up for Meetings on time, etc)",
            "Employee Utilizes Two Monitors, a Computer with at least 8 GB of RAM, has a webcam, and mic, and is able to be easily understood by co-workers, and clients through their devices",
            "The employee writes well formed emails, responds within 4 business hours, and practices the 0 unread inbox policy",
            "The employee properly utilizes their direct reports, makes sure they have enough tasks, properly delegates, etc.",
            "The employee always tries to learn, problem solve, and asks questions to get better at their job",
            "The employee openly complains about their job",
            "Utilizes an upbeat positive attitude and can do spirit which motivates others in which they interact with. Others respect employee (clients, peers, management)"
        ]
    },
    {
        "section": "Conclusion",
        "fields": [
            {
                "label": "Does this employee deserve a raise?",
                "type": "radio",
                "options": ["Yes", "No"],
                "value": ""
            },
            {
                "label": "Why? (Required written explanation)",
                "type": "textarea",
                "value": ""
            },
            {
                "label": "Please list any special projects the employee has completed outside of his/her core role responsibilities.",
                "type": "textarea",
                "value": ""
            }
        ]
    },
    {
        "section": "Technical Skill",
        "fields": [
            {
                "label": "PPC Knowledge - Is Able to Login to Amazon, Identify Issues with PPC Campaigns, Point Out Solutions, Understands Basic KPIs (ACOS, TACOS, etc), and Understands MAG's System for Solving Issues",
                "position": ["advertising specialist", "brand manager"],
                "1": "Requires close and extensive guidance. Cannot start unless taught.",
                "2": "Needs to confirm action with peers. Always seeks answers and confirmation to get task done. Revisions and QA is still needed. Needs more time to complete tasks.",
                "3": "Requires little or no guidance. Minimal QA needed. Gets tasks done on time.",
                "4": "Stands alone and can work with no supervision. Can QA own work. Completes tasks ahead of time. Can teach others.",
                "5": "Requires no oversight; serves as key resource and advises others. Can already anticipate future needs, create sop's and templates, train whole org and can correctly and consistently help in slack groups."
            },
            {
                "label": "Amazon SEO Knowledge - Understands Amazon SEO Basics, MAG's SEO Phases, and What Should and Should not be done in regards to SEO. (Copy, Alt Text, backend, etc)",
                "position": ["amazon specialist", "brand manager"],
                "1": "Requires close and extensive guidance. Cannot start unless taught.",
                "2": "Needs to confirm action with peers. Always seeks answers and confirmation to get task done. Revisions and QA is still needed. Needs more time to complete tasks.",
                "3": "Requires little or no guidance. Minimal QA needed. Gets tasks done on time.",
                "4": "Stands alone and can work with no supervision. Can QA own work. Completes tasks ahead of time. Can teach others.",
                "5": "Requires no oversight; serves as key resource and advises others. Can already anticipate future needs, create sop's and templates, train whole org and can correctly and consistently help in slack groups."
            },
            {
                "label": "Amazon Brand Registry Knowledge - Understands the Benefits of Brand Registry, Features, How to Manage Access Issues, how to report hijackers, Brand Name Changes, MAG Processes, and Basic Trademark Knowledge.",
                "position": ["amazon specialist", "brand manager"],
                "1": "Requires close and extensive guidance. Cannot start unless taught.",
                "2": "Needs to confirm action with peers. Always seeks answers and confirmation to get task done. Revisions and QA is still needed. Needs more time to complete tasks.",
                "3": "Requires little or no guidance. Minimal QA needed. Gets tasks done on time.",
                "4": "Stands alone and can work with no supervision. Can QA own work. Completes tasks ahead of time. Can teach others.",
                "5": "Requires no oversight; serves as key resource and advises others. Can already anticipate future needs, create sop's and templates, train whole org and can correctly and consistently help in slack groups."
            },
            {
                "label": "Amazon Merchandising/Catalog Knowledge - Understand how to create a listing, how to make a parentage, audit an account, find and solve BSR issues, knows how to audit accounts, utilize a flat file for listing changes, etc.",
                "position": ["amazon specialist", "brand manager"],
                "1": "Requires close and extensive guidance. Cannot start unless taught.",
                "2": "Needs to confirm action with peers. Always seeks answers and confirmation to get task done. Revisions and QA is still needed. Needs more time to complete tasks.",
                "3": "Requires little or no guidance. Minimal QA needed. Gets tasks done on time.",
                "4": "Stands alone and can work with no supervision. Can QA own work. Completes tasks ahead of time. Can teach others.",
                "5": "Requires no oversight; serves as key resource and advises others. Can already anticipate future needs, create sop's and templates, train whole org and can correctly and consistently help in slack groups."
            },
            {
                "label": "Amazon Troubleshooting Knowledge - Know's how to make a POA, unsuspend accounts, file appeals, address and resolve policy violations, etc.",
                "position": ["amazon specialist", "brand manager"],
                "1": "Requires close and extensive guidance. Cannot start unless taught.",
                "2": "Needs to confirm action with peers. Always seeks answers and confirmation to get task done. Revisions and QA is still needed. Needs more time to complete tasks.",
                "3": "Requires little or no guidance. Minimal QA needed. Gets tasks done on time.",
                "4": "Stands alone and can work with no supervision. Can QA own work. Completes tasks ahead of time. Can teach others.",
                "5": "Requires no oversight; serves as key resource and advises others. Can already anticipate future needs, create sop's and templates, train whole org and can correctly and consistently help in slack groups."
            },
            {
                "label": "Amazon Creative Design - Know's how to make A+ content, info-graphics, identify conversion issues, use photoshop, follow mag process, understand brand identity, etc",
                "position": ["graphic designer"],
                "1": "Requires close and extensive guidance. Cannot start unless taught.",
                "2": "Needs to confirm action with peers. Always seeks answers and confirmation to get task done. Revisions and QA is still needed. Needs more time to complete tasks.",
                "3": "Requires little or no guidance. Minimal QA needed. Gets tasks done on time.",
                "4": "Stands alone and can work with no supervision. Can QA own work. Completes tasks ahead of time. Can teach others.",
                "5": "Requires no oversight; serves as key resource and advises others. Can already anticipate future needs, create sop's and templates, train whole org and can correctly and consistently help in slack groups."
            }
        ]
    }
]
@router.get("/form-schema")
async def get_schema(rec_id: str):
    userInfo = get_user(rec_id)
    if not userInfo: raise HTTPException(status_code=404, detail="User not found")

    position = userInfo.get('Current Position Title', None)[0]
    if not position: raise HTTPException(status_code=404, detail="Position title not found for user")
    kpi_checklist_fields = get_kpi_checklist_fields(position)
        
    #Employee being scored
    target = next( (schema for schema in FORM_SCHEMAS if schema["section"] == "Employee Being Scored"), None )
    for field in target["fields"]:
        if field["Label"] == "Fullname":
            field["value"] = userInfo.get('Full Name', '')
        elif field["Label"] == "Email":
            field["value"] = userInfo.get('Work Email Address', '')
        elif field["Label"] == "Position":
            field["value"] = position
        elif field["Label"] == "Is Team Lead, Manager, Director, or Above":
            field["value"] = "Yes" if userInfo.get('Current Position Level', False)[0] not in ["Worker", "Intern"] else "No"
        elif field["Label"] == "Last Raise Given":
            field["value"] = userInfo.get('Last Pay Raise', '')
        elif field["Label"] == "Last Review Date":
            field["value"] = userInfo.get('Recent Review Date', '')
        elif field["Label"] == "Next Review Date":
            field["value"] = userInfo.get('Next Employee Review', '')

    final_schema = FORM_SCHEMAS + [kpi_checklist_fields]

    return final_schema