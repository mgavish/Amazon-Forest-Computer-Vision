from __future__ import annotations

import pandas as pd

from upwork_app.graphql_client import UpworkGraphQLClient
from upwork_app.queries import Q_JOB_BY_ID, Q_JOB_SKILLS


def enrich_job_title_desc(client: UpworkGraphQLClient, bids: pd.DataFrame) -> pd.DataFrame:
    if bids.empty:
        return bids.copy()

    job_ids = [str(j) for j in bids["job_id"].dropna().unique().tolist() if str(j).strip()]
    print(f"Unique job_ids for title/description: {len(job_ids)}")

    rows: list[dict[str, str | None]] = []
    errors: list[dict[str, str]] = []

    for i, job_id in enumerate(job_ids, start=1):
        try:
            output = client.gql(Q_JOB_BY_ID, variables={"id": job_id})
            posting = output.get("marketplaceJobPosting") or {}
            content = posting.get("content") or {}
            rows.append(
                {
                    "job_id": posting.get("id") or job_id,
                    "job_title": content.get("title"),
                    "job_description": content.get("description"),
                }
            )
        except Exception as exc:  # noqa: BLE001
            errors.append({"job_id": job_id, "error": str(exc)})

        if i % 10 == 0 or i == len(job_ids):
            print(f"Fetched {i}/{len(job_ids)}")

    jobs = pd.DataFrame(rows)
    result = bids.merge(jobs, on="job_id", how="left")

    print(f"Missing titles: {result['job_title'].isna().sum()}")
    if errors:
        print(f"Job fetch errors: {len(errors)}")
        print(errors[:3])

    return result


def enrich_job_skills(client: UpworkGraphQLClient, bids_jobs: pd.DataFrame) -> pd.DataFrame:
    if bids_jobs.empty:
        return bids_jobs.copy()

    job_ids = [str(j) for j in bids_jobs["job_id"].dropna().unique().tolist() if str(j).strip()]
    print(f"Unique job_ids for skills: {len(job_ids)}")

    rows: list[dict[str, str | int]] = []
    errors: list[dict[str, str]] = []

    for i, job_id in enumerate(job_ids, start=1):
        try:
            output = client.gql(Q_JOB_SKILLS, variables={"id": job_id})
            classification = ((output.get("marketplaceJobPosting") or {}).get("classification") or {})

            skills = [
                skill.get("preferredLabel")
                for skill in (classification.get("skills") or [])
                if skill.get("preferredLabel")
            ]
            additional_skills = [
                skill.get("preferredLabel")
                for skill in (classification.get("additionalSkills") or [])
                if skill.get("preferredLabel")
            ]

            rows.append(
                {
                    "job_id": job_id,
                    "job_skills": " | ".join(sorted(set(skills))),
                    "job_additional_skills": " | ".join(sorted(set(additional_skills))),
                    "job_skill_count": len(set(skills)),
                    "job_additional_skill_count": len(set(additional_skills)),
                }
            )
        except Exception as exc:  # noqa: BLE001
            errors.append({"job_id": job_id, "error": str(exc)})

        if i % 10 == 0 or i == len(job_ids):
            print(f"Fetched skills {i}/{len(job_ids)}")

    skills_df = pd.DataFrame(rows)
    final_df = bids_jobs.merge(skills_df, on="job_id", how="left")

    print(f"Missing skill rows: {final_df['job_skills'].isna().sum()}")
    if errors:
        print(f"Skill fetch errors: {len(errors)}")
        print(errors[:3])

    return final_df
