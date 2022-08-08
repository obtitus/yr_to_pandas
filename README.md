# YR to Pandas

Library to aid writing applications that downloads data from yr.no api (https://api.met.no/weatherapi/)
into the python library Pandas

Tries to aid in conforming to https://api.met.no/doc/TermsOfService with:

1. Results are cached to file and not re-submitted until `Expires` header allows. :heavy_check_mark:
2. After the first call, subsequent calls have the `If-Modified-Since` header. :heavy_check_mark:
3. Don't generate unnecessary traffic: left to the caller.
4. Don't schedule many requests at the same time: left to the caller.
5. latitude/lontitude truncated to 4 decimals. :heavy_check_mark:
6. Avoid continous poll: left to the caller.

Python API Documentation: https://obtitus.github.io/yr_to_pandas
