Feature: Resolved radio artwork survives playback lifecycle changes
  A rebuild for the same song keeps its resolved artwork.

  Background:
    Given the system now-playing display is empty
    And a station "KCRW Eclectic 24" that streams from the local test server
    And the station's tracklist lists only "Song A" by "Artist A" with red artwork

  @ios @carplay
  Scenario: Pausing and resuming keeps the current song's artwork
    Given the station's tracklist takes 2 seconds to arrive
    When the listener starts the station
    And the stream announces "Song A" by "Artist A"
    Then the display shows the title "Song A" with red artwork
    When the listener pauses and resumes
    Then the rebuilt display shows the title "Song A" with red artwork
    And the display is marked as a live music stream

  @ios @carplay
  Scenario: A cached tracklist at playback start keeps the artwork
    Given the station's tracklist is already cached before playback
    When the listener starts the station
    And the stream announces "Song A" by "Artist A"
    Then the display shows the title "Song A" with red artwork
    And the display keeps red artwork for 2 seconds

  @ios @carplay
  Scenario: Stopping and replaying the same song resolves its artwork again
    Given the station's tracklist takes 2 seconds to arrive
    When the listener starts the station
    And the stream announces "Song A" by "Artist A"
    Then the display shows the title "Song A" with red artwork
    When the listener stops and replays the same station
    Then the rebuilt display shows the title "Song A" with red artwork
    And the display is marked as a live music stream
