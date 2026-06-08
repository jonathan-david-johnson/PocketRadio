# M10: Tile Card Redesign — Faded Backdrop + Episode Metadata

**Status**: NOT STARTED

## Goal

Tiles currently show opaque artwork + title + one dim meta line. Replace with a full-bleed faded
backdrop (identical technique to the top panel) and surface three episode-specific rows: day-of-week,
podcast name, and a duration/progress string. Station tiles get a parallel treatment.

See `../ui.md` → "Tile Card Design (M10 target)" for ASCII mockups and exact measurements.

## Done when

### Episode tile
- [ ] Artwork is full-bleed faded background: Poster 270×200, opacity=0.35, `scaleToZoom`
- [ ] Dark scrim overlay: Rectangle 270×200, `#000000AA` on top of artwork
- [ ] Row 1 (y=144): day-of-week — "Monday", "Tuesday", etc. from `published` Unix timestamp
- [ ] Row 2 (y=166): podcast name — dim `#9C9FA4`
- [ ] Row 3 (y=188): `"47:30"` always; `" (20:00 left)"` appended in ACCENT `#00A0E8` only if `playedUpTo > 0`
- [ ] Progress strip (y=138, h=3): dim track full-width, ACCENT fill = `(playedUpTo/duration)×270`. Hidden if `duration = 0`
- [ ] NOW badge (top-right, 52×22 ACCENT rect + "NOW" label) preserved
- [ ] Focus border (274×204 ACCENT rect at -2,-2) preserved

### Station tile
- [ ] Same faded backdrop + scrim approach
- [ ] Row 1: station name — white
- [ ] Row 2: codec/bitrate — dim
- [ ] Row 3: "● LIVE" — ACCENT
- [ ] No progress strip

### Relay / data
- [ ] `published` (Unix seconds) added to description JSON in `onUpNextLoaded` and `onNewReleasesLoaded`
- [ ] TileItem uses `roDateTime` to convert `published` to day-of-week string

## TileItem.xml layout

```xml
<!-- base -->
<Rectangle id="bg"    width="270" height="200" color="0x1A1B1DFF" />
<!-- faded backdrop -->
<Poster id="art"      width="270" height="200" loadDisplayMode="scaleToZoom" opacity="0.35" />
<Rectangle id="scrim" width="270" height="200" color="0x000000AA" />
<!-- focus border (behind bg — shows as outer ring) -->
<Rectangle id="focusBorder" width="274" height="204" translation="[-2,-2]"
           color="0x00A0E8FF" visible="false" />
<!-- progress strip -->
<Rectangle id="progBg"   translation="[0,138]"  width="270" height="3" color="0x3A3D42FF" visible="false" />
<Rectangle id="progFill" translation="[0,138]"  width="0"   height="3" color="0x00A0E8FF" visible="false" />
<!-- text rows -->
<Label id="dayLabel"      translation="[10,144]" width="250" height="22"
       font="font:SmallSystemFont"      color="0xFFFFFFFF" />
<Label id="podcastLabel"  translation="[10,166]" width="250" height="22"
       font="font:SmallSystemFont"      color="0x9C9FA4FF" />
<Label id="durationLabel" translation="[10,188]" width="250" height="20"
       font="font:SmallestSystemFont"   color="0x9C9FA4FF" />
<!-- NOW badge -->
<Rectangle id="nowBg"    width="52" height="22" translation="[214,4]"
           color="0x00A0E8FF" visible="false" />
<Label id="nowLabel"     translation="[214,4]" width="52" height="22"
       font="font:SmallestSystemFont" color="0x000000FF"
       horizAlign="center" vertAlign="center" text="NOW" visible="false" />
```

Note: `focusBorder` must be first child so it renders behind `bg`.

## TileItem.brs logic

