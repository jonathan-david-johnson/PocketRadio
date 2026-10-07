# DRAFT (M13 E6/E7 baseline for iOS bugs 4 and 5). D3 is decided; M13.2 will rewrite this as the scenario suite.
# Steps used here that the iOS harness does not define yet: the pause/resume and slow-download steps.
# Platform-neutral wording: "the system now-playing display" is MPNowPlayingInfoCenter on iOS.
@ios @carplay
Feature: Artwork on the system now-playing display for a live radio station
  The display shows the title, artist, album and artwork of the song that is playing.
  A station has a tracklist that is fetched once, when playback starts.

  Background:
    Given the system now-playing display is empty
    And a station "KCRW Eclectic 24" that streams from the local test server

  @h1
  Scenario: A song missing from the stale tracklist does not keep the previous song's artwork
    Given the station's tracklist lists only "Song A" by "Artist A" with red artwork
    And the station's tracklist takes 2 seconds to arrive
    When the listener starts the station
    And the stream announces "Song A" by "Artist A"
    Then the display shows the title "Song A" with red artwork
    When the stream announces "Song B" by "Artist B"
    Then the display shows the title "Song B"
    And the display does not show red artwork

  @h2
  Scenario: Pausing and resuming keeps the current song's artwork
    Given the station's tracklist lists only "Song A" by "Artist A" with red artwork
    And the station's tracklist takes 2 seconds to arrive
    When the listener starts the station
    And the stream announces "Song A" by "Artist A"
    Then the display shows the title "Song A" with red artwork
    When the listener pauses and resumes
    Then the display shows the title "Song A" with red artwork

  @h3
  Scenario: Slow artwork for an earlier song never replaces the current song's artwork
    Given the station's tracklist lists "Song A" by "Artist A" with red artwork that takes 25 seconds to download
    And the station's tracklist also lists "Song B" by "Artist B" with green artwork
    When the listener starts the station
    And the stream announces "Song A" by "Artist A"
    And the stream announces "Song B" by "Artist B"
    Then the display shows the title "Song B" with green artwork
    And after 14 seconds the display still shows green artwork
