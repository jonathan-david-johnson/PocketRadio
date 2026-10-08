Feature: Late radio artwork cannot cross the current playback identity
  A result for an old song, station or episode is dropped.

  Background:
    Given the system now-playing display is empty
    And a station "KCRW Eclectic 24" that streams from the local test server
    And the station's tracklist lists "Song A" by "Artist A" with red artwork that takes 20 seconds to download
    And the station's tracklist also lists "Song B" by "Artist B" with green artwork
    And the station's tracklist takes 2 seconds to arrive

  @ios @carplay
  Scenario: Slow artwork for an earlier song never replaces the current song's artwork
    When the listener starts the station
    And the stream announces "Song A" by "Artist A"
    Then the artwork request for "Song A" has started
    When the stream announces "Song B" by "Artist B"
    Then the display shows the title "Song B" with green artwork
    And the display never shows red artwork until the request for "Song A" completes

  @ios @carplay
  Scenario: Switching stations prevents the old station's artwork from publishing
    When the listener starts the station
    And the stream announces "Song A" by "Artist A"
    Then the artwork request for "Song A" has started
    When the listener switches to another local station
    Then the display identifies the other station
    And the display never shows red artwork until the request for "Song A" completes

  @ios @carplay
  Scenario: Switching to a podcast prevents radio artwork from publishing over it
    When the listener starts the station
    And the stream announces "Song A" by "Artist A"
    Then the artwork request for "Song A" has started
    When the listener switches to a local podcast episode
    Then the display identifies the podcast episode
    And the display never shows red artwork until the request for "Song A" completes
