import datetime
from typing import Optional, Iterable, TypeVar, List

from bisect import bisect_right

from marshmallow import Schema, fields, post_load


class Timing:
    def __init__(self, start: float):
        self.start = start

    def __lt__(self, o: object) -> bool:
        try:
            other = getattr(o, 'start')
        except AttributeError:
            return False
        return self.start.__lt__(other)

    def __le__(self, o: object) -> bool:
        try:
            other = getattr(o, 'start')
        except AttributeError:
            return False
        return self.start.__le__(other)

    def __gt__(self, o: object) -> bool:
        try:
            other = getattr(o, 'start')
        except AttributeError:
            return False
        return self.start.__gt__(other)

    def __ge__(self, o: object) -> bool:
        try:
            other = getattr(o, 'start')
        except AttributeError:
            return False
        return self.start.__ge__(other)


T = TypeVar('T')


class TimingList(Iterable[T], list):
    def at(self, offset) -> T:
        index = bisect_right(self, Timing(offset))
        if index == 0:
            return None
        else:
            return self[index - 1]


class Section(Timing):
    def __init__(self, start: float, duration: float, loudness: Optional[float] = None,
                 tempo: Optional[float] = None):
        super().__init__(start)
        self.duration = duration
        self.loudness = loudness
        self.tempo = tempo


class Segment(Timing):
    def __init__(self, start: float, duration: float, loudness_start: Optional[float] = None,
                 loudness_max: Optional[float] = None, loudness_max_time: Optional[float] = None,
                 loudness_end: Optional[float] = None, pitches: List[float] = None, timbre: List[float] = None):
        super().__init__(start)
        self.duration = duration
        self.loudness_start = loudness_start
        self.loudness_max = loudness_max
        self.loudness_max_time = loudness_max_time
        self.loudness_end = loudness_end
        self.pitches = pitches
        self.timbre = timbre


class Analysis:
    def __init__(self,
                 danceability: Optional[float] = None,
                 energy: Optional[float] = None,
                 loudness: Optional[float] = None,
                 speechiness: Optional[float] = None,
                 acousticness: Optional[float] = None,
                 instrumentalness: Optional[float] = None,
                 liveness: Optional[float] = None,
                 valence: Optional[float] = None,
                 sections: Optional[TimingList[Section]] = None,
                 segments: Optional[TimingList[Segment]] = None):
        self.danceability = danceability
        self.energy = energy
        self.loudness = loudness
        self.speechiness = speechiness
        self.acousticness = acousticness
        self.instrumentalness = instrumentalness
        self.liveness = liveness
        self.valence = valence
        self.sections = sections if sections is not None else TimingList()
        self.segments = segments if segments is not None else TimingList()


class Media:
    def __init__(self, artist: Optional[str] = None, title: Optional[str] = None,
                 uri: Optional[str] = None, type: Optional[str] = None,
                 start_datetime: Optional[datetime.datetime] = None,
                 analysis: Analysis = None):
        self.artist = artist
        self.title = title
        self.uri = uri
        self.type = type
        self.start_datetime = start_datetime
        self.analysis = analysis or Analysis()

    @property
    def position(self):
        return (datetime.datetime.now(
            datetime.timezone.utc) - self.start_datetime).total_seconds() if self.start_datetime else None


class SectionSchema(Schema):
    start = fields.Float(required=True)
    duration = fields.Float(required=True)
    loudness = fields.Float()
    tempo = fields.Float()

    @post_load
    def construct(self, data):
        return Section(**data)


class SegmentSchema(Schema):
    start = fields.Float(required=True)
    duration = fields.Float(required=True)
    loudness_start = fields.Float()
    loudness_max = fields.Float()
    loudness_max_time = fields.Float()
    loudness_end = fields.Float()
    pitches = fields.List(fields.Float)
    timbre = fields.List(fields.Float)

    @post_load
    def construct(self, data):
        return Segment(**data)


class AnalysisSchema(Schema):
    danceability = fields.Float()
    energy = fields.Float()
    loudness = fields.Float()
    speechiness = fields.Float()
    acousticness = fields.Float()
    instrumentalness = fields.Float()
    liveness = fields.Float()
    valence = fields.Float()
    sections = fields.Nested(SectionSchema, many=True)
    segments = fields.Nested(SegmentSchema, many=True)

    @post_load
    def construct(self, data):
        if data.get('sections') is not None:
            data['sections'] = TimingList(sorted(data['sections']))
        if data.get('segments') is not None:
            data['segments'] = TimingList(sorted(data['segments']))
        return Analysis(**data)


class StartDateTimeSchema(Schema):
    elapsed = fields.Float(required=True)
    at = fields.LocalDateTime(required=True)

    @post_load
    def construct(self, data):
        return data['at'] - datetime.timedelta(seconds=data['elapsed'])


class MediaSchema(Schema):
    artist = fields.Str()
    title = fields.Str()
    uri = fields.Str()
    type = fields.Str()
    start_datetime = fields.Nested(StartDateTimeSchema)
    analysis = fields.Nested(AnalysisSchema)

    @post_load
    def construct(self, data):
        if data.get('analysis') is None:
            data['analysis'] = Analysis()
        return Media(**data)
