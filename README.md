# YR to Pandas

Library to aid writing applications that interface with yr.no data api (https://api.met.no/weatherapi/)
and the python library Pandas.

Tries to aid in conforming to https://api.met.no/doc/TermsOfService with:

1. Results are cached to file and not re-submitted until `Expires` header.
2. Data is requested with the `If-Modified-Since` header.
3. Don't generate unnecessary traffic: left to the caller.
4. Don't schedule many requests at the same time: left to the caller.
5. latitude/lontitude truncated to 4 decimals.
6. Avoid continous poll: left to the caller.
