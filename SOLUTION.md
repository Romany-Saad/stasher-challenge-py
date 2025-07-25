# Solution steps

1. Convert both `dropoff_time` and `pickup_time` on the `Booking` model to `timestamps` without timezone instead of `datetime`s which includes timezone to escape the timezone conversion hell for a simplified and more performant queries.
2. Add the needed indexes to enhance DB performance on the related queries:
   1. Add a new index to the `location` column on the `Stashpoint` model.
   2. Add a new compound index on the `stashpoint_id`, `dropoff_time`, and `pickup_time` columns on the `Booking` model.
      > **Note:** A separate index on the `open_from` and `open_until` columns is not required. The database query planner will prioritize using the highly selective geospatial index to create a small list of candidate stashpoints. Filtering this small list by opening hours is a very fast operation that does not need its own index.
3. Add the new DB filtering capability:
   The search will be a multi-stage pipeline to ensure performance:
   1. **Geospatial + Availability Filtering (Initial Query):** The first database query should find all stashpoints that are both within the `radius_km` of the search location AND are open during the requested `dropoff_time` to `pickup_time` window. This creates a list of initial candidates. Combining these two filters into a single query is ideal as it reduces the number of candidates for the next, more expensive step.
   2. **Capacity Filtering (Secondary Check):** For each candidate stashpoint from the first step, a second query is performed. This query checks the `Bookings` table to calculate the number of bags already booked during the requested time window. If `stashpoint.capacity - booked_bags >= bag_count`, the stashpoint is included in the final results.
4. Add testing to the the new method.
5. Change endpoint signature and add validation:
   1. Are `lat`, `lng`, `bag_count`, and `radius_km` the correct data types?
      1. `radius_km` param should have a default value from config if was null or 0.
      2. `lat`, `lng`, and `radius_km` should be `float`.
      3. `bag_count` should be `int`.
   2. Are `lat` and `lng` within their valid geographical ranges?
   3. Are `dropoff_time` and `pickup_time` valid `ISO 8601` datetime strings?
   4. Is `pickup_time` actually after `dropoff_time`?
   5. A default configurable value should be set for the optional `radius_km`.
   6. If any validation fails, the endpoint should return a 400 Bad Request with a clear error message.
6. Add API docs.

## Notes

- Renamed the request query params to `dropoff_time` and `pickup_time` instead of `dropoff` and `pickup` for more clarity.
- Both `days` and `is_active` do not exist on the Booking model and has been removed from the API response (seemed like a bug).

## Future Enhancements

Maybe it worth adding the following enhancements for next iteration in case of a real project:

- Add cursor-based pagination to the endpoint to enable infinite scrolling on the frontend for a seamless user experience.
- Better rank-based sorting for the results based on distance and availability.
- Recording the Check In and Check Out times on the Booking model, as it can be important for customer behavior analysis.
- Add a quantized caching layer to the `find_available()` method for better performance, the following is a high level of how this can be achieved.

  ```py
  def _get_quantized_dt(self, dt, interval_minutes=30):
       """
       Rounds a datetime down to the nearest interval (e.g., 30 mins)
       to improve cache hits.
       """
       return dt.replace(
           minute=(dt.minute // interval_minutes) * interval_minutes,
           second=0,
           microsecond=0,
       )

  def _get_booked_bags(self, stashpoint_id, dropoff_dt, pickup_dt):
       """
       Calculates booked bags for a stashpoint in a time window,
       using a versioned cache for instant invalidation.
       """
       # 1. Get current version for the stashpoint from cache.
       version_key = f"sp_version:{stashpoint_id}"
       version = cache.get(version_key) or 1

       # 2. Quantize time to create a consistent cache key.
       q_dropoff = self._get_quantized_dt(dropoff_dt)
       q_pickup = self._get_quantized_dt(pickup_dt)

       # 3. Generate a versioned cache key.
       data_key = f"booked_bags:v{version}:{stashpoint_id}:{q_dropoff.isoformat()}:{q_pickup.isoformat()}"

       cached_bags = cache.get(data_key)
       if cached_bags is not None:
           return cached_bags  # Cache Hit!

       # 4. Cache Miss: Query the database using the original, precise times.
       booked_bags = (
           db.session.query(func.sum(Booking.bag_count))
           .filter(
               Booking.stashpoint_id == stashpoint_id,
               Booking.is_cancelled == False,
               Booking.dropoff_time < pickup_dt,
               Booking.pickup_time > dropoff_dt,
           )
           .scalar() or 0
       )

       # 5. Store the result in the cache with a reasonable TTL.
       cache.set(data_key, booked_bags, timeout=3600 * 24)  # 24h TTL
       return booked_bags

  # =============================
  # This will also require cache invalidation on booking side, it will be as simple as incrementing the stashpoint's version number.
  cache.inc(f"sp_version:{stashpoint_id}")
  ```
