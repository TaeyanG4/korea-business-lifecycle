# Redistribution Written-Clarification Gate

Checked: **2026-09-07**

All three official MOIS v1 OpenAPI pages show `이용허락범위 제한 없음` (no restriction on the permitted-use scope), so the source-use metadata gate is `PASS_METADATA_CONFIRMED`. The Public Data Portal policy also states that legitimate permission is required when public data contains third-party rights.

The reviewed source pages do not explicitly establish that these three datasets contain no third-party rights. Public accessibility therefore remains separate from permission to mirror externally.

## Questions requiring a written answer

1. Does the no-restriction label authorize redistribution/mirroring of the row-level source records on a third-party platform such as Kaggle?
2. Do the three datasets contain any third-party rights that require separate permission under the portal policy?
3. If row-level mirroring is prohibited or conditional, may the derived aggregate that excludes direct/linkable row fields and precise coordinates and suppresses cells below k=10 be redistributed externally?
4. If redistribution is permitted, what attribution, notice, KOGL designation, or other conditions apply?

## Contact routes

- Public Data Portal inquiry service;
- operator support email: `opendata_help@nia.or.kr`;
- portal support phone: `1566-0025`;
- provider: Ministry of the Interior and Safety (MOIS); and
- management department: Regional Digital Cooperation Division (`지역디지털협력과`).

The project does not automatically send email or inquiries. A response must be archived as source-specific written evidence before any redistribution gate changes.

## Prepared inquiry

A Korean source-specific inquiry is frozen in `provenance/redistribution_clarification_plan.json` with status `READY_NOT_SENT`. It identifies all three portal dataset IDs (`15154916`, `15154921`, `15155252`) and asks in one request about Kaggle row-level mirroring, third-party rights, external redistribution of the privacy-minimized aggregate, and any required attribution/KOGL/notice conditions. It also explicitly states that the k=10 threshold is a technical minimization rule, not a legal privacy guarantee.

## Current state

- source-use metadata: PASS;
- raw external mirror: `UNRESOLVED_THIRD_PARTY_RIGHTS_CLARIFICATION`;
- privacy-minimized aggregate redistribution: `UNRESOLVED`;
- row-level public release: BLOCKED;
- aggregate publication: BLOCKED;
- outreach performed: false; and
- written response received: false.
