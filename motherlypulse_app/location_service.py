"""
MotherlyPulse Geospatial Health Facility & Immunization Lookup Service
Finds the nearest verified health facilities and immunization centers in Ondo State.
Enforces strict clinical honesty and transparency:
- Appends: 'Approximate town location; ask locally for the exact entrance' when coordinate_precision != 'facility_confirmed'.
- Appends: 'Session days may have changed; contact the clinic before travelling' for immunization sessions.
- Excludes any records marked 'unverified'.
"""

import csv
import os
import re
import math
from typing import Dict, Any, List, Optional, Tuple

FACILITIES_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "MotherlyPulse_Data", "05_Facilities_Ondo", "facilities.csv"
)

IMMUNIZATION_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "MotherlyPulse_Data", "07_Immunization_Ondo", "immunization_centers.csv"
)


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates the great-circle distance between two GPS coordinates in kilometers.
    """
    R = 6371.0  # Earth radius in kilometers
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


class LocationService:
    def __init__(
        self,
        facilities_path: str = FACILITIES_PATH,
        immunization_path: str = IMMUNIZATION_PATH
    ):
        self.facilities_path = facilities_path
        self.immunization_path = immunization_path
        self.facilities = self._load_facilities()
        self.immunization_centers = self._load_immunization_centers()

    def _load_facilities(self) -> List[Dict[str, Any]]:
        facilities = []
        if not os.path.exists(self.facilities_path):
            return facilities
        with open(self.facilities_path, mode="r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                # Exclude records without valid source or marked unverified
                status = row.get("verification_status", "").lower()
                source = row.get("source_id", "").strip()
                if not source or status == "unverified":
                    continue
                try:
                    lat = float(row.get("latitude", 0))
                    lon = float(row.get("longitude", 0))
                    if lat != 0 and lon != 0:
                        row["lat_float"] = lat
                        row["lon_float"] = lon
                        facilities.append(row)
                except (ValueError, TypeError):
                    continue
        return facilities

    def _load_immunization_centers(self) -> List[Dict[str, Any]]:
        centers = []
        if not os.path.exists(self.immunization_path):
            return centers
        with open(self.immunization_path, mode="r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                status = row.get("verification_status", "").lower()
                source = row.get("source_id", "").strip()
                if not source or status == "unverified":
                    continue
                try:
                    lat = float(row.get("latitude", 0))
                    lon = float(row.get("longitude", 0))
                    if lat != 0 and lon != 0:
                        row["lat_float"] = lat
                        row["lon_float"] = lon
                        centers.append(row)
                except (ValueError, TypeError):
                    continue
        return centers

    def parse_coordinates_from_text(self, text: str) -> Optional[Tuple[float, float]]:
        """
        Attempts to parse latitude and longitude coordinates from text string.
        Matches patterns like: "7.257, 5.205", "7.25 5.20", "lat: 7.25, lon: 5.20".
        Validates Ondo State approximate bounding box (Lat: 5.5 to 8.0, Lon: 4.3 to 6.2).
        """
        if not text:
            return None
        match = re.search(r"(-?\d{1,2}\.\d+)[,\s]+(-?\d{1,2}\.\d+)", text.strip())
        if match:
            try:
                lat = float(match.group(1))
                lon = float(match.group(2))
                # Validate reasonable Nigeria/Ondo bounds
                if 4.0 <= lat <= 14.0 and 2.0 <= lon <= 15.0:
                    return lat, lon
            except ValueError:
                pass
        return None

    def find_nearest_facility(
        self,
        latitude: float,
        longitude: float
    ) -> Optional[Dict[str, Any]]:
        """
        Finds the nearest verified health facility to the given coordinates.
        """
        if not self.facilities:
            return None

        best_fac = None
        min_dist = float("inf")

        for fac in self.facilities:
            dist = haversine_distance_km(latitude, longitude, fac["lat_float"], fac["lon_float"])
            if dist < min_dist:
                min_dist = dist
                best_fac = dict(fac)

        if best_fac:
            best_fac["distance_km"] = round(min_dist, 2)
            best_fac["lga"] = best_fac.get("local_government_area", "")
            precision = best_fac.get("coordinate_precision", "")
            notes = []
            if precision != "facility_confirmed":
                notes.append("Approximate town location; ask locally for the exact entrance.")
            best_fac["honesty_notes"] = " ".join(notes)
            best_fac["disclaimer"] = best_fac["honesty_notes"]
        return best_fac

    def find_nearest_immunization_center(
        self,
        latitude: float,
        longitude: float
    ) -> Optional[Dict[str, Any]]:
        """
        Finds the nearest verified immunization centre to the given coordinates.
        """
        if not self.immunization_centers:
            return None

        best_center = None
        min_dist = float("inf")

        for center in self.immunization_centers:
            dist = haversine_distance_km(latitude, longitude, center["lat_float"], center["lon_float"])
            if dist < min_dist:
                min_dist = dist
                best_center = dict(center)

        if best_center:
            best_center["distance_km"] = round(min_dist, 2)
            best_center["lga"] = best_center.get("local_government_area", "")
            precision = best_center.get("coordinate_precision", "")
            notes = ["Session days may have changed; contact the clinic before travelling."]
            if precision != "facility_confirmed":
                notes.append("Approximate town location; ask locally for the exact entrance.")
            best_center["honesty_notes"] = " ".join(notes)
            best_center["disclaimer"] = best_center["honesty_notes"]
        return best_center

    def find_facilities_by_query(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Searches facilities matching an LGA or town query text in Ondo State.
        """
        q = query.lower().strip()
        matches = []
        for fac in self.facilities:
            name = fac.get("facility_name", "").lower()
            lga = fac.get("local_government_area", "").lower()
            town = fac.get("town_or_community", "").lower()
            if q in name or q in lga or q in town:
                item = dict(fac)
                precision = item.get("coordinate_precision", "")
                notes = []
                if precision != "facility_confirmed":
                    notes.append("Approximate town location; ask locally for the exact entrance.")
                item["honesty_notes"] = " ".join(notes)
                item["disclaimer"] = item["honesty_notes"]
                item["lga"] = item.get("local_government_area", "")
                matches.append(item)
                if len(matches) >= limit:
                    break
        return matches

    def format_location_response(
        self,
        latitude: float,
        longitude: float,
        language: str = "English"
    ) -> str:
        """
        Generates a clear conversational response with both nearest hospital and immunization clinic.
        """
        fac = self.find_nearest_facility(latitude, longitude)
        imm = self.find_nearest_immunization_center(latitude, longitude)

        if not fac and not imm:
            if language == "Yoruba":
                return (
                    "Iwadi Ile-iwosan: Ko si ile-iwosan to fidi mule ti a ri fun awon nomba yi ni Ipinle Ondo. "
                    "Ti pajawiri ba wa, pe 112 lesekese tabi ki o lo si Ile-iwosan Gbogbogbo to sunmo e."
                )
            elif language == "Nigerian Pidgin":
                return (
                    "Clinic Finder: We no see verified hospital for these coordinates inside Ondo State. "
                    "If emergency happen, call 112 now-now or carry body go the nearest General Hospital."
                )
            else:
                return (
                    "Location Lookup: No verified health facilities could be matched in Ondo State for these coordinates. "
                    "In an emergency, please dial 112 immediately or proceed to your nearest General Hospital."
                )

        lines = []
        if language == "Yoruba":
            lines.append("Awon ile-iwosan ati ile-iṣẹ ajesara to sunmọ yin ni Ipinle Ondo:\n")
            if fac:
                lines.append(
                    f"🏥 Ile-iwosan: {fac['facility_name']} ({fac['local_government_area']} LGA)\n"
                    f"📍 Ijinna: ~{fac['distance_km']} km | Adirẹsi: {fac.get('street_address', fac.get('town_or_community', ''))}\n"
                    f"⚠️ Akiyesi: {fac['honesty_notes']}\n"
                )
            if imm:
                lines.append(
                    f"💉 Ile-iṣẹ Ajesara: {imm['center_name']} ({imm['local_government_area']} LGA)\n"
                    f"📍 Ijinna: ~{imm['distance_km']} km\n"
                    f"⚠️ Akiyesi: {imm['honesty_notes']}\n"
                )
            lines.append("Ti pajawiri ba wa, pe 112 lẹsẹkẹsẹ.")
        elif language == "Nigerian Pidgin":
            lines.append("Verified clinics and vaccine centres wey near you for Ondo State:\n")
            if fac:
                lines.append(
                    f"🏥 Nearest Hospital: {fac['facility_name']} ({fac['local_government_area']} LGA)\n"
                    f"📍 Distance: ~{fac['distance_km']} km | Address: {fac.get('street_address', fac.get('town_or_community', ''))}\n"
                    f"⚠️ Note: {fac['honesty_notes']}\n"
                )
            if imm:
                lines.append(
                    f"💉 Vaccine Post: {imm['center_name']} ({imm['local_government_area']} LGA)\n"
                    f"📍 Distance: ~{imm['distance_km']} km\n"
                    f"⚠️ Note: {imm['honesty_notes']}\n"
                )
            lines.append("If na emergency, call 112 right now.")
        else:
            lines.append("Nearby Health Facilities and Clinics in Ondo State based on your location:\n")
            if fac:
                lines.append(
                    f"🏥 Nearest Hospital: {fac['facility_name']} ({fac['local_government_area']} LGA)\n"
                    f"📍 Distance: ~{fac['distance_km']} km | Address: {fac.get('street_address', fac.get('town_or_community', ''))}\n"
                    f"⚠️ Note: {fac['honesty_notes']}\n"
                )
            if imm:
                lines.append(
                    f"💉 Nearest Immunization Clinic: {imm['center_name']} ({imm['local_government_area']} LGA)\n"
                    f"📍 Distance: ~{imm['distance_km']} km\n"
                    f"⚠️ Note: {imm['honesty_notes']}\n"
                )
            lines.append("For emergencies, always dial 112 directly.")

        return "\n".join(lines)

    def get_location_instructions(self, language: str = "English") -> str:
        """Returns clear instructions on how to share location."""
        if language == "Yoruba":
            return (
                "📍 Lati wa ile-iwosan tabi ile-iṣẹ ajesara to sunmọ yin ni Ipinle Ondo:\n\n"
                "1. Tẹ aami 'paperclip' tabi 'attach' lori Telegram.\n"
                "2. Yan 'Location' (Ibi ti o wa) ki o si pin pẹlu bot yii.\n"
                "3. Tabi ki o tẹ orukọ ilu rẹ ni Ipinle Ondo (fun apẹẹrẹ: Akure, Ondo, Owo, Ikare, Ore)."
            )
        elif language == "Nigerian Pidgin":
            return (
                "📍 How to find clinic or vaccine post wey near you for Ondo State:\n\n"
                "1. Tap the paperclip or attach icon for your Telegram.\n"
                "2. Choose 'Location' make you send your current location.\n"
                "3. Or type your town or LGA name for Ondo State (like Akure, Ondo, Owo, Ikare, Ore)."
            )
        else:
            return (
                "📍 To find health facilities or immunization centres in Ondo State:\n\n"
                "1. Tap the paperclip / attachment icon in Telegram.\n"
                "2. Select 'Location' and send your current location.\n"
                "3. Or type your town or LGA name in Ondo State (e.g. Akure, Ondo, Owo, Ikare, Ore)."
            )
