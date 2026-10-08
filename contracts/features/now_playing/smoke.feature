# Harness smoke test (M13.1). Platform-neutral wording: "the system now-playing display" is
# MPNowPlayingInfoCenter on iOS. Tag @ios @carplay marks the platforms that implement the steps.
@ios @carplay @smoke
Feature: The first song of a live radio station appears on the system now-playing display
  The display shows the title, artist, album and artwork of the song the station announces.
  A station's tracklist is fetched once, when playback starts.

  Background:
    Given the system now-playing display is empty
    And a station "KCRW Eclectic 24" that streams from the local test server

  @ios @carplay @smoke
  Scenario: The first song shows its title, artist, album and artwork
    Given the station's tracklist lists only "Song 1" by "Artist 1" with red artwork
    # The tracklist arrives after playback has started. If it arrived first, iOS could lose the
    # artwork to the first Now Playing rebuild (iOS bug 5, symptom B).
    And the station's tracklist takes 2 seconds to arrive
    When the listener starts the station
    And the stream announces "Song 1" by "Artist 1"
    Then the display shows the title "Song 1", the artist "Artist 1" and the album "Album"
    And the display shows red artwork
    And the display is marked as a live music stream