```brightscript
Sub onContentSet()
    item = m.top.itemContent
    if item = invalid then return
    m.art.uri = item.HDPosterUrl

    meta = ParseJSON(item.description)
    if meta = invalid then return

    if meta.isStation = true
        m.progBg.visible   = false
        m.progFill.visible = false
        m.dayLabel.text    = item.title
        m.dayLabel.color   = "0xFFFFFFFF"
        codecStr = ""
        if meta.codec <> invalid and meta.codec <> ""
            codecStr = meta.codec
            if meta.bitrate <> invalid and meta.bitrate > 0
                codecStr = codecStr + " / " + meta.bitrate.ToStr() + "k"
            end if
        end if
        m.podcastLabel.text  = codecStr
        m.durationLabel.text = Chr(0x25CF) + " LIVE"   ' ● LIVE
        m.durationLabel.color = "0x00A0E8FF"
    else
        dur    = CInt(meta.duration)
        played = CInt(meta.playedUpTo)

        ' progress strip
        if dur > 0
            m.progBg.visible   = true
            m.progFill.visible = true
            m.progFill.width   = int((played / dur) * 270)
        else
            m.progBg.visible   = false
            m.progFill.visible = false
        end if

        ' day of week
        m.dayLabel.color = "0xFFFFFFFF"
        published = meta.published   ' ISO 8601 string from relay
        if published <> invalid and published <> ""
            dt = CreateObject("roDateTime")
            dt.FromISO8601String(published)
            days = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
            m.dayLabel.text = days[dt.GetDayOfWeek()]
        else
            m.dayLabel.text = ""
        end if

        ' podcast name
        m.podcastLabel.text = meta.podcastName

        ' duration + left
        durStr = FmtHMS(dur)
        if played > 0
            leftStr = FmtHMS(dur - played)
            m.durationLabel.text  = durStr + "  (" + leftStr + " left)"
            m.durationLabel.color = "0x00A0E8FF"
        else
            m.durationLabel.text  = durStr
            m.durationLabel.color = "0x9C9FA4FF"
        end if
    end if
End Sub

' Format seconds → M:SS or H:MM:SS
Function FmtHMS(secs as integer) as string
    if secs <= 0 then return "0:00"
    h    = secs \ 3600
    m    = (secs mod 3600) \ 60
    s    = secs mod 60
    ss   = Right("0" + s.ToStr(), 2)
    if h > 0
        mm = Right("0" + m.ToStr(), 2)
        return h.ToStr() + ":" + mm + ":" + ss
    end if
    return m.ToStr() + ":" + ss
End Function
```

Note: relay already emits ISO strings for both upNext and newReleases — upNext was Unix int
and was fixed in `pc-relay/index.ts` to emit `.toISOString()`. `roDateTime.FromISO8601String`
is reliable with ISO 8601 strings across all Roku firmware.

## Relay change (already done)

`pc-relay/index.ts` upNext path now emits `published` as ISO 8601 string (was Unix int).
newReleases already emitted ISO strings. Both are consistent.

## MainScene.brs change

In both `onUpNextLoaded` and `onNewReleasesLoaded`, add `published` to the description JSON:

```brightscript
child.description = FormatJSON({
    ...
    published: ep.published,   ' ISO 8601 string, e.g. "2025-03-06T15:30:00.000Z"
    ...
})
```

## Implementation Strategy

1. Update `TileItem.xml` — replace Poster+labels with backdrop+scrim+new layout.
2. Update `TileItem.brs` — `onContentSet` handles episode and station branches, `FmtHMS` helper.
3. Add `published` to description JSON in `MainScene.brs` (two loaders).
4. Test: Up Next (in-progress episodes), New Releases (unplayed), Radio Favs (stations).
5. Verify NOW badge and focus border still render correctly.

## User Checkpoint

Up Next tab: tiles show faded artwork background, day-of-week, podcast name, "47:30  (20:00 left)" in blue for in-progress episodes; no "(left)" for unplayed. Radio Favs: faded logo background, station name, codec, "● LIVE" in blue. Playing tile: NOW badge top-right. Focused tile: ACCENT border around tile.

## Commit

TBD.
