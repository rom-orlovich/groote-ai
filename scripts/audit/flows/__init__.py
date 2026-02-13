from .f01_slack_knowledge import SlackKnowledgeFlow
from .f02_jira_code_plan import JiraCodePlanFlow
from .f03_github_issue import GitHubIssueFlow
from .f04_github_pr_review import GitHubPRReviewFlow
from .f05_jira_comment import JiraCommentFlow
from .f06_full_chain import FullChainFlow
from .f07_knowledge_health import KnowledgeHealthFlow

FLOW_REGISTRY: dict[str, type] = {
    "f01": SlackKnowledgeFlow,
    "f02": JiraCodePlanFlow,
    "f03": GitHubIssueFlow,
    "f04": GitHubPRReviewFlow,
    "f05": JiraCommentFlow,
    "f06": FullChainFlow,
    "f07": KnowledgeHealthFlow,
    "slack": SlackKnowledgeFlow,
    "jira": JiraCodePlanFlow,
    "github": GitHubIssueFlow,
    "pr": GitHubPRReviewFlow,
    "comment": JiraCommentFlow,
    "chain": FullChainFlow,
    "knowledge": KnowledgeHealthFlow,
}

__all__ = [
    "FLOW_REGISTRY",
    "SlackKnowledgeFlow",
    "JiraCodePlanFlow",
    "GitHubIssueFlow",
    "GitHubPRReviewFlow",
    "JiraCommentFlow",
    "FullChainFlow",
    "KnowledgeHealthFlow",
]
