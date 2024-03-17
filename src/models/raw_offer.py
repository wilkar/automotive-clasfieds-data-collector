from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, kw_only=True)
class RawOfferLocation:
    id: int
    region: str | None
    city: str | None


@dataclass(frozen=True, kw_only=True)
class RawOfferParameters:
    id: int
    model: str | None
    price: int | None
    engine_size: str | None
    manufactured_year: str | None
    engine_power: str | None
    petrol: str | None
    car_body: str | None
    milage: int | None
    color: str | None
    condition: str | None
    transmission: str | None
    drive: str | None
    country_origin: str | None
    righthanddrive: str | None
    vin: str | None


@dataclass(frozen=True, kw_only=True)
class RawOffer:
    brand: str
    id: int
    link: str
    title: str
    created_time: datetime | None
    description: str
    image_links: list[str] | None
    parameters: list[RawOfferParameters] = field(default_factory=list)
    location: list[RawOfferLocation] = field(default_factory=list)
    vin: str | None
    scraped_time: datetime | None


@dataclass(frozen=True, kw_only=True)
class SuspiciousOffer:
    suspicious_clasfieds_id: int
    is_suspicious: bool
