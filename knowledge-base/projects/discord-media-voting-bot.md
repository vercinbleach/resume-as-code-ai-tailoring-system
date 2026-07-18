---
id: project-discord-media-voting-bot
name: Discord Media Voting Bot
type: personal-project
team_size: 1
status: incomplete
sources:
  - archive/previous-cvs/CV Vincenzo Actualizado ENG.pdf
  - github:vercinbleach/animexbot
  - user-confirmed: 2026-07-17
evidence_checked: 2026-07-17
github_match_status: confirmed-same-project
language_source_conflict: historical CV says Python; repository is TypeScript
---

# Discord Media Voting Bot

## Motivation

Vincenzo was active in World of Warcraft and Discord communities and was
interested in the emerging use of bots to organize groups inside a server. He
started this personal project to help a Discord group decide which seasonal
anime to watch without leaving its shared channel.

## What the application does

The intended workflow was to retrieve every anime in the current season from
MyAnimeList, display titles and images in a Discord channel, and let server
members vote on which series the group would watch.

The project remained incomplete. The public repository contains anime search
and metadata retrieval, but the complete seasonal listing and group-voting
workflow should not be presented as finished.

## Implemented and intended solution

- TypeScript bot built with Discord.js.
- Axios integration with the Jikan API, an unofficial API for MyAnimeList data.
- Anime search and retrieval of public metadata and images.
- Intended seasonal-anime catalog inside a Discord channel.
- Intended voting workflow for selecting which anime the group would watch.
- No AI, LLM, agent, or generative component; the project predates Vincenzo's
  AI work.

## My contribution

- Designed and prototyped the personal Discord bot independently.
- Integrated Discord.js with Jikan/MyAnimeList data through Axios.
- Implemented the available anime search and media-retrieval functionality.
- Explored image-rich Discord interactions and community voting, but did not
  complete the end-to-end seasonal selection flow.

## Outcome

- Produced an incomplete but functional integration prototype for retrieving
  anime information inside Discord.
- Gained early experience with TypeScript, Discord bots, external REST APIs,
  image-rich chat interactions, and community-oriented product ideas.
- The bot did not reach a completed or adopted state and currently has no AI
  component or active development plan.

## Technologies

- TypeScript
- Node.js
- Discord.js
- Axios
- Jikan API
- MyAnimeList public data
- REST API integration

## GitHub reconciliation

The public repository [vercinbleach/animexbot](https://github.com/vercinbleach/animexbot)
is confirmed as the source repository for this project. Jikan provides the
MyAnimeList-backed API described in Vincenzo's recollection.

The repository's TypeScript, Discord.js, Axios, and Jikan implementation is
stronger technical evidence than the historical CV's Python description. The
CV language should be treated as inaccurate unless an earlier Python version is
found.

## Optional resume bullet

- Prototyped a TypeScript Discord bot that retrieved anime metadata and images
  through Discord.js, Axios, and the Jikan/MyAnimeList API as the foundation for
  a seasonal group-voting workflow.

## Resume suitability

Low priority for the current resume because the project was not completed or
adopted. It may still support an early-project or personal-interests portfolio
section when incomplete prototypes are appropriate.

## Evidence gaps

- Inspect the repository history to determine how much of seasonal listing and
  voting was implemented before development stopped.
- Confirm whether any earlier Python version existed.
- Confirm whether the prototype was ever deployed to the Discord server.
- Confirm whether votes were intended to persist and, if so, which storage layer
  was planned.
