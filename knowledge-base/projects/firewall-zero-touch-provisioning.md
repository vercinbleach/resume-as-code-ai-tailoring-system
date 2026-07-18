---
id: project-firewall-zero-touch-provisioning
name: Firewall Zero-Touch Provisioning PoC
aliases:
  - Firewall Zero-Touch Provisioning MVP
type: client-project
organization: Innovery
duration: 1 month
team_size: 4
status: draft
sources:
  - archive/previous-cvs/CV Vincenzo Actualizado - Copy.pdf
  - user-confirmed: 2026-07-17
evidence_checked: 2026-07-17
vendor_source_conflict: historical CV lists Cisco, Fortinet, and Aruba; current user confirmation lists Cisco and Arista
deployment_status: successful proof of concept; later adoption unknown
---

# Firewall Zero-Touch Provisioning PoC

## Problem

Provisioning multiple firewalls required repeated manual network setup. The
infrastructure and network teams wanted to test whether code-driven provisioning
could assign IP addresses and apply baseline configurations consistently.

## What the application does

The successful PoC configured 20 firewalls through Python automation and Ansible
playbooks. The current user-confirmed scope was Cisco and Arista, with one
automated configuration path applying IP assignments and the baseline settings
specified by the infrastructure and network specialists.

## Solution

- Reproduced and adapted a zero-touch provisioning approach discovered in a
  public technical blog.
- Implemented the automation scripts in Python and coordinated their execution
  through Ansible playbooks.
- Automated IP assignment and baseline device configuration from requirements
  supplied by the systems and network specialists.
- Versioned the automation in an internal GitLab repository.
- Connected repository changes to a GitLab CI workflow so updates were checked
  or executed through the shared delivery pipeline. The exact CI jobs are no
  longer recalled.
- Completed the successful PoC during a one-month project.

## Collaboration model

The four-person cross-functional team consisted of Vincenzo, two infrastructure
or systems colleagues, and one network specialist. The infrastructure and
network specialists defined the required device settings, while Vincenzo wrote
the Python and Ansible automation that applied them.

## My contribution

- Developed all Python scripts and Ansible automation used by the PoC.
- Translated the IP and baseline-configuration requirements supplied by the
  systems and network colleagues into repeatable code.
- Integrated the automation with the internal GitLab repository and CI workflow.
- Collaborated with two infrastructure or systems colleagues and one network
  specialist to validate the configuration of 20 firewalls.

## Outcome

- Successfully configured 20 firewalls through the automated PoC.
- Demonstrated that the blog-derived approach could be reproduced within the
  company's Python, Ansible, and GitLab environment.
- Established version-controlled network configuration with CI-backed changes.
- Production adoption and continuation are unknown because the network
  specialist later left the company and Vincenzo was no longer involved.

## Technologies

- Ansible
- Python
- YAML
- Network automation
- Cisco
- Arista
- GitLab
- GitLab CI/CD
- Git

## Structured claims

