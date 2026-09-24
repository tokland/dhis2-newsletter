from . import cop, dev_portal, github, jira, newsletter, releases, youtube

REGISTRY = {
    "cop": cop.fetch,
    "jira": jira.fetch,
    "newsletter": newsletter.fetch,
    "releases": releases.fetch,
    "dev_portal": dev_portal.fetch,
    "github": github.fetch,
    "youtube": youtube.fetch,
}
