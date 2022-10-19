import structlog

from toolbelt.client.github import GithubClient
from toolbelt.types import Network, RepoInfos
from toolbelt.utils.parse import latest_tag

REPOS = (
    "9c-launcher",
    "NineChronicles",
    "NineChronicles.Headless",
    "NineChronicles.DataProvider",
)

logger = structlog.get_logger(__name__)


def get_latest_commits(
    github_client: GithubClient, network: Network, branch: str, rc: int
):
    repo_infos: RepoInfos = []
    for repo in REPOS:
        github_client.repo = repo

        if network == "internal":
            r = github_client.get_ref(f"heads/{branch}")

            commit = r["object"]["sha"]
            tag = None
        elif network == "main":
            tags = []
            for v in github_client.get_tags(per_page=100):
                tags.extend(v)
            tag, commit = latest_tag(
                tags, rc, prefix=create_tag_prefix(network)
            )
        repo_infos.append((repo, tag, commit))

        logger.info(f"Found latest commit", repo=repo, tag=tag, commit=commit)

    return repo_infos


def create_tag_prefix(network: Network) -> str:
    prefix = ""

    if network != "main":
        prefix += f"{network}-"

    return prefix
