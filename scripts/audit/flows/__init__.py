from .f01_slack_knowledge import SlackKnowledgeFlow
from .f02_jira_code_plan import JiraCodePlanFlow
from .f04_github_pr_review import GitHubPRReviewFlow
from .f05_jira_comment import JiraCommentFlow
from .f06_full_chain import FullChainFlow
from .f07_knowledge_health import KnowledgeHealthFlow
from .f08_slack_multi_repo import SlackMultiRepoFlow
from .f09_plan_approval_flow import PlanApprovalFlow

FLOW_REGISTRY: dict[str, type] = {
    "f01": SlackKnowledgeFlow,
    "f02": JiraCodePlanFlow,
    "f04": GitHubPRReviewFlow,
    "f05": JiraCommentFlow,
    "f06": FullChainFlow,
    "f07": KnowledgeHealthFlow,
    "f08": SlackMultiRepoFlow,
    "f09": PlanApprovalFlow,
    "slack": SlackKnowledgeFlow,
    "jira": JiraCodePlanFlow,
    "pr": GitHubPRReviewFlow,
    "comment": JiraCommentFlow,
    "chain": FullChainFlow,
    "knowledge": KnowledgeHealthFlow,
    "multi-repo": SlackMultiRepoFlow,
    "plan-approval": PlanApprovalFlow,
}

__all__ = [
    "FLOW_REGISTRY",
    "SlackKnowledgeFlow",
    "JiraCodePlanFlow",
    "GitHubPRReviewFlow",
    "JiraCommentFlow",
    "FullChainFlow",
    "KnowledgeHealthFlow",
    "SlackMultiRepoFlow",
    "PlanApprovalFlow",
]
