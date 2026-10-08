Feature: Artwork on the system now-playing display for live radio
  The current song never borrows another song's album or artwork.

  Background:
    Given the system now-playing display is empty
    And a station "KCRW Eclectic 24" that streams from the local test server

  @ios @carplay
  Scenario: A second song without station detail does not keep the previous artwork
    Given the station's tracklist lists only "Song A" by "Artist A" from album "Album A" with red artwork
    And the station's tracklist takes 2 seconds to arrive
    When the listener starts the station
    And the stream announces "Song A" by "Artist A" from album "Album A"
    Then the display shows the title "Song A" with red artwork
    When the stream announces "Song B" by "Artist B"
    Then the display shows the title "Song B"
    And the display shows the station logo

  @ios @carplay
  Scenario: A second song with station detail open shows its matching artwork
    Given the station's tracklist lists only "Song A" by "Artist A" with red artwork
    And the station's tracklist takes 2 seconds to arrive
    When the listener starts the station
    And the stream announces "Song A" by "Artist A" from album "Album A"
    Then the display shows the title "Song A" with red artwork
    When the listener opens station detail
    And the station's tracklist lists only "Song B" by "Artist B" from album "Album B" with green artwork
    And the stream announces "Song B" by "Artist B" from album "Album B"
    Then the station's tracklist has refreshed for "Song B"
    And the display shows the title "Song B", the artist "Artist B" and the album "Album B"
    And the display shows green artwork

  @ios @carplay
  Scenario: A tracklist one song behind lends neither its album nor its artwork
    Given the station's tracklist lists only "Song A" by "Artist A" from album "Album A" with red artwork
    And the station's tracklist takes 2 seconds to arrive
    When the listener starts the station
    And the stream announces "Song A" by "Artist A" from album "Album A"
    Then the display shows the title "Song A", the artist "Artist A" and the album "Album A"
    And the display shows red artwork
    When the stream announces "Song B" by "Artist B" without an album
    Then the display shows the title "Song B"
    And the display does not show the album "Album A"
    And the display shows the station logo

  @ios @carplay
  Scenario: A matching track without artwork uses the iTunes fallback
    Given the station's tracklist lists only "Song A" by "Artist A" from album "Album A" without artwork
    And iTunes finds blue artwork for "Song A" by "Artist A"
    And the station's tracklist takes 2 seconds to arrive
    When the listener starts the station
    And the stream announces "Song A" by "Artist A" from album "Album A"
    Then the display shows the title "Song A", the artist "Artist A" and the album "Album A"
    And the display shows blue artwork
    And the iTunes lookup for "Song A" by "Artist A" was served

  @ios @carplay
  Scenario: A song without artwork anywhere shows the logo instead of previous artwork
    Given the station's tracklist lists only "Song A" by "Artist A" with red artwork
    And the station's tracklist takes 2 seconds to arrive
    When the listener starts the station
    And the stream announces "Song A" by "Artist A" from album "Album A"
    Then the display shows the title "Song A" with red artwork
    When the station's tracklist lists only "Song B" by "Artist B" without artwork
    And the station's refreshed tracklist has arrived
    And the stream announces "Song B" by "Artist B"
    Then the display shows the title "Song B"
    And the iTunes lookup for "Song B" by "Artist B" was served
    And the display shows the station logo
