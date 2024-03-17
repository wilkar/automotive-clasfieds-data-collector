from sqlalchemy import (JSON, BigInteger, Boolean, Column, DateTime, Identity,
                        Integer, MetaData, String, Table, UniqueConstraint)

metadata_obj = MetaData()
offers_base = Table(
    "offers_base",
    metadata_obj,
    Column("id", Integer, Identity(start=0, cycle=True), primary_key=True),
    Column("brand", String, nullable=False),
    Column("clasfieds_id", Integer, nullable=False),
    Column("link", String, nullable=False),
    Column("title", String, nullable=False),
    Column("created_time", DateTime, nullable=True),
    Column("description", String, nullable=True),
    Column("image_links", JSON, nullable=True),
    Column("vin", String, nullable=True),
    Column("scraperd_time", DateTime, nullable=True),
    UniqueConstraint("clasfieds_id", name="clasfieds_id"),
)

offers_details = Table(
    "offers_details",
    metadata_obj,
    Column("id", Integer, Identity(start=0, cycle=True), primary_key=True),
    Column("clasfieds_id", Integer, nullable=False),
    Column("model", String, nullable=True),
    Column("price", BigInteger, nullable=True),
    Column("engine_size", Integer, nullable=True),
    Column("manufactured_year", Integer, nullable=True),
    Column("engine_power", Integer, nullable=True),
    Column("petrol", String, nullable=True),
    Column("car_body", String, nullable=True),
    Column("milage", BigInteger, nullable=True),
    Column("color", String, nullable=True),
    Column("condition", String, nullable=True),
    Column("transmission", String, nullable=True),
    Column("drive", String, nullable=True),
    Column("country_origin", String, nullable=True),
    Column("righthanddrive", String, nullable=True),
    UniqueConstraint("clasfieds_id", name="clasfieds_id"),
)

offer_location = Table(
    "offer_location",
    metadata_obj,
    Column("id", Integer, Identity(start=0, cycle=True), primary_key=True),
    Column("clasfieds_id", Integer, nullable=False),
    Column("region", String, nullable=True),
    Column("city", String, nullable=True),
    UniqueConstraint("clasfieds_id", name="clasfieds_id"),
)
labeling_data = Table(
    "labeling_data",
    metadata_obj,
    Column("id", Integer, Identity(start=0, cycle=True), primary_key=True),
    Column("vin", String, nullable=False),
    UniqueConstraint("vin", name="vin"),
)

suspicious_offers = Table(
    "suspicious_offers",
    metadata_obj,
    Column("id", Integer, Identity(start=1, cycle=True), primary_key=True),
    Column("suspicious_clasfieds_id", Integer, nullable=False),
    Column("is_suspicious", Boolean, nullable=True),
)
