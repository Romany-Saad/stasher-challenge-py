import unittest
from datetime import datetime, time

from app import create_app, db
from app.models import Booking, Customer, Stashpoint
from services.stashpoint_search_service import StashpointSearchService
from config import TestConfig


class StashpointSearchServiceTestCase(unittest.TestCase):
    """Test suite for the StashpointSearchService."""

    def setUp(self):
        """Set up a test application and a clean database for each test."""
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.service = StashpointSearchService()

        # Common test data
        self.search_lat = 51.5107
        self.search_lng = -0.1246  # Near "Central Cafe Storage"
        self.dropoff_dt = datetime(2024, 1, 1, 10, 0)
        self.pickup_dt = datetime(2024, 1, 1, 18, 0)

        # Create a reusable test customer to avoid unique constraint errors
        self.customer = Customer(name="Test Customer", email="test@test.com")
        db.session.add(self.customer)
        db.session.commit()

    def tearDown(self):
        """Clean up the database session and drop all tables."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _create_stashpoint(self, **kwargs):
        """Helper to create and commit a stashpoint."""
        defaults = {
            "name": "Test Stashpoint",
            "address": "123 Test Street",
            "postal_code": "TEST1",
            "latitude": self.search_lat,
            "longitude": self.search_lng,
            "capacity": 10,
            "open_from": time(8, 0),
            "open_until": time(22, 0),
        }
        defaults.update(kwargs)
        sp = Stashpoint(**defaults)
        db.session.add(sp)
        db.session.commit()
        return sp

    def _create_booking(self, stashpoint_id, bag_count, dropoff, pickup, is_cancelled=False):
        """Helper to create and commit a booking."""
        booking = Booking(
            stashpoint_id=stashpoint_id,
            customer_id=self.customer.id,
            bag_count=bag_count,
            dropoff_time=dropoff,
            pickup_time=pickup,
            is_cancelled=is_cancelled,
        )
        db.session.add(booking)
        db.session.commit()
        return booking

    # --- Test Cases ---

    def test_1_1_find_available_and_verify_order(self):
        """Test 1.1: Find available stashpoints and verify they are ordered by distance."""
        # Stashpoint B is further away than A
        sp_a = self._create_stashpoint(name="Closer", latitude=51.5108, longitude=-0.1247)
        sp_b = self._create_stashpoint(name="Further", latitude=51.5200, longitude=-0.1300)

        results = self.service.find_available(
            self.search_lat, self.search_lng, self.dropoff_dt, self.pickup_dt, 1, 5
        )

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["name"], "Closer")
        self.assertEqual(results[1]["name"], "Further")
        self.assertLess(results[0]["distance_km"], results[1]["distance_km"])

    def test_1_2_verify_response_data_structure(self):
        """Test 1.2: Verify the structure and fields of the returned data."""
        self._create_stashpoint(name="Test SP", capacity=20)

        results = self.service.find_available(
            self.search_lat, self.search_lng, self.dropoff_dt, self.pickup_dt, 1, 5
        )

        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertIn("id", result)
        self.assertIn("name", result)
        self.assertIn("distance_km", result)
        self.assertIn("available_capacity", result)
        self.assertEqual(result["name"], "Test SP")
        self.assertEqual(result["available_capacity"], 20)
        # Check that distance is rounded to 2 decimal places
        self.assertIsInstance(result["distance_km"], float)
        self.assertTrue(result["distance_km"] * 100 % 1 < 1e-9) # A way to check for 2 decimal places

    def test_2_1_and_2_2_geospatial_filtering(self):
        """Test 2.1 & 2.2: Stashpoint inside the radius is found, one outside is not."""
        # Approx 1.1 km away
        self._create_stashpoint(name="Inside", latitude=51.5207, longitude=-0.1246)
        # Approx 11.1 km away
        self._create_stashpoint(name="Outside", latitude=51.6107, longitude=-0.1246)

        results = self.service.find_available(
            self.search_lat, self.search_lng, self.dropoff_dt, self.pickup_dt, 1, radius_km=5
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Inside")

    def test_2_3_very_small_radius_search(self):
        """Test 2.3: A very small radius should only find the exact stashpoint."""
        sp_exact = self._create_stashpoint(name="Exact Spot", latitude=51.5, longitude=-0.1)
        self._create_stashpoint(name="Nearby Spot", latitude=51.501, longitude=-0.101)

        results = self.service.find_available(
            lat=51.5, lng=-0.1, dropoff_dt=self.dropoff_dt, pickup_dt=self.pickup_dt, bag_count=1, radius_km=0.1
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], sp_exact.id)

    def test_3_opening_hours_filtering(self):
        """Test 3: Stashpoints are filtered based on opening hours."""
        sp = self._create_stashpoint(name="9-to-5", open_from=time(9, 0), open_until=time(17, 0))

        # Case 1: Drop-off too early
        results_early = self.service.find_available(
            self.search_lat, self.search_lng, datetime(2024, 1, 1, 8, 59), self.pickup_dt, 1, 5
        )
        self.assertEqual(len(results_early), 0)

        # Case 2: Pick-up too late
        results_late = self.service.find_available(
            self.search_lat, self.search_lng, self.dropoff_dt, datetime(2024, 1, 1, 17, 1), 1, 5
        )
        self.assertEqual(len(results_late), 0)

        # Case 3: Exactly on the boundary
        results_boundary = self.service.find_available(
            self.search_lat, self.search_lng, datetime(2024, 1, 1, 9, 0), datetime(2024, 1, 1, 17, 0), 1, 5
        )
        self.assertEqual(len(results_boundary), 1)
        self.assertEqual(results_boundary[0]["id"], sp.id)

        # Case 4: Well within hours
        results_within = self.service.find_available(
            self.search_lat, self.search_lng, datetime(2024, 1, 1, 10, 0), datetime(2024, 1, 1, 16, 0), 1, 5
        )
        self.assertEqual(len(results_within), 1)
        self.assertEqual(results_within[0]["id"], sp.id)

    def test_4_2_capacity_with_overlapping_booking(self):
        """Test 4.2: Available capacity is reduced by overlapping bookings."""
        sp = self._create_stashpoint(name="Busy SP", capacity=20)
        self._create_booking(
            sp.id, 5, datetime(2024, 1, 1, 12, 0), datetime(2024, 1, 1, 14, 0)
        )

        # Search window fully contains the booking
        results = self.service.find_available(
            self.search_lat, self.search_lng, self.dropoff_dt, self.pickup_dt, 1, 5
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["available_capacity"], 15) # 20 - 5

    def test_4_5_capacity_with_multiple_overlapping_bookings(self):
        """Test 4.5: Available capacity is reduced by sum of multiple overlapping bookings."""
        sp = self._create_stashpoint(name="Very Busy SP", capacity=20)
        # Booking 1: 5 bags
        self._create_booking(
            sp.id, 5, datetime(2024, 1, 1, 10, 0), datetime(2024, 1, 1, 14, 0)
        )
        # Booking 2: 3 bags
        self._create_booking(
            sp.id, 3, datetime(2024, 1, 1, 12, 0), datetime(2024, 1, 1, 16, 0)
        )

        # Search during the time both bookings are active
        results = self.service.find_available(
            self.search_lat, self.search_lng, datetime(2024, 1, 1, 13, 0), datetime(2024, 1, 1, 13, 30), 1, 5
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["available_capacity"], 12) # 20 - 5 - 3

    def test_4_7_insufficient_capacity(self):
        """Test 4.7: Stashpoint is not returned if it has insufficient capacity."""
        sp = self._create_stashpoint(name="Almost Full SP", capacity=10)
        self._create_booking(
            sp.id, 8, self.dropoff_dt, self.pickup_dt
        )

        # Request 3 bags when only 2 are available
        results = self.service.find_available(
            self.search_lat, self.search_lng, self.dropoff_dt, self.pickup_dt, 3, 5
        )

        self.assertEqual(len(results), 0)

    def test_4_8_cancelled_booking_is_ignored(self):
        """Test 4.8: Cancelled bookings do not affect available capacity."""
        sp = self._create_stashpoint(name="SP with Cancellation", capacity=10)
        self._create_booking(
            sp.id, 9, self.dropoff_dt, self.pickup_dt, is_cancelled=True
        )

        results = self.service.find_available(
            self.search_lat, self.search_lng, self.dropoff_dt, self.pickup_dt, 2, 5
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["available_capacity"], 10)

    def test_4_9_non_overlapping_booking(self):
        """Test 4.9: Bookings that do not overlap do not affect capacity."""
        sp = self._create_stashpoint(name="Free SP", capacity=10)
        # Booking is before the search window
        self._create_booking(
            sp.id, 5, datetime(2024, 1, 1, 8, 0), datetime(2024, 1, 1, 9, 59)
        )

        results = self.service.find_available(
            self.search_lat, self.search_lng, self.dropoff_dt, self.pickup_dt, 1, 5
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["available_capacity"], 10)

    def test_4_9_touching_booking(self):
        """Test 4.9: A booking ending exactly when the search begins should not overlap."""
        sp = self._create_stashpoint(name="Touching SP", capacity=10)
        # Booking ends exactly at 10:00
        self._create_booking(
            sp.id, 5, datetime(2024, 1, 1, 8, 0), datetime(2024, 1, 1, 10, 0)
        )

        # Search starts at 10:00
        results = self.service.find_available(
            self.search_lat, self.search_lng, self.dropoff_dt, self.pickup_dt, 1, 5
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["available_capacity"], 10)

    def test_5_1_no_results_found(self):
        """Test 5.1: An empty list is returned when no stashpoints are in the area."""
        # Search in the middle of the ocean
        results = self.service.find_available(
            0, 0, self.dropoff_dt, self.pickup_dt, 1, 5
        )
        self.assertEqual(results, [])

    def test_5_2_request_for_zero_bags(self):
        """Test 5.2: Searching for 0 bags should return open stashpoints regardless of capacity."""
        sp = self._create_stashpoint(name="Full SP", capacity=5)
        self._create_booking(sp.id, 5, self.dropoff_dt, self.pickup_dt)

        # Search for 1 bag should fail
        results_one_bag = self.service.find_available(
            self.search_lat, self.search_lng, self.dropoff_dt, self.pickup_dt, 1, 5
        )
        self.assertEqual(len(results_one_bag), 0)

        # Search for 0 bags should succeed
        results_zero_bags = self.service.find_available(
            self.search_lat, self.search_lng, self.dropoff_dt, self.pickup_dt, 0, 5
        )
        self.assertEqual(len(results_zero_bags), 1)
        self.assertEqual(results_zero_bags[0]["id"], sp.id)
        self.assertEqual(results_zero_bags[0]["available_capacity"], 0)

    def test_5_3_request_for_more_bags_than_total_capacity(self):
        """Test 5.3: Searching for more bags than any stashpoint's total capacity returns nothing."""
        self._create_stashpoint(name="Small SP", capacity=10)

        results = self.service.find_available(
            self.search_lat, self.search_lng, self.dropoff_dt, self.pickup_dt, 999, 5
        )
        self.assertEqual(len(results), 0)

    def test_5_4_correctly_filter_a_mixed_set(self):
        """Test 5.4: Correctly filters a mixed set of candidates for various reasons."""
        # SP_A: Closest, but closed
        self._create_stashpoint(
            name="SP_A_Closed", latitude=51.511, longitude=-0.125, open_from=time(19, 0)
        )
        # SP_B: Second closest, open, but full
        sp_b = self._create_stashpoint(
            name="SP_B_Full", latitude=51.512, longitude=-0.126, capacity=5
        )
        self._create_booking(sp_b.id, 5, self.dropoff_dt, self.pickup_dt)
        # SP_C: Furthest, but open and has capacity
        self._create_stashpoint(
            name="SP_C_Available", latitude=51.513, longitude=-0.127, capacity=10
        )

        results = self.service.find_available(
            self.search_lat, self.search_lng, self.dropoff_dt, self.pickup_dt, 2, 5
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "SP_C_Available")


if __name__ == "__main__":
    unittest.main()