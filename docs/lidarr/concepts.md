---
title: Lidarr Concepts
description: How Lidarr models music, why MusicBrainz metadata matters, and when Lidarr is (and isn't) the right tool for your library
tags:
  - lidarr
  - releases
  - metadata
  - concepts
  - musicbrainz
  - artist
---
# Lidarr Concepts

This page explains the model Lidarr uses to manage music, why that model depends on MusicBrainz, and when Lidarr is — and isn't — the right tool for your library. If you just want to install and start using Lidarr, read the [Quick Start](../lidarr/quick-start-guide.md) first and come back here when you want to understand *why* something behaves the way it does.

## How Lidarr manages music

Lidarr is a music library management system, data aggregator, and automation platform for finding and downloading media. At a high level it follows the same principles as the other Arr applications (Sonarr, Radarr, etc.), but music introduces complications that film and TV don't.

Unlike movies and TV shows, music has no consistent set of standards for tagging, naming, or storage. Distribution has shifted from physical media to electronic over several decades, which has widened the variation rather than narrowed it. Opinions on how to handle music-library management are wide and varied, and Lidarr has to pick one.

The choice Lidarr makes is to lean on third-party metadata to impose order. Every album and artist in Lidarr corresponds to a record in an external data source, and Lidarr uses that record to categorize, tag, and manage files. Everything else in this page follows from that decision.

!!! warning
    If the data doesn't exist in third-party services, Lidarr can't manage it.

## The Release model

Lidarr organizes music around the `Release` standard from MusicBrainz. Every item Lidarr manages must correspond to a `Release` in its metadata source.

Examples of `Releases`:

- Album
- EP
- Single
- Broadcast

If something you want to manage doesn't exist as a `Release` in the metadata source, Lidarr can't handle it — there's no "add it locally only" escape hatch.

Lidarr is audio-only. MusicBrainz marks some recordings as video (music videos, live video streams, etc.), and Lidarr skips them entirely — it won't search for, grab, or import a release where all tracks carry the video flag.

!!! info
    You can only manage `Releases` in Lidarr if they exist in third-party services.

## Release groups and releases

{#release-groups-and-releases}

MusicBrainz distinguishes two levels: the **release group** ("the album") and the **release** ("a specific edition of the album"). The 2005 studio album is a release group; the 2005 US CD, the 2005 UK vinyl, and the 2015 remastered reissue are all releases within that release group.

Lidarr's `Album` corresponds to **MusicBrainz's release group**, not its release. When Lidarr adds an album, it's really adding the release group and tracking one of its releases as the "active" release for your library.

Two consequences follow:

- **You can't add a single release without its release group.** There's no "only this pressing" model in Lidarr; the release group is always added, and Lidarr designates one of its releases as active. You can switch which release is active from the album's Edit dialog — this is how you tell Lidarr to match the 2015 remaster instead of the 2005 original, for example.
- **Adding "just an album" still involves the artist.** When you add an album, Lidarr also needs the artist record in its database. You can add the album without monitoring the rest of the artist's catalogue by setting monitoring to *None* at add-time; the artist row exists in Lidarr's database but Lidarr only monitors the target album.

Individual tracks aren't addable in isolation. A recording that was released as part of an album lives inside that release group; to get Lidarr to fetch it you would need to add the release group and let Lidarr fetch the whole thing. Where a track was released *as a single* in MusicBrainz (its own release group of type `Single`), Lidarr can handle it — that's one of the reasons Metadata Profiles expose `Single` as a release-group-type toggle separately from `Album`.

The [Metadata Troubleshooting](../lidarr/metadata-troubleshooting.md) page covers the related failure modes — for example, when a release group has `Type: Unknown` and your Metadata Profile filters it out, and what that looks like from the user's side.

## The Artist model

An `Artist` in Lidarr is the `Release Artist` — the artist the metadata source attributes a `Release` to. This is a surprisingly slippery thing to pin down: naming, stylization, collaborations, and user preferences all contribute to ambiguity about what counts as "the" artist.

Consider how many ways the same person can appear:

- Bob Dylan
- BOB DYLAN
- The Bob Dylan
- Bob Dylan, The
- Bob Dylan & the Band
- Bob Dylan feat. The Band
- The Band featuring Bob Dylan

Each `Release` belongs to exactly one `Artist`. To add a `Release` in Lidarr you have to find and use the canonical `Artist` as the metadata source defines it — not the one written on the album cover, the one written in MusicBrainz. This is the source of most "why can't I add this artist?" problems; see the [FAQ](../lidarr/faq.md) for specific cases.

!!! info
    You can only manage `Release Artists` in Lidarr if they exist in third-party services.

## Dependence on MusicBrainz

The metadata source Lidarr relies on is [MusicBrainz](https://musicbrainz.org/) — a free, community-driven service that exists and survives on user contributions. Lidarr doesn't have its own metadata; it reads MusicBrainz's.

Two practical consequences follow.

**Missing or incorrect data is a MusicBrainz problem, not a Lidarr problem.** If an album isn't showing up in Lidarr, the first question to ask is whether it exists on MusicBrainz and whether the data there's correct. Lidarr doesn't offer a way to edit metadata locally — it reads MusicBrainz, it doesn't override it. Fixes have to happen upstream at MusicBrainz, and Lidarr picks them up on the next refresh after propagation.

**Propagation takes time.** When someone adds or corrects a record on MusicBrainz, Lidarr doesn't see it immediately. Updates flow from MusicBrainz through a periodic sync into a metadata service that Lidarr queries, and from there into your instance on refresh. You can refresh individual artists and albums inside Lidarr once the upstream propagation has happened, but you can't accelerate the propagation itself. Expect a delay measured in hours to days, not minutes.

If you find that a `Release` or `Release Artist` is missing from MusicBrainz, you can help fix it: see [How To Contribute](https://musicbrainz.org/doc/How_to_Contribute). Creating and editing MusicBrainz records is beyond the scope of this wiki.

## Hardlinks and completed downloads

{#hardlinks-and-completed-downloads}

Two questions that come up often enough to answer here:

- *Why do I have the same file in my download folder and my library folder?*
