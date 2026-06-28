from app.models.organization import Organization
from app.models.workspace import Workspace
from app.models.knowledge_schema import KnowledgeSchema, SchemaField
from app.models.business_rule import BusinessRule, RuleCondition
from app.models.enums import UserRole, UserStatus, WorkspaceStatus, FieldType, AssetContentType, AssetStatus, DecisionOutcome, RuleType

class DemoScenario:
    def __init__(
        self,
        id: str,
        name: str,
        organization: Organization,
        workspace_name: str,
        workspace_description: str,
        schema: KnowledgeSchema,
        rules: list[BusinessRule]
    ):
        self.id = id
        self.name = name
        self.organization = organization
        self.workspace_name = workspace_name
        self.workspace_description = workspace_description
        self.schema = schema
        self.rules = rules

def get_demo_scenarios() -> dict[str, DemoScenario]:
    # --- Scenario 1: Hiring AI Engineer ---
    hiring_org = Organization(
        name="Acme Corporation", domains=["acme.com"], slug="acme-corp", contact_email="contact@acme.com"
    )
    hiring_schema = KnowledgeSchema(
        organization_id=hiring_org.id,
        name="Candidate Profile",
        description="Profile schema for AI Engineer candidates",
        fields=[
            SchemaField(name="name", label="Name", field_type=FieldType.STRING, required=True),
            SchemaField(name="skills", label="Skills", field_type=FieldType.LIST, required=True),
            SchemaField(name="years_experience", label="Years of Experience", field_type=FieldType.INTEGER, required=False),
        ]
    )
    
    # --- Scenario 2: Software Vendor Evaluation ---
    vendor_org = Organization(
        name="TechGlobal Inc", domains=["techglobal.com"], slug="techglobal", contact_email="procurement@techglobal.com"
    )
    vendor_schema = KnowledgeSchema(
        organization_id=vendor_org.id,
        name="Software Vendor Profile",
        description="Evaluation profiles for third-party software vendors",
        fields=[
            SchemaField(name="vendor_name", label="Vendor Name", field_type=FieldType.STRING, required=True),
            SchemaField(name="cost", label="Annual Cost", field_type=FieldType.INTEGER, required=True),
            SchemaField(name="strengths", label="Key Strengths", field_type=FieldType.LIST, required=False),
            SchemaField(name="weaknesses", label="Weaknesses", field_type=FieldType.LIST, required=False),
        ]
    )

    scenarios = {
        "hiring": DemoScenario(
            id="hiring",
            name="Hiring: AI Engineer",
            organization=hiring_org,
            workspace_name="Hiring AI Engineer",
            workspace_description="Workspace for evaluating AI engineering candidates.",
            schema=hiring_schema,
            rules=[]
        ),
        "vendor": DemoScenario(
            id="vendor",
            name="Procurement: Software Vendor Evaluation",
            organization=vendor_org,
            workspace_name="CRM Vendor Selection",
            workspace_description="Workspace for selecting the best CRM software vendor.",
            schema=vendor_schema,
            rules=[]
        )
    }
    return scenarios
