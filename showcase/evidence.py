"""Validate structured AI proposals against approved facts; no live model calls."""
import json


def validate_proposal(raw, approved_facts):
    """Use source text verbatim so a valid citation cannot disguise an invented claim.

    This constrained boundary sacrifices prose flexibility for auditable drafting.
    It does not prove that the approved facts themselves are true.
    """
    if len(raw) > 16000:
        raise ValueError('Proposal too large')
    proposal = json.loads(raw)
    if not isinstance(proposal, dict) or set(proposal) != {'headline', 'fact_ids'}:
        raise ValueError('Unexpected proposal schema')
    if proposal['headline'] not in {'Analytical engineering', 'Business automation'}:
        raise ValueError('Choose an approved headline')
    ids = proposal['fact_ids']
    if not isinstance(ids, list) or not 1 <= len(ids) <= 5:
        raise ValueError('One to five evidence references required')
    if any(not isinstance(identifier, str) for identifier in ids) or len(set(ids)) != len(ids):
        raise ValueError('References must be unique strings')
    if any(identifier not in approved_facts for identifier in ids):
        raise ValueError('Unsupported evidence reference')
    return {'headline': proposal['headline'], 'bullets': [approved_facts[i] for i in ids],
            'evidence_ids': ids, 'status': 'draft_for_human_review'}


SYNTHETIC_FACTS = {
    'example-01': 'Built a synthetic SQLite reporting pipeline with currency-separated totals.',
    'example-02': 'Tested interrupted-worker recovery and stale-claim rejection.',
}
