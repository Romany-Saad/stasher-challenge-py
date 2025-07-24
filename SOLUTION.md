# Solution steps
1. Convert both `dropoff_time` and `pickup_time` on the `Booking` model to `timestamps` instead of `datetime`s with timezone to escape the timezone conversion hell for a simplified and more performant queries.
2. Add the needed indexes to enhance DB performance on the related queries:
   1. Add a new index to the `location` column on the `Stashpoint` model.
   2. Add a new compound index on the `stashpoint_id`, `dropoff_time`, and `pickup_time` columns on the `Booking` model.
   > **Note:** A separate index on the `open_from` and `open_until` columns is not required. The database query planner will prioritize using the highly selective geospatial index to create a small list of candidate stashpoints. Filtering this small list by opening hours is a very fast operation that does not need its own index.
3. Add the new DB filtering capability:
   The search will be a multi-stage pipeline to ensure performance:
   1. **Geospatial + Availability Filtering (Initial Query):** The first database query should find all stashpoints that are both within the `radius_km` of the search location AND are open during the requested `dropoff_time` to `pickup_time` window. This creates a list of initial candidates. Combining these two filters into a single query is ideal as it reduces the number of candidates for the next, more expensive step.
   2. **Capacity Filtering (Secondary Check):** For each candidate stashpoint from the first step, a second query is performed. This query checks the `Bookings` table to calculate the number of bags already booked during the requested time window. If `stashpoint.capacity - booked_bags >= bag_count`, the stashpoint is included in the final results.
4. Change endpoint signature and add validation:
   1. Are `lat`, `lng`, `bag_count`, and `radius_km` the correct data types `float`?
   2. Are `lat` and `lng` within their valid geographical ranges?
   3. Are `dropoff_time` and `pickup_time` valid `ISO 8601` datetime strings?
   4. Is `pickup_time` actually after `dropoff_time`?
   5. A default configurable value should be set for the optional `radius_km`.
   6. If any validation fails, the endpoint should return a 400 Bad Request with a clear error message.
5. Add pagination to the endpoint.
6. Add caching to cache the endpoint responses unless a new reservation is made.
7. Add API docs.
 
# Notes
* Maybe it worth recording the Check In and Check Out times on the Booking model, as it can be important for customer behavior analysis.