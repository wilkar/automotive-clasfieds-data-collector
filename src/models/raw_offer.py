from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, kw_only=True)
class RawOfferLocation:
    region: str
    city: str


@dataclass(frozen=True, kw_only=True)
class RawOfferParameters:
    model: str  # enum
    price: str | None  # convert to Int and append currency #bi
    engine_size: str | None  # convert to Int and appent unit
    manufactured_year: str | None
    engine_power: str | None  # convert to inte and append unit
    petrol: str | None  # enum
    car_body: str | None  # enum
    milage: str | None  # convert to int append unit
    color: str | None
    condition: str | None  # enum
    transmission: str | None  # enum
    drive: str | None  # enum
    country_origin: str | None  # enum
    righthanddrive: str | None
    vin: str | None


# TODO define enums for some values
@dataclass(frozen=True, kw_only=True)
class RawOffer:
    brand: str  # enum
    id: int
    link: str
    title: str
    created_time: datetime | None
    description: str
    image_links: list[str] | None  # saved as JSON in db
    parameters: list[RawOfferParameters] = field(default_factory=list)
    location: list[RawOfferLocation] = field(default_factory=list)
    vin: str | None
