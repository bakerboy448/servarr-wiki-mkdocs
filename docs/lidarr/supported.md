---
title: Lidarr Supported
description: List of supported music indexers, trackers, and download clients compatible with Lidarr
tags:
  - lidarr
  - indexers
  - music
  - supported
  - download-clients
  - compatibility
  - trackers
---
This page is the disambiguation target for all **More Info** links in the Lidarr UI. Each entry corresponds to a specific integration type.

!!! info
    The integrations listed here are built into Lidarr. Additional download clients and indexers — including slskd, Deezer, Tidal, and others — can be added via [plugins](../lidarr/plugins.md).

# Download Clients

{#downloadclient}

- Deluge {#deluge}
  - [Refer to the Settings Page](../lidarr/settings.md#download-clients)
- Download Station {#torrentdownloadstation}
  - [Refer to the Settings Page](../lidarr/settings.md#download-clients)
- Download Station {#usenetdownloadstation}
  - [Refer to the Settings Page](../lidarr/settings.md#download-clients)
- Flood {#flood}
  - [Refer to the Settings Page](../lidarr/settings.md#download-clients)
- Hadouken {#hadouken}
  - [Refer to the Settings Page](../lidarr/settings.md#download-clients)
- NZBGet {#nzbget}
  - [Refer to the Settings Page](../lidarr/settings.md#download-clients)
- NZBVortex {#nzbvortex}
  - [Refer to the Settings Page](../lidarr/settings.md#download-clients)
- Pneumatic {#pneumatic}
  - [Refer to the Settings Page](../lidarr/settings.md#download-clients)
- qBittorrent {#qbittorrent}
  - [Refer to the Settings Page](../lidarr/settings.md#download-clients)
- rTorrent {#rtorrent}
  - [Refer to the Settings Page](../lidarr/settings.md#download-clients)
- SABnzbd {#sabnzbd}
  - [Refer to the Settings Page](../lidarr/settings.md#download-clients)
- Torrent Blackhole {#torrentblackhole}
  - [Refer to the Settings Page](../lidarr/settings.md#download-clients)
- Transmission {#transmission}
  - [Refer to the Settings Page](../lidarr/settings.md#download-clients)
- Usenet Blackhole {#usenetblackhole}
  - [Refer to the Settings Page](../lidarr/settings.md#download-clients)
- uTorrent {#utorrent}
  - [Refer to the Settings Page](../lidarr/settings.md#download-clients)
  - Due to uTorrent being adware and formerly spyware, it isn't recommended. Most users use qBittorrent.
- Vuze {#vuze}
  - [Refer to the Settings Page](../lidarr/settings.md#download-clients)

# Indexers

{#indexer}

## Usenet

- Newznab {#newznab}
  - [Refer to the Settings Page](../lidarr/settings.md#indexer-settings)
  - Newznab is a standardised API used by many Usenet indexing sites. Many presets are available, but all require an API key. Indexer aggregators like [Prowlarr](../prowlarr.md) and [NZBHydra2](https://github.com/theotherp/nzbhydra2) can manage multiple Newznab indexers from a single interface.

## Torrents

- FileList {#filelist}
  - [Refer to the Settings Page](../lidarr/settings.md#indexer-settings)
- Gazelle API {#gazelle}
  - [Refer to the Settings Page](../lidarr/settings.md#indexer-settings)
  - Used by Gazelle-based private trackers such as Redacted (formerly What.CD).
- Headphones VIP {#headphones}
  - [Refer to the Settings Page](../lidarr/settings.md#indexer-settings)
- IP Torrents {#iptorrents}
  - Private Tracker
  !!! info
      IP Torrents' native implementation doesn't support Search.

  - [Refer to the Settings Page](../lidarr/settings.md#indexer-settings)
- Nyaa {#nyaa}
  - [Refer to the Settings Page](../lidarr/settings.md#indexer-settings)
- Redacted {#redacted}
  - [Refer to the Settings Page](../lidarr/settings.md#indexer-settings)
- Torrent RSS Feed {#torrentrssindexer}
  - Generic torrent RSS feed parser.
  !!! info
      The RSS feed must contain a `pubdate`. The release size is recommended as well.

  - [Refer to the Settings Page](../lidarr/settings.md#indexer-settings)
- TorrentLeech {#torrentleech}
  - Private Indexer
  - [Refer to the Settings Page](../lidarr/settings.md#indexer-settings)
- Torznab {#torznab}
  - Torznab is a standardised API for torrent indexers, based on the Newznab specification with torrent-specific extensions. It supports both RSS feeds and backlog searching. Torznab is primarily supported by [Prowlarr](../prowlarr.md) and [Jackett](https://github.com/Jackett/Jackett).
  - [Refer to the Settings Page](../lidarr/settings.md#indexer-settings)

# Notifications

{#notification}

- Boxcar {#boxcar}
- Custom Script {#customscript}
  - Runs a user-supplied script when a specified event occurs. See [Custom Scripts](../lidarr/custom-scripts.md) for the full list of available environment variables and example scripts.
- Discord {#discord}
  - Sends notifications to a Discord channel via webhook. One of the most commonly used notification integrations.
- Email {#email}
  - Sends notification emails. If you use Gmail, enable App Passwords under your Google account security settings rather than using your main password.
  !!! info
      You can use a display name with the address: `Your Name <email@example.com>`

- Emby (Media Browser) {#mediabrowser}
  - Notifies an Emby server to refresh its music library after a track is imported or upgraded.
- Gotify {#gotify}
- Join {#join}
- Kodi {#xbmc}
  - Notifies a Kodi instance to refresh its music library after a track is imported or upgraded. Kodi is a free, open-source media centre application.
- Mailgun {#mailgun}
- Notifiarr {#notifiarr}
  - See [Useful Tools — Notifiarr](../useful-tools.md#notifiarr-fka-discord-notifier)
- Plex Media Server {#plexserver}
  - Notifies a Plex Media Server to refresh its music library after a track is imported or upgraded.
- Prowl {#prowl}
- Pushbullet {#pushbullet}
- Pushover {#pushover}
- SendGrid {#sendgrid}
- Slack {#slack}
- Subsonic {#subsonic}
- Synology Indexer {#synologyindexer}
- Telegram {#telegram}
- Webhook {#webhook}

# Lists

{#importlist}

- Headphones {#headphonesimport}
  - [More Info](https://github.com/rembo10/headphones)
- Last.fm Tag {#lastfmtag}
- Last.fm User {#lastfmuser}
- Lidarr {#lidarrimport}
  - Sync monitored artists from another Lidarr instance.
- Lidarr Lists {#lidarrlists}
- MusicBrainz Series {#musicbrainzseries}
  - [More Info](https://musicbrainz.org/doc/Series)
- Spotify Followed Artists {#spotifyfollowedartists}
- Spotify Playlists {#spotifyplaylist}
- Spotify Saved Albums {#spotifysavedalbums}

# Metadata

{#metadata}

- Kodi (XBMC) / Emby {#xbmcmetadata}
  - Generates `.nfo` sidecar files for artist and album folders, compatible with Kodi and Emby/Jellyfin.
- Roksbox {#roksboxmetadata}
- WDTV {#wdtvmetadata}
