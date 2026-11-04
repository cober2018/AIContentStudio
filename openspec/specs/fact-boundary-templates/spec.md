# fact-boundary-templates Specification

## Purpose
TBD - created by archiving change fact-boundary-topic-templates. Update Purpose after archive.
## Requirements
### Requirement: Built-in topic templates for fact boundaries

The platform SHALL ship seven built-in fact-boundary templates — health, parenting and education, products, technology and AI, quant and investing, life observation and news, policy and public services — each stating which claims need a source, the accepted sources (with domains where they exist), freshness, red lines and what may only be said as personal opinion. Templates are code data, not editable on the page.

#### Scenario: Read a template
- **WHEN** the model asks for the templates of a project that chose 健康科普
- **THEN** it receives that template's full rules

### Requirement: Templates are chosen by the model

When the model submits facts it SHALL name the templates it chose from the topic; a project without a choice records them. The platform SHALL suggest templates from the topic and persona. The 选题与资料 step SHALL let the user change the choice but SHALL NOT require it. Product works need no template.

#### Scenario: First submission
- **WHEN** the model submits facts with templates [health] for a project with no choice
- **THEN** the project records 健康科普

### Requirement: Submitted facts are checked and frozen automatically

Over MCP the model SHALL submit every claim it will state as fact (statement, kind, source URL, quoted passage, source date, template, and who said it for quotes and opinions). The platform SHALL open every source: items whose source is unreachable or whose quote is not in the source SHALL be returned with the reason and not stored; items from outside the template's common domains or possibly out of date SHALL be kept with a label. The kept items SHALL be frozen automatically as the project's new fact-boundary version, replacing the previous one; when nothing is kept the boundary SHALL stay as it was. No user freeze step exists.

#### Scenario: Mixed submission
- **WHEN** the model submits five items of which one source is unreachable and one quote is not found
- **THEN** those two come back with reasons and the other three become fact-boundary version 1

#### Scenario: Nothing passes
- **WHEN** every submitted item is returned
- **THEN** the project's fact boundary is unchanged

### Requirement: Writing follows the boundary and the template

Video 导演稿 and article writing rules SHALL require submitting facts before saving a draft and saving again after the facts change; claims presented as facts come only from the frozen fact boundary. The briefs SHALL carry the chosen templates' red lines and list quotes and opinions with who said them.

#### Scenario: Video brief
- **WHEN** the model reads the video brief of a project with 健康科普
- **THEN** the brief includes the health template's red lines

### Requirement: The user sees the checked facts while reviewing

The 导演稿 review and the article review SHALL show how many facts in the current boundary were checked against their sources and how many carry a label, expandable to each statement, source link, quoted passage and label, with nothing to operate. A draft saved against an older boundary SHALL show that it needs saving again.

#### Scenario: Reviewing work 94
- **WHEN** the user reviews work 94's 导演稿 after facts were frozen
- **THEN** the review shows the number of checked facts and lists them on expanding

### Requirement: Manual fact-boundary entry points are removed

The project 来源与事实边界 page SHALL no longer offer binding a frozen fact pack, creating a fact pack, cloning the boundary or editing and freezing drafts; it SHALL show the current boundary read-only with labels, its history and the template choice. The system library SHALL only view fact packs.

#### Scenario: Evidence page
- **WHEN** the user opens 来源与事实边界 of project 49
- **THEN** no bind, create, clone or freeze control is shown

### Requirement: Fact-boundary results reach the model

The results of `submit_facts` and `get_fact_template` SHALL be plain JSON in every case, including when the project already has a frozen fact boundary; the boundary's freeze time SHALL be given as an ISO 8601 string, or null when absent.

#### Scenario: Submitting facts when a boundary exists
- **WHEN** the model calls `submit_facts` on a project that already has a fact boundary and some items pass
- **THEN** it gets the kept count, the returned items with reasons, and the new current boundary, instead of an argument error

#### Scenario: Reading templates when a boundary exists
- **WHEN** the model calls `get_fact_template` on a project that has a fact boundary
- **THEN** it gets the templates and the current boundary, with `frozen_at` as an ISO string

