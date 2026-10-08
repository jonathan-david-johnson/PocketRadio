Feature: Radio display policy for breaks, CarPlay and live markers
  A break does not replace the current song. CarPlay does not show lyrics as an album.

  Background:
    Given the system now-playing display is empty
    And a station "KCRW Eclectic 24" that streams from the local test server
    And the station's tracklist lists only "Song A" by "Artist A" from album "Album A" with red artwork
    And the station's tracklist takes 2 seconds to arrive

  @ios @carplay
  Scenario: An ad frame leaves the current title artist and artwork unchanged
    When the listener starts the station
    And the stream announces "Song A" by "Artist A" from album "Album A"
    Then the display shows the title "Song A", the artist "Artist A" and the album "Album A"
    And the display shows red artwork
    When the stream sends an ad frame
    Then the display keeps the current title artist and artwork for 8 seconds

  @ios @carplay @ios-only
  Scenario: CarPlay suppresses lyric album writes and disconnect restores the real album
    When the listener starts the station
    And the stream announces "Song A" by "Artist A" from album "Album A"
    Then the display shows the title "Song A", the artist "Artist A" and the album "Album A"
    When CarPlay connects
    And a lyric line "A lyric that is not an album" reaches the album publishing boundary
    Then the display keeps the album "Album A" for 1 second
    When CarPlay disconnects
    Then the display shows the album "Album A"

  @ios @carplay
  Scenario: Live music markers survive initial metadata artwork and rebuild writes
    When the listener starts the station
    Then the display is marked as a live music stream
    When the stream announces "Song A" by "Artist A" from album "Album A"
    Then the display shows the title "Song A", the artist "Artist A" and the album "Album A"
    And the display is marked as a live music stream
    And the display shows red artwork
    And the display is marked as a live music stream
    When the listener pauses and resumes
    Then the display is marked as a live music stream