<!-- structured-claims:start -->
```json
{
  "schema_version": 1,
  "claims": [
    {
      "id": "claim-firewall-twenty-device-poc",
      "statement": "The one-month proof of concept successfully configured 20 firewalls through code-driven provisioning.",
      "dimensions": ["impact", "infrastructure", "technical"],
      "technologies": ["Network automation"],
      "evidence": [
        {
          "source_type": "user-confirmed",
          "locator": "user-confirmed: 2026-07-17",
          "checked": "2026-07-17"
        }
      ],
      "confidence": "high",
      "status": "confirmed",
      "resume_safe": true,
      "sensitivity": "internal-anonymized",
      "aliases": ["20 firewalls", "zero-touch provisioning PoC"],
      "caveats": ["Production adoption after the PoC is unknown."]
    },
    {
      "id": "claim-firewall-python-ansible-ownership",
      "statement": "Vincenzo developed all Python scripts and Ansible automation used to assign IP addresses and apply baseline configuration in the PoC.",
      "dimensions": ["infrastructure", "technical"],
      "technologies": ["Python", "Ansible", "YAML"],
      "evidence": [
        {
          "source_type": "user-confirmed",
          "locator": "user-confirmed: 2026-07-17",
          "checked": "2026-07-17"
        }
      ],
      "confidence": "high",
      "status": "confirmed",
      "resume_safe": true,
      "sensitivity": "internal-anonymized",
      "aliases": ["provisioning scripts", "Ansible playbooks"],
      "caveats": ["The exact Ansible modules and collections have not been recovered."]
    },
    {
      "id": "claim-firewall-gitlab-ci",
      "statement": "The provisioning automation was versioned in an internal GitLab repository and connected to a GitLab CI workflow.",
      "dimensions": ["infrastructure", "reliability", "technical"],
      "technologies": ["Git", "GitLab", "GitLab CI/CD"],
      "evidence": [
        {
          "source_type": "user-confirmed",
          "locator": "user-confirmed: 2026-07-17",
          "checked": "2026-07-17"
        }
      ],
      "confidence": "medium",
      "status": "partial",
      "resume_safe": true,
      "sensitivity": "internal-anonymized",
      "aliases": ["CI-backed configuration", "internal GitLab pipeline"],
      "caveats": ["The exact CI stages and whether changes were validated, deployed, or both are not recalled."]
    },
    {
      "id": "claim-firewall-cross-functional-team",
      "statement": "Vincenzo collaborated with two infrastructure or systems colleagues and one network specialist in a four-person team.",
      "dimensions": ["collaboration", "leadership"],
      "technologies": [],
      "evidence": [
        {
          "source_type": "user-confirmed",
          "locator": "user-confirmed: 2026-07-17",
          "checked": "2026-07-17"
        }
      ],
      "confidence": "high",
      "status": "confirmed",
      "resume_safe": true,
      "sensitivity": "internal-anonymized",
      "aliases": ["four-person cross-functional team"],
      "caveats": []
    },
    {
      "id": "claim-firewall-vendor-list",
      "statement": "The exact firewall vendor list is unresolved between historical CV wording and current recollection.",
      "dimensions": ["infrastructure", "technical"],
      "technologies": ["Arista", "Cisco", "Fortinet", "Aruba"],
      "evidence": [
        {
          "source_type": "historical-cv",
          "locator": "archive/previous-cvs/CV Vincenzo Actualizado - Copy.pdf",
          "checked": "2026-07-17"
        },
        {
          "source_type": "user-confirmed",
          "locator": "user-confirmed: 2026-07-17",
          "checked": "2026-07-17"
        }
      ],
      "confidence": "low",
      "status": "conflicting",
      "resume_safe": false,
      "sensitivity": "internal-anonymized",
      "aliases": ["Cisco and Arista", "Cisco, Fortinet, and Aruba"],
      "caveats": ["The historical CV lists Cisco, Fortinet, and Aruba; current recollection lists Cisco and Arista."]
    }
  ],
  "evidence_gaps": [
    {
      "id": "gap-firewall-vendors",
      "question": "Which exact firewall vendors and models were configured during the successful PoC?",
      "importance": "high",
      "status": "open",
      "affects_claims": ["claim-firewall-vendor-list"]
    },
    {
      "id": "gap-firewall-ci-stages",
      "question": "Which GitLab CI stages validated or applied provisioning changes?",
      "importance": "medium",
      "status": "open",
      "affects_claims": ["claim-firewall-gitlab-ci"]
    },
    {
      "id": "gap-firewall-production-adoption",
      "question": "Was the successful PoC adopted or continued after the network specialist left?",
      "importance": "medium",
      "status": "open",
      "affects_claims": ["claim-firewall-twenty-device-poc"]
    }
  ]
}
```
<!-- structured-claims:end -->

## Reusable resume bullets

- Delivered a successful one-month zero-touch provisioning PoC for 20 Cisco and
  Arista firewalls by developing Python and Ansible automation for IP assignment
  and baseline configuration.
- Enabled version-controlled firewall provisioning by integrating Python and
  Ansible configuration changes with an internal GitLab CI workflow.
- Collaborated with two infrastructure specialists and one network engineer to
  translate device requirements into repeatable provisioning scripts for 20
  firewalls.

## Evidence gaps

- Resolve the vendor conflict between the historical CV, which lists Cisco,
  Fortinet, and Aruba, and the current recollection of Cisco and Arista.
- Confirm the exact firewall models and Ansible modules or collections used.
- Recover the GitLab CI stages and determine whether the pipeline validated,
  deployed, or performed both actions on each change.
- Add provisioning time before and after automation and any error-rate measure.
- Confirm whether the PoC was adopted or continued after the network specialist
  left the company.
